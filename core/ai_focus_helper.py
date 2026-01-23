"""
AI-powered helpers for Executive Focus Workflow (Module 25)
Integrates GPT-4 to analyze tasks, recommend priorities, and generate priming scripts

Author: Kibray AI Team
Date: December 3, 2025
"""

import json
import logging
from typing import Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# Check OpenAI availability
try:
    from openai import OpenAI

    OPENAI_AVAILABLE = hasattr(settings, "OPENAI_API_KEY") and settings.OPENAI_API_KEY
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning(
        "OpenAI package not installed. AI features will use fallback. Run: pip install openai"
    )


def calculate_task_impact_ai(
    task_title: str, task_description: str, user_role: str, session_context: dict
) -> dict:
    """
    Calculate task impact score (1-10) using AI analysis

    Args:
        task_title: Brief task title
        task_description: Detailed description
        user_role: 'admin', 'owner', 'pm', 'superintendent', 'employee'
        session_context: {'energy_level': 8, 'date': '2025-12-03'}

    Returns:
        {
            'score': 8,
            'reason': 'High revenue potential, strategic importance',
            'is_delegable': False,
            'delegation_reason': 'Requires owner expertise'
        }

    Example:
        >>> score = calculate_task_impact_ai(
        ...     "Follow up ABC Corp $120K proposal",
        ...     "Call client to discuss timeline",
        ...     "owner",
        ...     {"energy_level": 8},
        ... )
        >>> print(score["score"])  # 9
    """
    if not OPENAI_AVAILABLE:
        logger.info("OpenAI unavailable, using fallback scoring")
        return _fallback_scoring(task_title, task_description, user_role)

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # Role-specific priorities
    role_priorities = {
        "admin": "Strategic decisions, sales, high-value client relationships, business growth",
        "owner": "Business growth, major contracts ($50K+), key relationships, strategic planning",
        "pm": "Project execution, quality control, team coordination, problem-solving",
        "superintendent": "On-site management, crew coordination, safety, quality inspection",
        "employee": "Task execution, quality work, skill development, efficiency",
    }

    priority_desc = role_priorities.get(user_role, "General productivity and task completion")

    prompt = f"""
You are an executive productivity coach for a construction business.
Analyze this task for a {user_role} and score its impact.

TASK:
Title: {task_title}
Description: {task_description}

USER CONTEXT:
- Role: {user_role}
- Key Priorities: {priority_desc}
- Energy Level Today: {session_context.get("energy_level", 5)}/10

SCORING CRITERIA (1-10):
- 9-10: Critical revenue/strategic impact (major contracts, VIP clients)
- 7-8: High impact (prevents losses, important relationships)
- 5-6: Medium impact (necessary but not urgent)
- 3-4: Low impact (routine tasks, delegable)
- 1-2: Very low impact (busy work, should not do)

Also determine:
- Is this delegable? (Can someone else do it 80% as well?)
- Who should do it if delegable?

Response format (JSON only, no markdown):
{{
    "score": 7,
    "reason": "Brief explanation of score (1-2 sentences max)",
    "is_delegable": false,
    "delegation_reason": "Who should do it and why, or empty string if not delegable"
}}

Be HONEST. Low scores are OK for admin work. High scores only for truly impactful tasks.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a productivity expert for construction executives. Be direct, honest, and concise.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=300,
        )

        result = json.loads(response.choices[0].message.content)

        # Validate and clamp score
        score = result.get("score", 5)
        if not isinstance(score, (int, float)):
            score = 5
        score = max(1, min(10, int(score)))
        result["score"] = score

        logger.info(f"AI scored '{task_title[:40]}...' as {score}/10")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"AI returned invalid JSON: {e}")
        return _fallback_scoring(task_title, task_description, user_role)
    except Exception as e:
        logger.error(f"AI task scoring failed: {e}")
        return _fallback_scoring(task_title, task_description, user_role)


def recommend_one_thing_ai(tasks: list[dict], user_context: dict) -> Optional[Dict]:
    """
    AI analyzes all tasks and recommends THE ONE THING (Frog task)

    Applies "Eat That Frog" principle: tackle most important task first.

    Args:
        tasks: List of task dicts with keys: id, title, description, ai_impact_score
        user_context: {
            'role': 'owner',
            'energy_level': 8,
            'date': '2025-12-03'
        }

    Returns:
        {
            'recommended_task_id': 123,
            'confidence': 0.85,
            'reasoning': 'Highest revenue impact and time-sensitive'
        }
        or None if no tasks

    Example:
        >>> tasks = [
        ...     {"id": 1, "title": "Follow up proposal", "ai_impact_score": 9},
        ...     {"id": 2, "title": "Review invoices", "ai_impact_score": 4},
        ... ]
        >>> rec = recommend_one_thing_ai(tasks, {"role": "owner", "energy_level": 8})
        >>> print(rec["recommended_task_id"])  # 1
    """
    if not tasks:
        return None

    if not OPENAI_AVAILABLE:
        # Fallback: return highest impact score
        highest = max(tasks, key=lambda t: t.get("ai_impact_score", 0))
        return {
            "recommended_task_id": highest["id"],
            "confidence": 0.7,
            "reasoning": "Highest impact score (AI unavailable, using fallback)",
        }

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # Format tasks for AI
    tasks_summary = "\n".join(
        [
            f"{i + 1}. {t['title']} (Impact: {t.get('ai_impact_score', '?')}/10)\n   {t.get('description', 'No description')[:100]}"
            for i, t in enumerate(tasks)
        ]
    )

    prompt = f"""
You are advising a construction {user_context.get("role", "executive")} on their ONE THING today.

Apply "Eat That Frog" principle:
- Choose THE MOST IMPORTANT task
- The one that moves the needle most
- Completing this makes today a success

TODAY'S TASKS:
{tasks_summary}

USER CONTEXT:
- Role: {user_context.get("role", "unknown")}
- Energy Level: {user_context.get("energy_level", 5)}/10
- Date: {user_context.get("date", "today")}

Which ONE task should be their Frog?
Consider: Impact score, urgency, energy required, role-appropriateness.

Response (JSON only):
{{
    "recommended_task_number": 1,
    "confidence": 0.85,
    "reasoning": "1-2 sentences max why THIS is the one to eat first"
}}

Task number must be 1-{len(tasks)}.
Be decisive. Pick ONE.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.6,
            max_tokens=200,
        )

        result = json.loads(response.choices[0].message.content)

        # Convert task number to task ID
        task_num = result.get("recommended_task_number", 1) - 1
        if 0 <= task_num < len(tasks):
            result["recommended_task_id"] = tasks[task_num]["id"]
            logger.info(
                f"AI recommended task #{task_num + 1} as Frog: {tasks[task_num]['title'][:40]}..."
            )
            return result
        else:
            logger.warning(f"AI returned invalid task number: {task_num + 1}")
            # Fallback to highest score
            highest = max(tasks, key=lambda t: t.get("ai_impact_score", 0))
            return {
                "recommended_task_id": highest["id"],
                "confidence": 0.6,
                "reasoning": "Highest impact score (AI recommendation invalid)",
            }

    except Exception as e:
        logger.error(f"AI Frog recommendation failed: {e}")
        # Fallback
        if tasks:
            highest = max(tasks, key=lambda t: t.get("ai_impact_score", 0))
            return {
                "recommended_task_id": highest["id"],
                "confidence": 0.5,
                "reasoning": "Highest impact score (AI error fallback)",
            }
        return None


def generate_priming_script_ai(user_name: str, one_thing: str, energy_level: int) -> str:
    """
    Generate personalized morning priming/motivation script

    Style: Tony Robbins meets construction executive - powerful but brief.

    Args:
        user_name: User's first name
        one_thing: Their Frog task for today
        energy_level: 1-10

    Returns:
        Motivational script (60 seconds to read)

    Example:
        >>> script = generate_priming_script_ai("Jesus", "Close ABC Corp deal", 8)
        >>> print(script)
        Good morning, Jesus!

        Today you're tackling your ONE THING: Close ABC Corp deal.
        This is what moves the needle. Everything else is noise.
        ...
    """
    if not OPENAI_AVAILABLE:
        # Fallback: simple template
        return f"""
Good morning, {user_name}!

Today your ONE THING is: {one_thing}

Remember the 80/20 rule: This ONE task matters more than everything else combined.
If you only accomplish THIS, today is a success.

You have the energy ({energy_level}/10) and focus to make this happen.

Now go crush it! 🚀
"""

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    prompt = f"""
Generate a powerful, concise morning priming script for:

User: {user_name}
Energy Level: {energy_level}/10
ONE THING Today: {one_thing}

Requirements:
- Style: Tony Robbins energy + construction executive practicality
- Length: 2-3 short paragraphs (60 seconds to read out loud)
- Specific to their ONE THING
- Actionable mindset, no fluff
- Remind them: if they ONLY do this, day = success

Structure:
1. Powerful greeting with their name
2. Context on why this ONE THING matters
3. Brief affirmation/mindset shift
4. End with: "Now go crush it! 🚀"

Be concise. No generic platitudes. Make it PERSONAL to their task.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a high-performance coach. Write powerful but brief priming scripts.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=250,
        )

        script = response.choices[0].message.content.strip()
        logger.info(f"Generated AI priming script for {user_name}")
        return script

    except Exception as e:
        logger.error(f"AI priming script generation failed: {e}")
        # Fallback
        return generate_priming_script_ai.__doc__


def analyze_delegation_batch(tasks: list[dict], user_role: str = "owner") -> list[dict]:
    """
    Batch analyze which tasks are delegable

    Identifies tasks that:
    - Someone else can do 80% as well
    - Are below the user's pay grade
    - Are routine/repetitive

    Args:
        tasks: List of task dicts with title, description, ai_impact_score
        user_role: User's role for context

    Returns:
        [
            {
                'task_id': 123,
                'delegable': True,
                'delegate_to': 'Project Manager',
                'reasoning': 'Routine operational task'
            },
            ...
        ]

    Example:
        >>> tasks = [
        ...     {"id": 1, "title": "Review invoices", "ai_impact_score": 3},
        ...     {"id": 2, "title": "Close $200K deal", "ai_impact_score": 10},
        ... ]
        >>> delegable = analyze_delegation_batch(tasks, "owner")
        >>> len(delegable)  # 1 (invoices delegable)
    """
    if not tasks or not OPENAI_AVAILABLE:
        # Fallback: mark low-score tasks as delegable
        delegable = []
        for task in tasks:
            if task.get("ai_impact_score", 5) < 5:
                delegable.append(
                    {
                        "task_id": task["id"],
                        "delegable": True,
                        "delegate_to": "Team member",
                        "reasoning": "Low impact score suggests delegable (AI unavailable)",
                    }
                )
        return delegable

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    tasks_list = "\n".join(
        [
            f"{i + 1}. (ID: {t['id']}) {t['title']} - Score: {t.get('ai_impact_score', '?')}/10\n   {t.get('description', '')[:80]}"
            for i, t in enumerate(tasks)
        ]
    )

    prompt = f"""
Review these tasks for a construction {user_role} and identify which are DELEGABLE.

DELEGATION RULE: Task is delegable if someone else can do it 80% as well.

TASKS:
{tasks_list}

For EACH task that IS delegable, respond:
{{
    "delegable_tasks": [
        {{
            "task_id": 123,
            "delegable": true,
            "delegate_to": "Project Manager / Office Manager / Specific role",
            "reasoning": "Brief reason why delegable (1 sentence)"
        }}
    ]
}}

Be STRICT: Only delegate if it truly doesn't require {user_role} expertise.
High-impact tasks (8-10) are rarely delegable.
Return ONLY delegable tasks (skip non-delegable ones).
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.6,
            max_tokens=500,
        )

        result = json.loads(response.choices[0].message.content)
        delegable_tasks = result.get("delegable_tasks", [])

        logger.info(f"AI identified {len(delegable_tasks)} delegable tasks out of {len(tasks)}")
        return delegable_tasks

    except Exception as e:
        logger.error(f"AI delegation analysis failed: {e}")
        return []


def _fallback_scoring(title: str, description: str, role: str) -> dict:
    """
    Fallback heuristic scoring when AI is unavailable

    Uses keyword matching and role-based logic.
    """
    score = 5  # Default medium

    # High-value keywords (boost score)
    high_value_keywords = [
        "sale",
        "sales",
        "client",
        "contract",
        "proposal",
        "meeting",
        "revenue",
        "deal",
        "close",
        "vip",
        "major",
        "strategic",
    ]

    # Low-value keywords (reduce score)
    low_value_keywords = [
        "email",
        "admin",
        "file",
        "organize",
        "sort",
        "schedule",
        "routine",
        "minor",
        "paperwork",
    ]

    # Combine title and description
    text_lower = f"{title} {description}".lower()

    # Keyword scoring
    if any(kw in text_lower for kw in high_value_keywords):
        score += 3
    if any(kw in text_lower for kw in low_value_keywords):
        score -= 2

    # Role-specific adjustments
    if role in ["admin", "owner"] and ("client" in text_lower or "contract" in text_lower):
        score += 2

    # Clamp to 1-10
    score = max(1, min(10, score))

    # Determine delegability
    is_delegable = score < 6  # Low scores usually delegable

    return {
        "score": score,
        "reason": "Heuristic scoring based on keywords (AI unavailable)",
        "is_delegable": is_delegable,
        "delegation_reason": "Routine task, appears delegable"
        if is_delegable
        else "Requires direct attention",
    }


# CLI Test
if __name__ == "__main__":
    print("🧪 Testing AI Focus Helper...")
    print(f"OpenAI Available: {OPENAI_AVAILABLE}\n")

    if OPENAI_AVAILABLE:
        print("Test 1: Task Impact Scoring")
        print("-" * 50)
        test_score = calculate_task_impact_ai(
            task_title="Follow up on ABC Corp $120K proposal",
            task_description="Call client to discuss timeline and finalize contract terms",
            user_role="owner",
            session_context={"energy_level": 8},
        )
        print(f"Score: {test_score['score']}/10")
        print(f"Reason: {test_score['reason']}")
        print(f"Delegable: {test_score['is_delegable']}")
        if test_score["delegation_reason"]:
            print(f"Delegation: {test_score['delegation_reason']}")
        print()

        print("Test 2: ONE THING Recommendation")
        print("-" * 50)
        test_tasks = [
            {
                "id": 1,
                "title": "Follow up $120K proposal",
                "ai_impact_score": 9,
                "description": "Close deal",
            },
            {
                "id": 2,
                "title": "Review invoices",
                "ai_impact_score": 3,
                "description": "Check payments",
            },
            {
                "id": 3,
                "title": "Site visit",
                "ai_impact_score": 7,
                "description": "Inspect quality",
            },
        ]
        rec = recommend_one_thing_ai(test_tasks, {"role": "owner", "energy_level": 8})
        if rec:
            print(f"Recommended Task ID: {rec['recommended_task_id']}")
            print(f"Confidence: {rec['confidence'] * 100:.0f}%")
            print(f"Reasoning: {rec['reasoning']}")
        print()

        print("✅ Tests complete!")
    else:
        print("⚠️ OpenAI not configured")
        print("Set OPENAI_API_KEY in Django settings to test AI features")
        print("\nTesting fallback scoring...")

        test_score = calculate_task_impact_ai(
            "Follow up proposal", "Call client about contract", "owner", {"energy_level": 8}
        )
        print(f"Fallback Score: {test_score['score']}/10")
        print(f"Reason: {test_score['reason']}")
