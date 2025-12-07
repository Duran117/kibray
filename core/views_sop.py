from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def sop_express_creator(request):
    """
    Render the SOP Express Creator page (AI-powered).
    """
    return render(request, "core/sop_express.html")
