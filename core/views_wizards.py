import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import ClientOrganization, Project

logger = logging.getLogger(__name__)

# Check OpenAI availability
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY
except ImportError:
    OPENAI_AVAILABLE = False

@login_required
def project_launchpad_wizard(request):
    """
    Render the Project Launchpad Wizard (Step-by-step project creation).
    """
    # Fetch data for dropdowns
    clients = ClientOrganization.objects.all().order_by('name')

    context = {
        'clients': clients,
        'openai_available': OPENAI_AVAILABLE
    }
    return render(request, "core/wizards/project_launchpad.html", context)

@login_required
@require_POST
def project_launchpad_ai_suggest(request):
    """
    AI Endpoint to suggest project details based on description.
    """
    if not OPENAI_AVAILABLE:
        return JsonResponse({'success': False, 'error': 'AI not configured'})

    try:
        data = json.loads(request.body)
        description = data.get('description', '')
        project_type = data.get('project_type', 'General')

        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = f"""
        Act as a Construction Project Manager assistant.
        Based on this project description: "{description}"
        Type: {project_type}

        Suggest the following in JSON format:
        1. A professional project name.
        2. A refined description.
        3. Estimated duration in days.
        4. A list of 3-5 key phases (milestones).
        5. A list of 3 potential risks.

        JSON Structure:
        {{
            "suggested_name": "...",
            "refined_description": "...",
            "duration_days": 30,
            "phases": ["Phase 1", "Phase 2"],
            "risks": ["Risk 1", "Risk 2"]
        }}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return JsonResponse({'success': True, 'data': result})

    except Exception as e:
        logger.error(f"AI Launchpad Error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def project_launchpad_save(request):
    """
    Save the project from the wizard.
    """
    try:
        data = json.loads(request.body)

        # Basic fields
        name = data.get('name')
        client_id = data.get('client_id')
        address = data.get('address')
        start_date_str = data.get('start_date')
        duration_days = int(data.get('duration_days', 30))
        description = data.get('description')

        if not name or not start_date_str:
            return JsonResponse({'success': False, 'error': 'Missing required fields'})

        start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = start_date + timezone.timedelta(days=duration_days)

        # Create Project
        project = Project.objects.create(
            name=name,
            address=address,
            start_date=start_date,
            end_date=end_date,
            description=description,
            billing_organization_id=client_id if client_id else None
        )

        # TODO: Create Phases/Schedule items if provided in the wizard payload

        return JsonResponse({'success': True, 'project_id': project.id, 'redirect_url': f"/projects/{project.id}/overview/"})

    except Exception as e:
        logger.error(f"Launchpad Save Error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})
