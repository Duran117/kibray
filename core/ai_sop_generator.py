"""
AI-Powered SOP Generator for Kibray
Generates professional Standard Operating Procedures using GPT-4

Author: Kibray AI Team
Date: December 3, 2025
"""

import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

# Placeholder for OpenAI client - will be initialized when API key is configured
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. Run: pip install openai")


def generate_sop_with_ai(
    task_description: str,
    category: str = 'general',
    language: str = 'es'
) -> dict:
    """
    Generate a complete SOP using GPT-4 based on task description

    Args:
        task_description: Brief description like "Install drywall in 12x15 living room"
        category: prep, paint, sand, stain, seal, caulk, cleanup, other
        language: 'es' or 'en'

    Returns:
        dict: Structured SOP ready to save to ActivityTemplate model

    Example:
        >>> sop = generate_sop_with_ai(
        ...     "Instalar drywall en sala de 12x15 pies",
        ...     category="PREP",
        ...     language="es"
        ... )
        >>> print(sop['name'])
        'Instalación de Drywall - Sala Estándar'
    """
    if not OPENAI_AVAILABLE:
        raise RuntimeError(
            "OpenAI not configured. Set OPENAI_API_KEY in settings or install: pip install openai"
        )

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # Language-specific prompts
    prompts = {
        'es': f"""
Eres un experto en construcción y pintura con 20 años de experiencia en Estados Unidos.
Genera un Standard Operating Procedure (SOP) profesional y detallado para:

TAREA: {task_description}
CATEGORÍA: {category}

El SOP debe ser práctico, específico y orientado a resultados de calidad.

Formato de respuesta (JSON):
{{
    "name": "Título descriptivo del SOP (conciso)",
    "description": "Descripción breve en 1-2 líneas explicando qué logra este procedimiento",
    "tips": "Tips profesionales separados por \\n (3-5 consejos basados en experiencia)",
    "steps": [
        "Paso 1: Acción específica y medible",
        "Paso 2: Acción específica y medible",
        "Paso 3: ...",
        // 5-12 pasos típicamente
    ],
    "materials_list": [
        "Material 1 con cantidad específica (ej: '2 láminas 4x8 drywall')",
        "Material 2 con cantidad...",
        // Lista completa de materiales necesarios
    ],
    "tools_list": [
        "Herramienta 1 (ej: 'Taladro inalámbrico 18V')",
        "Herramienta 2...",
        // Herramientas específicas necesarias
    ],
    "common_errors": "Errores comunes que novatos cometen, separados por \\n",
    "time_estimate": 120,  // minutos realistas (incluye setup + trabajo + cleanup)
    "safety_warnings": "Advertencias de seguridad críticas (EPP, riesgos, etc.)"
}}

IMPORTANTE:
- Pasos detallados pero concisos (no párrafos largos)
- Cantidades específicas de materiales basadas en el tamaño mencionado
- Tips basados en experiencia real de construcción
- Errores comunes que ahorran tiempo/dinero al evitar
- Tiempo realista considerando setup completo y cleanup
- Safety warnings críticos para proteger al trabajador
""",
        'en': f"""
You are a construction and painting expert with 20 years of experience in the US.
Generate a professional, detailed Standard Operating Procedure (SOP) for:

TASK: {task_description}
CATEGORY: {category}

The SOP should be practical, specific, and quality-focused.

Response format (JSON):
{{
    "name": "Descriptive SOP title (concise)",
    "description": "Brief 1-2 line description of what this procedure achieves",
    "tips": "Professional tips separated by \\n (3-5 experience-based tips)",
    "steps": [
        "Step 1: Specific, measurable action",
        "Step 2: Specific, measurable action",
        "Step 3: ...",
        // Typically 5-12 steps
    ],
    "materials_list": [
        "Material 1 with specific quantity (e.g., '2 sheets 4x8 drywall')",
        "Material 2 with quantity...",
        // Complete list of required materials
    ],
    "tools_list": [
        "Tool 1 (e.g., '18V Cordless Drill')",
        "Tool 2...",
        // Specific tools needed
    ],
    "common_errors": "Common mistakes beginners make, separated by \\n",
    "time_estimate": 120,  // realistic minutes (includes setup + work + cleanup)
    "safety_warnings": "Critical safety warnings (PPE, hazards, etc.)"
}}

IMPORTANT:
- Detailed but concise steps (not long paragraphs)
- Specific material quantities based on mentioned size
- Tips based on real construction experience
- Common errors that save time/money when avoided
- Realistic time including full setup and cleanup
- Critical safety warnings to protect workers
"""
    }

    prompt = prompts.get(language, prompts['es'])

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a construction expert generating professional SOPs in JSON format."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=2000
        )

        sop_data = json.loads(response.choices[0].message.content)

        # Validate required fields
        required_fields = ['name', 'description', 'steps', 'materials_list', 'tools_list']
        missing_fields = [f for f in required_fields if f not in sop_data]

        if missing_fields:
            raise ValueError(f"AI response missing required fields: {missing_fields}")

        # Ensure steps is a list
        if isinstance(sop_data['steps'], str):
            sop_data['steps'] = [s.strip() for s in sop_data['steps'].split('\n') if s.strip()]

        # Add metadata
        sop_data['ai_generated'] = True
        sop_data['ai_model'] = 'gpt-4'
        sop_data['original_prompt'] = task_description

        logger.info(f"Successfully generated SOP: {sop_data['name']}")
        return sop_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        raise ValueError(f"AI returned invalid JSON: {e}") from e
    except Exception as e:
        logger.error(f"Error generating SOP with AI: {e}")
        raise


def improve_existing_sop(sop_id: int, feedback: str, language: str = 'es') -> dict:
    """
    Improve an existing SOP based on field feedback

    Args:
        sop_id: ID of ActivityTemplate to improve
        feedback: Field feedback like "Steps 3-4 are confusing, missing tool X"
        language: 'es' or 'en'

    Returns:
        dict: Improved SOP data

    Example:
        >>> improved = improve_existing_sop(
        ...     sop_id=123,
        ...     feedback="Paso 3 muy confuso, falta espátula 6 pulgadas"
        ... )
    """
    if not OPENAI_AVAILABLE:
        raise RuntimeError("OpenAI not configured")

    from core.models import ActivityTemplate

    try:
        sop = ActivityTemplate.objects.get(id=sop_id)
    except ActivityTemplate.DoesNotExist:
        raise ValueError(f"SOP with ID {sop_id} not found") from None

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    prompts = {
        'es': f"""
Tienes un SOP existente que necesita mejorarse basado en feedback real de trabajadores.

SOP ACTUAL:
Nombre: {sop.name}
Pasos actuales: {json.dumps(sop.steps, ensure_ascii=False)}
Materiales actuales: {json.dumps(sop.materials_list, ensure_ascii=False)}
Herramientas actuales: {json.dumps(sop.tools_list, ensure_ascii=False)}
Tips actuales: {sop.tips}

FEEDBACK DE CAMPO (REAL):
{feedback}

INSTRUCCIONES:
1. Analiza el feedback cuidadosamente
2. Identifica qué está funcionando y mantenlo
3. Mejora lo que está causando confusión o problemas
4. Agrega detalles faltantes mencionados en feedback
5. Mantén la estructura JSON igual

Genera la versión mejorada del SOP en el mismo formato JSON que antes.
""",
        'en': f"""
You have an existing SOP that needs improvement based on real worker feedback.

CURRENT SOP:
Name: {sop.name}
Current steps: {json.dumps(sop.steps)}
Current materials: {json.dumps(sop.materials_list)}
Current tools: {json.dumps(sop.tools_list)}
Current tips: {sop.tips}

FIELD FEEDBACK (REAL):
{feedback}

INSTRUCTIONS:
1. Carefully analyze the feedback
2. Identify what's working and keep it
3. Improve what's causing confusion or problems
4. Add missing details mentioned in feedback
5. Keep the same JSON structure

Generate the improved SOP version in the same JSON format as before.
"""
    }

    prompt = prompts.get(language, prompts['es'])

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7
        )

        improved_sop = json.loads(response.choices[0].message.content)

        # Update SOP with improvements
        sop.steps = improved_sop.get('steps', sop.steps)
        sop.materials_list = improved_sop.get('materials_list', sop.materials_list)
        sop.tools_list = improved_sop.get('tools_list', sop.tools_list)
        sop.tips = improved_sop.get('tips', sop.tips)
        sop.common_errors = improved_sop.get('common_errors', sop.common_errors)
        sop.time_estimate = improved_sop.get('time_estimate', sop.time_estimate)
        sop.save()

        logger.info(f"Successfully improved SOP ID {sop_id} based on feedback")
        return improved_sop

    except Exception as e:
        logger.error(f"Error improving SOP {sop_id}: {e}")
        raise


def batch_generate_sops(task_descriptions: list[str], category: str = 'general') -> list[dict]:
    """
    Generate multiple SOPs in batch (useful for initial library setup)

    Args:
        task_descriptions: List of task descriptions
        category: Category for all SOPs

    Returns:
        list: List of generated SOP dicts

    Example:
        >>> tasks = [
        ...     "Preparar superficie para pintura interior",
        ...     "Aplicar primera capa de pintura latex",
        ...     "Calafatear ventanas y puertas"
        ... ]
        >>> sops = batch_generate_sops(tasks, category="PREP")
        >>> len(sops)
        3
    """
    if not OPENAI_AVAILABLE:
        raise RuntimeError("OpenAI not configured")

    results = []

    for i, task_desc in enumerate(task_descriptions, 1):
        try:
            logger.info(f"Generating SOP {i}/{len(task_descriptions)}: {task_desc[:50]}...")
            sop = generate_sop_with_ai(task_desc, category)
            results.append(sop)
        except Exception as e:
            logger.error(f"Failed to generate SOP for '{task_desc}': {e}")
            results.append({
                'error': str(e),
                'task_description': task_desc
            })

    return results


def get_sop_suggestions(project_type: str, scope: str) -> list[str]:
    """
    Get AI suggestions for which SOPs to create for a project type

    Args:
        project_type: 'residential_interior', 'commercial', 'exterior', etc.
        scope: Brief scope description

    Returns:
        list: Suggested SOP titles to create

    Example:
        >>> suggestions = get_sop_suggestions(
        ...     project_type='residential_interior',
        ...     scope='3 bedroom house, full interior paint + drywall repairs'
        ... )
        >>> suggestions
        ['Reparación de Drywall - Huecos Pequeños',
         'Preparación de Superficie Interior',
         'Pintura de Techos',
         'Pintura de Paredes', ...]
    """
    if not OPENAI_AVAILABLE:
        raise RuntimeError("OpenAI not configured")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    prompt = f"""
Eres un construction project manager experto.
Dado este tipo de proyecto, sugiere SOPs específicos que deberían crearse.

TIPO DE PROYECTO: {project_type}
ALCANCE: {scope}

Genera una lista de 8-12 SOPs específicos que este proyecto necesitaría.
Responde en formato JSON:

{{
    "suggested_sops": [
        "Título SOP 1 específico",
        "Título SOP 2 específico",
        ...
    ]
}}

Sé específico al tipo de proyecto y alcance mencionado.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.8
        )

        data = json.loads(response.choices[0].message.content)
        return data.get('suggested_sops', [])

    except Exception as e:
        logger.error(f"Error getting SOP suggestions: {e}")
        return []


# Default SOPs for common construction tasks
DEFAULT_CONSTRUCTION_SOPS = [
    ("Preparación de Superficie para Pintura Interior", "PREP"),
    ("Reparación de Drywall - Huecos Pequeños (<2 pulgadas)", "PREP"),
    ("Reparación de Drywall - Huecos Grandes (>2 pulgadas)", "PREP"),
    ("Aplicar Primera Capa de Pintura (Interior)", "PAINT"),
    ("Aplicar Segunda Capa de Pintura (Interior)", "PAINT"),
    ("Pintura de Techos", "PAINT"),
    ("Pintura de Molduras y Trim", "PAINT"),
    ("Lijado de Paredes Antes de Pintura", "SAND"),
    ("Lijado de Compound en Drywall", "SAND"),
    ("Aplicar Stain en Madera - Primera Capa", "STAIN"),
    ("Aplicar Stain en Madera - Segunda Capa", "STAIN"),
    ("Calafatear Ventanas y Puertas", "CAULK"),
    ("Calafatear Baseboards", "CAULK"),
    ("Limpieza Final de Proyecto", "CLEANUP"),
    ("Protección de Pisos y Muebles", "COVER"),
]


if __name__ == "__main__":
    # Test script
    print("Testing AI SOP Generator...")

    if not OPENAI_AVAILABLE:
        print("❌ OpenAI not configured")
        print("Set OPENAI_API_KEY in your Django settings")
    else:
        print("✅ OpenAI configured")

        # Test single SOP generation
        try:
            test_sop = generate_sop_with_ai(
                "Instalar drywall en sala de 12x15 pies con techo de 9 pies",
                category="PREP"
            )
            print(f"\n✅ Generated test SOP: {test_sop['name']}")
            print(f"   Steps: {len(test_sop['steps'])}")
            print(f"   Materials: {len(test_sop['materials_list'])}")
            print(f"   Time: {test_sop.get('time_estimate')} min")
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
