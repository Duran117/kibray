"""
AI Enhancement Models for Daily Planning

Provides models for:
- Timeline view preferences
- AI analysis logging
- AI suggestions
- Voice commands
"""

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class TimelineView(models.Model):
    """
    User preferences for timeline visualization
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="timeline_preferences")
    default_view_mode = models.CharField(
        max_length=20,
        choices=[("compact", "Compact"), ("detailed", "Detailed"), ("calendar", "Calendar")],
        default="detailed",
    )
    days_visible = models.IntegerField(default=7, help_text="Number of days to show in timeline")
    auto_scroll_today = models.BooleanField(default=True, help_text="Auto-scroll to today's date")
    show_ai_suggestions = models.BooleanField(default=True, help_text="Show AI suggestions panel")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "timeline_views"
        verbose_name = _("Timeline View Preference")
        verbose_name_plural = _("Timeline View Preferences")

    def __str__(self):
        return f"Timeline preferences for {self.user.username}"


class AIAnalysisLog(models.Model):
    """
    Log of AI analysis runs for debugging and learning
    """

    # Import here to avoid circular dependency
    from core.models import DailyPlan

    daily_plan = models.ForeignKey(DailyPlan, on_delete=models.CASCADE, related_name="ai_analyses")
    analysis_type = models.CharField(
        max_length=50,
        choices=[
            ("material", "Material Check"),
            ("employee", "Employee Check"),
            ("schedule", "Schedule Check"),
            ("safety", "Safety Check"),
            ("full", "Full Analysis"),
        ],
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    findings = models.JSONField(default=dict, help_text="Analysis results in JSON format")
    auto_actions_taken = models.JSONField(
        default=list, help_text="List of automatic actions taken (activities created, etc.)"
    )
    user_feedback = models.CharField(
        max_length=20,
        choices=[("helpful", "Helpful"), ("not_helpful", "Not Helpful"), ("wrong", "Wrong")],
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "ai_analysis_logs"
        ordering = ["-timestamp"]
        verbose_name = _("AI Analysis Log")
        verbose_name_plural = _("AI Analysis Logs")
        indexes = [
            models.Index(fields=["daily_plan", "-timestamp"]),
            models.Index(fields=["analysis_type"]),
        ]

    def __str__(self):
        return f"AI {self.analysis_type} for {self.daily_plan} at {self.timestamp}"


class AISuggestion(models.Model):
    """
    AI-generated suggestions for daily plans
    """

    # Import here to avoid circular dependency
    from core.models import DailyPlan

    SUGGESTION_TYPES = [
        ("missing_material", "Missing Material"),
        ("employee_conflict", "Employee Conflict"),
        ("task_dependency", "Task Dependency"),
        ("time_issue", "Time Issue"),
        ("safety_concern", "Safety Concern"),
        ("optimization", "Optimization"),
        ("missing_sop", "Missing SOP"),
        ("weather_alert", "Weather Alert"),
    ]

    SEVERITY_LEVELS = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("critical", "Critical"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("dismissed", "Dismissed"),
        ("auto_fixed", "Auto Fixed"),
    ]

    daily_plan = models.ForeignKey(
        DailyPlan, on_delete=models.CASCADE, related_name="ai_suggestions"
    )
    suggestion_type = models.CharField(max_length=50, choices=SUGGESTION_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default="info")

    title = models.CharField(max_length=200)
    description = models.TextField()
    suggested_action = models.TextField(help_text="Recommended action to resolve")

    auto_fixable = models.BooleanField(default=False, help_text="Can AI automatically fix this?")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        db_table = "ai_suggestions"
        ordering = ["-created_at"]
        verbose_name = _("AI Suggestion")
        verbose_name_plural = _("AI Suggestions")
        indexes = [
            models.Index(fields=["daily_plan", "status"]),
            models.Index(fields=["severity", "status"]),
        ]

    def __str__(self):
        return f"{self.get_severity_display()}: {self.title}"

    def accept(self, user):
        """Mark suggestion as accepted"""
        self.status = "accepted"
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.save()

    def dismiss(self, user):
        """Mark suggestion as dismissed"""
        self.status = "dismissed"
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.save()


class VoiceCommand(models.Model):
    """
    Voice commands for debugging and ML training
    """

    # Import here to avoid circular dependency
    from core.models import DailyPlan

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="voice_commands")
    audio_file = models.FileField(upload_to="voice_commands/%Y/%m/", null=True, blank=True)

    transcription = models.TextField(help_text="Speech-to-text result")
    parsed_command = models.JSONField(default=dict, help_text="Parsed command structure")
    execution_result = models.JSONField(default=dict, help_text="Result of command execution")

    success = models.BooleanField(default=False, help_text="Was command executed successfully?")
    timestamp = models.DateTimeField(auto_now_add=True)

    # Related plan (optional)
    daily_plan = models.ForeignKey(
        DailyPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name="voice_commands"
    )

    class Meta:
        db_table = "voice_commands"
        ordering = ["-timestamp"]
        verbose_name = _("Voice Command")
        verbose_name_plural = _("Voice Commands")
        indexes = [
            models.Index(fields=["user", "-timestamp"]),
            models.Index(fields=["success"]),
        ]

    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.transcription[:50]}..."
