"""
SOP Express API - AI-powered SOP generation and management
"""

import base64
import json
import logging
import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils.translation import gettext as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import ActivityTemplate

logger = logging.getLogger(__name__)

# Check OpenAI availability
try:
    from openai import OpenAI

    OPENAI_AVAILABLE = hasattr(settings, "OPENAI_API_KEY") and settings.OPENAI_API_KEY
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. Run: pip install openai")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_sop_with_ai(request):
    """
    Generate a complete SOP using AI based on task description

    POST /api/v1/sop/generate/
    {
        "task_description": "Instalación de puertas interiores",
        "category": "INSTALL",
        "language": "es"
    }
    """
    if not OPENAI_AVAILABLE:
        return Response(
            {"success": False, "error": _("AI no disponible. Configure OPENAI_API_KEY.")},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    task_description = request.data.get("task_description", "").strip()
    category = request.data.get("category", "OTHER")
    language = request.data.get("language", "es")

    if not task_description:
        return Response(
            {"success": False, "error": _("La descripción de la tarea es requerida")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

        # Build prompt based on language
        if language == "es":
            prompt = f"""Eres un experto en construcción y acabados profesionales.
Genera un SOP (Procedimiento Operativo Estándar) completo para la siguiente tarea:

TAREA: {task_description}
CATEGORÍA: {category}

Responde SOLO con un JSON válido con esta estructura exacta:
{{
    "name": "Nombre descriptivo del SOP",
    "description": "Descripción breve de 1-2 oraciones",
    "steps": ["Paso 1: descripción clara", "Paso 2: descripción clara", ...],
    "materials_list": ["Material 1", "Material 2", ...],
    "tools_list": ["Herramienta 1", "Herramienta 2", ...],
    "tips": "Consejos importantes separados por punto y coma",
    "common_errors": "Errores comunes a evitar separados por punto y coma",
    "safety_warnings": "Advertencias de seguridad importantes",
    "time_estimate": 2.5,
    "difficulty_level": "beginner|intermediate|advanced"
}}

Los pasos deben ser específicos, accionables y en orden lógico.
Incluye entre 5-10 pasos detallados.
"""
        else:
            prompt = f"""You are an expert in construction and professional finishes.
Generate a complete SOP (Standard Operating Procedure) for the following task:

TASK: {task_description}
CATEGORY: {category}

Respond ONLY with a valid JSON with this exact structure:
{{
    "name": "Descriptive SOP name",
    "description": "Brief 1-2 sentence description",
    "steps": ["Step 1: clear description", "Step 2: clear description", ...],
    "materials_list": ["Material 1", "Material 2", ...],
    "tools_list": ["Tool 1", "Tool 2", ...],
    "tips": "Important tips separated by semicolons",
    "common_errors": "Common errors to avoid separated by semicolons",
    "safety_warnings": "Important safety warnings",
    "time_estimate": 2.5,
    "difficulty_level": "beginner|intermediate|advanced"
}}

Steps should be specific, actionable, and in logical order.
Include between 5-10 detailed steps.
"""

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        sop_data = json.loads(response.choices[0].message.content)

        # Validate required fields
        required_fields = ["name", "steps"]
        for field in required_fields:
            if field not in sop_data:
                raise ValueError(f"AI response missing required field: {field}")

        # Ensure lists are lists
        for field in ["steps", "materials_list", "tools_list"]:
            if field in sop_data and not isinstance(sop_data[field], list):
                sop_data[field] = [sop_data[field]] if sop_data[field] else []

        # Add category
        sop_data["category"] = category

        logger.info(f"AI generated SOP: {sop_data.get('name')} for user {request.user.id}")

        return Response({"success": True, "sop": sop_data, "ai_generated": True})

    except json.JSONDecodeError as e:
        logger.error(f"AI response JSON parse error: {e}")
        return Response(
            {"success": False, "error": _("Error procesando respuesta de AI")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    except Exception as e:
        logger.error(f"AI SOP generation error: {e}")
        return Response(
            {"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_popular_templates(request):
    """
    Get popular SOP templates for quick selection

    GET /api/v1/sop/templates/popular/
    """
    category = request.query_params.get("category", None)
    limit = int(request.query_params.get("limit", 6))

    queryset = ActivityTemplate.objects.filter(is_active=True)

    if category:
        queryset = queryset.filter(category=category)

    # Order by usage (you could add a usage_count field later)
    templates = queryset.order_by("-created_at")[:limit]

    data = []
    for t in templates:
        data.append(
            {
                "id": t.id,
                "name": t.name,
                "category": t.category,
                "category_display": t.get_category_display(),
                "description": t.description[:100] + "..."
                if len(t.description) > 100
                else t.description,
                "steps_count": len(t.steps) if t.steps else 0,
                "difficulty_level": t.difficulty_level,
                "time_estimate": float(t.time_estimate) if t.time_estimate else None,
                "completion_points": t.completion_points,
            }
        )

    return Response({"success": True, "templates": data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_template_detail(request, template_id):
    """
    Get full template details for cloning/editing

    GET /api/v1/sop/templates/<id>/
    """
    try:
        template = ActivityTemplate.objects.get(pk=template_id, is_active=True)

        return Response(
            {
                "success": True,
                "template": {
                    "id": template.id,
                    "name": template.name,
                    "category": template.category,
                    "category_display": template.get_category_display(),
                    "description": template.description,
                    "steps": template.steps or [],
                    "materials_list": template.materials_list or [],
                    "tools_list": template.tools_list or [],
                    "tips": template.tips,
                    "common_errors": template.common_errors,
                    "safety_warnings": template.safety_warnings,
                    "time_estimate": float(template.time_estimate)
                    if template.time_estimate
                    else None,
                    "difficulty_level": template.difficulty_level,
                    "completion_points": template.completion_points,
                    "video_url": template.video_url,
                    "reference_photos": template.reference_photos or [],
                },
            }
        )
    except ActivityTemplate.DoesNotExist:
        return Response(
            {"success": False, "error": _("Template no encontrado")},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_sop(request):
    """
    Save a new SOP (from AI or manual creation)

    POST /api/v1/sop/save/
    """
    data = request.data

    required_fields = ["name", "category"]
    for field in required_fields:
        if not data.get(field):
            return Response(
                {"success": False, "error": f"{field} es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    try:
        # Parse time estimate
        time_hours = float(data.get("time_hours", 0) or 0)
        time_minutes = float(data.get("time_minutes", 0) or 0)
        time_estimate = time_hours + (time_minutes / 60.0)

        # Create SOP
        sop = ActivityTemplate.objects.create(
            name=data["name"],
            category=data["category"],
            description=data.get("description", ""),
            steps=data.get("steps", []),
            materials_list=data.get("materials_list", []),
            tools_list=data.get("tools_list", []),
            tips=data.get("tips", ""),
            common_errors=data.get("common_errors", ""),
            safety_warnings=data.get("safety_warnings", ""),
            video_url=data.get("video_url", ""),
            time_estimate=time_estimate if time_estimate > 0 else None,
            difficulty_level=data.get("difficulty_level", "beginner"),
            completion_points=data.get("completion_points", 10),
            created_by=request.user,
            is_active=data.get("is_active", True),
        )

        logger.info(f"SOP created: {sop.name} (ID: {sop.id}) by user {request.user.id}")

        return Response(
            {"success": True, "sop_id": sop.id, "message": _("¡SOP creado exitosamente!")},
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        logger.error(f"Error saving SOP: {e}")
        return Response(
            {"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_categories(request):
    """
    Get all available SOP categories with counts

    GET /api/v1/sop/categories/
    """
    categories = []
    for code, name in ActivityTemplate.CATEGORY_CHOICES:
        count = ActivityTemplate.objects.filter(category=code, is_active=True).count()
        categories.append(
            {"code": code, "name": name, "count": count, "icon": CATEGORY_ICONS.get(code, "📋")}
        )

    return Response({"success": True, "categories": categories})


# Category icons mapping
CATEGORY_ICONS = {
    "PREP": "🔧",
    "COVER": "🛡️",
    "SAND": "🪨",
    "STAIN": "🎨",
    "SEAL": "💧",
    "PAINT": "🖌️",
    "CAULK": "🔩",
    "CLEANUP": "🧹",
    "OTHER": "📋",
}

# Material/Tool suggestions by category
CATEGORY_SUGGESTIONS = {
    "PREP": {
        "materials": [
            "Drywall sheets",
            "Joint compound",
            "Drywall screws",
            "Mesh tape",
            "Corner bead",
        ],
        "tools": [
            "Power drill",
            "Utility knife",
            "T-square",
            "Level",
            "Drywall saw",
            "Taping knife",
        ],
    },
    "PAINT": {
        "materials": [
            "Paint (color specified)",
            "Primer",
            "Painter's tape",
            "Drop cloths",
            "Sandpaper",
        ],
        "tools": ["Brushes (various sizes)", "Rollers", "Paint tray", "Extension pole", "Ladder"],
    },
    "SAND": {
        "materials": [
            "Sandpaper (80, 120, 220 grit)",
            "Sanding sponges",
            "Tack cloth",
            "Dust masks",
        ],
        "tools": ["Orbital sander", "Sanding block", "Shop vacuum", "Safety goggles"],
    },
    "STAIN": {
        "materials": ["Wood stain", "Pre-stain conditioner", "Clean rags", "Mineral spirits"],
        "tools": ["Stain brushes", "Foam applicators", "Gloves", "Respirator"],
    },
    "SEAL": {
        "materials": ["Polyurethane/Sealer", "Tack cloth", "Fine sandpaper (320 grit)"],
        "tools": ["Natural bristle brush", "Foam brush", "Clean lint-free cloths"],
    },
    "CAULK": {
        "materials": ["Caulk (silicone/acrylic)", "Painter's tape", "Denatured alcohol"],
        "tools": ["Caulk gun", "Caulk finishing tool", "Utility knife", "Clean rags"],
    },
    "CLEANUP": {
        "materials": ["Trash bags", "Cleaning solution", "Paper towels"],
        "tools": ["Broom", "Dustpan", "Shop vacuum", "Mop"],
    },
    "COVER": {
        "materials": ["Plastic sheeting", "Painter's tape", "Drop cloths", "Masking paper"],
        "tools": ["Tape dispenser", "Scissors", "Utility knife"],
    },
    "OTHER": {"materials": [], "tools": []},
}


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_suggestions(request):
    """
    Get material/tool suggestions for a category

    GET /api/v1/sop/suggestions/?category=PAINT
    """
    category = request.query_params.get("category", "OTHER")
    suggestions = CATEGORY_SUGGESTIONS.get(category, CATEGORY_SUGGESTIONS["OTHER"])

    return Response(
        {
            "success": True,
            "materials": suggestions.get("materials", []),
            "tools": suggestions.get("tools", []),
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_sop_express_creator(request):
    """
    Save a new SOP from the Express Creator
    """
    try:
        data = request.data
        title = data.get("title")
        goal = data.get("goal")
        steps = data.get("steps", [])
        image_data = data.get("image_data")

        if not title:
            return Response({"status": "error", "message": "Title is required"}, status=400)

        # Handle Image Upload
        reference_photos = []
        if image_data and ";base64," in image_data:
            try:
                format, imgstr = image_data.split(";base64,")
                ext = format.split("/")[-1]
                filename = f"sop_images/{uuid.uuid4()}.{ext}"
                file_data = ContentFile(base64.b64decode(imgstr), name=filename)
                file_path = default_storage.save(filename, file_data)
                # Assuming default storage url works, otherwise might need MEDIA_URL
                reference_photos.append(default_storage.url(file_path))
            except Exception as img_err:
                logger.error(f"Error saving image: {img_err}")
                # Continue without image if it fails

        sop = ActivityTemplate.objects.create(
            name=title,
            description=goal,
            steps=steps,
            reference_photos=reference_photos,
            # Default values
            category="OTHER",
            difficulty_level="beginner",
            is_active=True,
        )

        return Response({"status": "success", "id": sop.id})

    except Exception as e:
        logger.error(f"Error saving SOP: {str(e)}")
        return Response({"status": "error", "message": str(e)}, status=500)


# Backwards-compatible alias to avoid breaking any older imports.
# NOTE: Keep only one real definition of `save_sop` in this module.
save_sop_express = save_sop_express_creator
