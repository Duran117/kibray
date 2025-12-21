"""
Module 25: The Strategic Planner (Admin & PM Productivity)
Integrates Psychology (Tony Robbins' Triad), Strategy (Goals), and Execution (Pareto/Time-Blocking)

CRITICAL: These models are for EXECUTIVE MANAGEMENT ONLY, not for construction project tasks.
"""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class LifeVision(models.Model):
    """
    The North Star - High-level life/business goals that drive everything.
    Example: "Achieve Financial Freedom", "Become Market Leader in Construction"
    """

    SCOPE_CHOICES = [
        ("PERSONAL", "Personal Life"),
        ("BUSINESS", "Business/Career"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="life_visions"
    )
    title = models.CharField(
        max_length=255, help_text="The goal/vision (e.g., 'Financial Freedom', 'Market Leadership')"
    )
    scope = models.CharField(
        max_length=20, choices=SCOPE_CHOICES, help_text="Is this a personal or business goal?"
    )
    deep_why = models.TextField(
        help_text="The EMOTIONAL anchor - WHY does this matter? What will it give you?"
    )
    deadline = models.DateField(
        null=True, blank=True, help_text="Target completion date (if applicable)"
    )
    progress_pct = models.IntegerField(default=0, help_text="Estimated progress (0-100)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Life Vision"
        verbose_name_plural = "Life Visions"

    def __str__(self):
        return f"{self.title} ({self.get_scope_display()})"

    def clean(self):
        """Validate fields"""
        if not self.deep_why or not self.deep_why.strip():
            raise ValidationError(
                {"deep_why": "You MUST articulate WHY this vision matters emotionally."}
            )

        if self.progress_pct < 0 or self.progress_pct > 100:
            raise ValidationError({"progress_pct": "Progress must be between 0 and 100."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ExecutiveHabit(models.Model):
    """
    Routine Maintenance - Personal/Professional habits separate from daily work tasks.
    Example: "Morning Gym", "Read 30 minutes", "Strategic Thinking Time"
    """

    FREQUENCY_CHOICES = [
        ("DAILY", "Daily"),
        ("WEEKLY", "Weekly"),
        ("MONTHLY", "Monthly"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="executive_habits"
    )
    title = models.CharField(
        max_length=255, help_text="Habit name (e.g., 'Morning Gym', 'Read 30 minutes')"
    )
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default="DAILY",
        help_text="How often should this be done?",
    )
    is_active = models.BooleanField(
        default=True, help_text="Is this habit currently being tracked?"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["frequency", "title"]
        verbose_name = "Executive Habit"
        verbose_name_plural = "Executive Habits"

    def __str__(self):
        return f"{self.title} ({self.get_frequency_display()})"


class DailyRitualSession(models.Model):
    """
    The Container - Captures the daily executive planning session.
    Includes mindset work (physiology, gratitude, intention).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ritual_sessions"
    )
    date = models.DateField(help_text="The day this ritual is for")

    # PHASE 1: STATE & FOUNDATION (Tony Robbins' Triad)
    physiology_check = models.BooleanField(
        default=False, help_text="Did you do the priming exercise? (Stand up, breathe, move)"
    )
    gratitude_entries = models.JSONField(
        default=list,
        blank=True,
        help_text="List of 3 things you're grateful for. Format: ['Item 1', 'Item 2', 'Item 3']",
    )
    daily_intention = models.TextField(blank=True, help_text="Your main focus/intention for today")

    # Energy tracking (from Focus Workflow)
    energy_level = models.IntegerField(default=5, help_text="Self-reported energy level (1-10)")

    # Habit tracking for today
    habits_checked = models.JSONField(
        default=list,
        blank=True,
        help_text="List of habit IDs checked/committed to today. Format: [1, 2, 3]",
    )

    # Metadata
    completed_at = models.DateTimeField(
        null=True, blank=True, help_text="When the ritual was completed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]
        unique_together = ["user", "date"]
        verbose_name = "Daily Ritual Session"
        verbose_name_plural = "Daily Ritual Sessions"

    def __str__(self):
        return f"{self.user.username} - {self.date}"

    def clean(self):
        """Validate energy level"""
        if self.energy_level < 1 or self.energy_level > 10:
            raise ValidationError({"energy_level": "Energy level must be between 1 and 10."})

    @property
    def is_completed(self):
        """Check if ritual is completed"""
        return self.completed_at is not None

    @property
    def total_power_actions(self):
        """Count of all power actions"""
        return self.power_actions.count()

    @property
    def completed_power_actions(self):
        """Count of completed power actions"""
        return self.power_actions.filter(status="DONE").count()

    @property
    def high_impact_actions(self):
        """Count of 80/20 actions"""
        return self.power_actions.filter(is_80_20=True).count()

    @property
    def frog_action(self):
        """Get THE frog action"""
        return self.power_actions.filter(is_frog=True).first()

    def mark_completed(self):
        """Mark ritual as completed"""
        if not self.completed_at:
            self.completed_at = timezone.now()
            self.save(update_fields=["completed_at"])


class PowerAction(models.Model):
    """
    Strategic Tasks - Executive management actions (NOT construction project tasks).
    These are the high-level strategic actions that advance Life Visions.

    CRITICAL: This is NOT for operational project work. This is for executive strategy.
    """

    STATUS_CHOICES = [
        ("DRAFT", "Draft/Inbox"),
        ("SCHEDULED", "Scheduled"),
        ("DONE", "Completed"),
    ]

    session = models.ForeignKey(
        DailyRitualSession, on_delete=models.CASCADE, related_name="power_actions"
    )
    title = models.CharField(max_length=255, help_text="Strategic action title")
    description = models.TextField(blank=True, help_text="Detailed description")

    # PARETO PRINCIPLE (80/20 Rule)
    is_80_20 = models.BooleanField(
        default=False, help_text="Is this a HIGH IMPACT action (top 20%)?"
    )
    impact_reason = models.TextField(
        blank=True, help_text="WHY is this high impact? What will it advance?"
    )

    # EAT THE FROG
    is_frog = models.BooleanField(
        default=False, help_text="Is this THE #1 most important action today?"
    )

    # VISION ALIGNMENT
    linked_vision = models.ForeignKey(
        LifeVision,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="power_actions",
        help_text="Which Life Vision does this advance?",
    )

    # EXECUTION PLAN
    micro_steps = models.JSONField(
        default=list,
        blank=True,
        help_text="Checklist of micro-actions. Format: [{'text': 'Step 1', 'done': false}, ...]",
    )

    # TIME BLOCKING
    scheduled_start = models.DateTimeField(
        null=True, blank=True, help_text="When to start (time blocking)"
    )
    scheduled_end = models.DateTimeField(
        null=True, blank=True, help_text="When to end (time blocking)"
    )

    # CALENDAR INTEGRATION
    ical_uid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, help_text="Unique identifier for iCal sync"
    )

    # STATUS
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="DRAFT", help_text="Current status"
    )
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When completed")

    # METADATA
    order = models.IntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-is_frog", "-is_80_20", "created_at"]
        verbose_name = "Power Action"
        verbose_name_plural = "Power Actions"

    def __str__(self):
        prefix = "🐸 " if self.is_frog else "⚡ " if self.is_80_20 else ""
        return f"{prefix}{self.title}"

    def clean(self):
        """Validate constraints"""
        errors = {}

        # Only one Frog per session
        if self.is_frog:
            existing_frog = (
                PowerAction.objects.filter(session=self.session, is_frog=True)
                .exclude(pk=self.pk)
                .first()
            )

            if existing_frog:
                errors["is_frog"] = (
                    f"Only ONE Frog allowed per session. Current: '{existing_frog.title}'"
                )

        # Frog must be high impact
        if self.is_frog and not self.is_80_20:
            errors["is_80_20"] = "The Frog MUST be a High Impact (80/20) action."

        # High impact requires reason
        if self.is_80_20 and not self.impact_reason.strip():
            errors["impact_reason"] = (
                "High Impact actions require an explanation of WHY they matter."
            )

        # Validate time blocking
        if (
            self.scheduled_start
            and self.scheduled_end
            and self.scheduled_end <= self.scheduled_start
        ):
            errors["scheduled_end"] = "End time must be after start time."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Auto-update status and timestamps"""
        # Auto-set completed_at
        if self.status == "DONE" and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != "DONE":
            self.completed_at = None

        # Validate if session exists
        if self.session_id:
            self.full_clean()

        super().save(*args, **kwargs)

    @property
    def duration_minutes(self):
        """Calculate duration"""
        if self.scheduled_start and self.scheduled_end:
            delta = self.scheduled_end - self.scheduled_start
            return int(delta.total_seconds() / 60)
        return None

    @property
    def micro_steps_progress(self):
        """Calculate checklist completion percentage"""
        if not self.micro_steps or len(self.micro_steps) == 0:
            return 0

        completed = sum(1 for item in self.micro_steps if item.get("done", False))
        return int((completed / len(self.micro_steps)) * 100)

    @property
    def micro_steps_completed(self):
        """Count of completed micro steps"""
        if not self.micro_steps:
            return 0
        return sum(1 for item in self.micro_steps if item.get("done", False))

    @property
    def micro_steps_total(self):
        """Total micro steps"""
        return len(self.micro_steps) if self.micro_steps else 0

    def get_calendar_title(self):
        """Get title formatted for calendar"""
        if self.is_frog:
            return f"🐸 {self.title}"
        elif self.is_80_20:
            return f"⚡ {self.title}"
        return self.title

    def get_calendar_description(self):
        """Get description formatted for calendar"""
        parts = []

        if self.description:
            parts.append(self.description)

        if self.is_frog:
            parts.append("\n🐸 THE FROG - #1 Priority for Today")
        elif self.is_80_20:
            parts.append("\n⚡ HIGH IMPACT - Top 20% Action")

        if self.impact_reason:
            parts.append(f"\n💡 Why it matters: {self.impact_reason}")

        if self.linked_vision:
            parts.append(f"\n🎯 Advances: {self.linked_vision.title}")

        if self.micro_steps:
            parts.append("\n\n📋 Battle Plan:")
            for idx, step in enumerate(self.micro_steps, 1):
                status = "✅" if step.get("done") else "⬜"
                parts.append(f"{status} {idx}. {step.get('text', '')}")

        return "\n".join(parts)


class HabitCompletion(models.Model):
    """
    Track when habits are completed.
    Separate from PowerActions to keep operational data clean.
    """

    habit = models.ForeignKey(ExecutiveHabit, on_delete=models.CASCADE, related_name="completions")
    session = models.ForeignKey(
        DailyRitualSession,
        on_delete=models.CASCADE,
        related_name="habit_completions",
        null=True,
        blank=True,
    )
    completed_date = models.DateField()
    notes = models.TextField(blank=True, help_text="Optional notes about completion")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_date"]
        unique_together = ["habit", "completed_date"]
        verbose_name = "Habit Completion"
        verbose_name_plural = "Habit Completions"

    def __str__(self):
        return f"{self.habit.title} - {self.completed_date}"
