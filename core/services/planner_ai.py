"""
AI Services for Strategic Planner
Provides intelligent assistance for task prioritization and planning
"""
from __future__ import annotations

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

import json

from django.conf import settings

# Configure OpenAI
if OPENAI_AVAILABLE and openai:
    openai.api_key = getattr(settings, "OPENAI_API_KEY", None)


class PlannerAI:
    """AI Assistant for Strategic Planning"""

    @staticmethod
    def process_brain_dump(text: str, user_context: dict | None = None) -> dict:
        """
        Process brain dump text and categorize tasks into high-impact vs noise.

        Args:
            text: Raw brain dump text from user
            user_context: Optional dict with user's life visions, habits, etc.

        Returns:
            {
                'high_impact': [{'text': 'Task 1', 'reason': 'Why it matters'}],
                'noise': [{'text': 'Task 2'}],
                'summary': 'AI analysis summary'
            }
        """
        if not OPENAI_AVAILABLE or not openai or not openai.api_key:
            return {"high_impact": [], "noise": [], "summary": "OpenAI API key not configured"}

        # Build context prompt
        context_info = ""
        if user_context:
            visions = user_context.get("visions", [])
            if visions:
                context_info = "\n\nUser's Life Visions:\n" + "\n".join([f"- {v}" for v in visions])

        prompt = f"""You are an executive productivity coach. Analyze this brain dump and apply the 80/20 rule.

Brain Dump:
{text}
{context_info}

Categorize each item as either:
1. HIGH IMPACT (advances major goals, creates leverage, strategic)
2. NOISE (busy work, low value, reactive tasks)

Return JSON format:
{{
    "high_impact": [
        {{"text": "Clear task description", "reason": "Why this is high-impact"}},
        ...
    ],
    "noise": [
        {{"text": "Task description"}},
        ...
    ],
    "summary": "Brief analysis of what you found"
}}

RULES:
- Limit high_impact to maximum 5 items (80/20 principle)
- Be ruthless: most things are noise
- Focus on what creates RESULTS, not just activity"""

        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in executive productivity and the Pareto Principle.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            # Handle markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]

            result = json.loads(result_text)
            return result

        except Exception as e:
            print(f"AI Brain Dump Error: {e}")
            return {"high_impact": [], "noise": [], "summary": f"Error processing: {str(e)}"}

    @staticmethod
    def suggest_frog(high_impact_items: list[dict], user_context: dict | None = None) -> dict:
        """
        Suggest which high-impact item should be "The Frog" (most important).

        Args:
            high_impact_items: List of high-impact tasks
            user_context: Optional context about user's energy, goals, etc.

        Returns:
            {
                'recommended_index': 0,
                'reasoning': 'Why this should be the frog',
                'alternative': 'Second choice if applicable'
            }
        """
        if not OPENAI_AVAILABLE or not openai or not openai.api_key or not high_impact_items:
            return {
                "recommended_index": 0,
                "reasoning": "No AI available or no items to analyze",
                "alternative": "",
            }

        # Build context
        context_info = ""
        if user_context:
            energy = user_context.get("energy_level")
            if energy:
                context_info += f"\nUser's current energy level: {energy}/10"

        items_list = "\n".join(
            [f"{i + 1}. {item['text']}" for i, item in enumerate(high_impact_items)]
        )

        prompt = f"""You are Brian Tracy, author of "Eat That Frog". Help choose THE ONE most important task.

High-Impact Tasks:
{items_list}
{context_info}

Which ONE task should be "The Frog" (done FIRST today)?

Consider:
- Which creates the most leverage?
- Which removes the biggest bottleneck?
- Which, if completed, makes everything else easier?
- "Eat a live frog first thing in the morning and nothing worse will happen to you the rest of the day"

Return JSON:
{{
    "recommended_index": 0,
    "reasoning": "Why this is the frog (2-3 sentences)",
    "alternative": "Second choice if first isn't possible"
}}"""

        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are Brian Tracy, expert in time management and productivity.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=300,
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]

            result = json.loads(result_text)
            return result

        except Exception as e:
            print(f"AI Frog Suggestion Error: {e}")
            return {"recommended_index": 0, "reasoning": f"Error: {str(e)}", "alternative": ""}

    @staticmethod
    def generate_micro_steps(frog_title: str, context: str | None = None) -> list[dict]:
        """
        Generate actionable micro-steps for completing the frog.

        Args:
            frog_title: The main task to break down
            context: Optional additional context

        Returns:
            [
                {'text': 'Step 1: ...', 'done': false},
                {'text': 'Step 2: ...', 'done': false},
                ...
            ]
        """
        if not OPENAI_AVAILABLE or not openai or not openai.api_key:
            return [
                {"text": "Define the first action", "done": False},
                {"text": "Complete the main work", "done": False},
                {"text": "Review and finalize", "done": False},
            ]

        context_text = f"\nContext: {context}" if context else ""

        prompt = f"""Break this task into 3-5 micro-steps (specific, actionable, 15-30 minutes each).

Task: {frog_title}
{context_text}

Rules:
- Each step must be CONCRETE and ACTIONABLE
- Start with verbs: "Draft", "Call", "Review", "Send"
- No vague steps like "Think about" or "Work on"
- Each step should take 15-30 minutes max
- Total: 3-5 steps only

Return JSON array:
[
    {{"text": "Step 1: Clear action verb + specific task"}},
    {{"text": "Step 2: ..."}},
    ...
]"""

        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a GTD (Getting Things Done) expert specializing in breaking down complex tasks.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=400,
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]

            steps = json.loads(result_text)

            # Ensure proper format
            return [{"text": step.get("text", step), "done": False} for step in steps]

        except Exception as e:
            print(f"AI Micro-Steps Error: {e}")
            return [
                {"text": "Start the task", "done": False},
                {"text": "Complete the main work", "done": False},
                {"text": "Finalize and review", "done": False},
            ]

    @staticmethod
    def suggest_time_blocks(frog_title: str, energy_level: int, micro_steps: list[dict]) -> dict:
        """
        Suggest optimal time blocks based on task complexity and user energy.

        Args:
            frog_title: The task
            energy_level: User's energy (1-10)
            micro_steps: List of micro-steps

        Returns:
            {
                'suggested_start': 'HH:MM',
                'suggested_end': 'HH:MM',
                'reasoning': 'Why this time block'
            }
        """
        if not OPENAI_AVAILABLE or not openai or not openai.api_key:
            # Default smart suggestion
            if energy_level >= 7:
                return {
                    "suggested_start": "09:00",
                    "suggested_end": "11:00",
                    "reasoning": "High energy - tackle during peak morning hours",
                }
            else:
                return {
                    "suggested_start": "10:00",
                    "suggested_end": "12:00",
                    "reasoning": "Start after warm-up period",
                }

        num_steps = len(micro_steps)

        prompt = f"""Suggest optimal time block for this task.

Task: {frog_title}
User Energy: {energy_level}/10
Micro-steps: {num_steps}

Return JSON:
{{
    "suggested_start": "HH:MM (24h format)",
    "suggested_end": "HH:MM",
    "reasoning": "One sentence why"
}}

Consider:
- High energy (8-10) = morning (8am-11am)
- Medium energy (5-7) = mid-morning (9am-12pm)
- Low energy (1-4) = after lunch warm-up (2pm-4pm)
- Complex tasks need 2-3 hours, simple tasks 1-2 hours"""

        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a time management expert."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=150,
            )

            result_text = response.choices[0].message.content.strip()

            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]

            return json.loads(result_text)

        except Exception as e:
            print(f"AI Time Block Error: {e}")
            return {
                "suggested_start": "09:00",
                "suggested_end": "11:00",
                "reasoning": f"Default suggestion (Error: {str(e)})",
            }
