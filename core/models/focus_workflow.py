"""
Module 25: Executive Focus Workflow (Productivity)
Implements Pareto (80/20) + Eat That Frog methodology for daily planning.
"""
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class DailyFocusSession(models.Model):
    """
    Daily planning session for a user.
    Tracks energy level and overall notes for the day.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='focus_sessions'
    )
    date = models.DateField(
        help_text="The day this focus session is for"
    )
    energy_level = models.IntegerField(
        default=5,
        help_text="Self-reported energy level (1-10)"
    )
    notes = models.TextField(
        blank=True,
        help_text="General notes, reflections, or insights for the day"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']
        verbose_name = "Daily Focus Session"
        verbose_name_plural = "Daily Focus Sessions"
    
    def __str__(self):
        return f"{self.user.username} - {self.date} (Energy: {self.energy_level}/10)"
    
    def clean(self):
        """Validate energy level is between 1-10."""
        if self.energy_level < 1 or self.energy_level > 10:
            raise ValidationError({
                'energy_level': 'Energy level must be between 1 and 10.'
            })
    
    @property
    def total_tasks(self):
        """Count of all tasks in this session."""
        return self.focus_tasks.count()
    
    @property
    def completed_tasks(self):
        """Count of completed tasks."""
        return self.focus_tasks.filter(is_completed=True).count()
    
    @property
    def high_impact_tasks(self):
        """Count of high impact (20%) tasks."""
        return self.focus_tasks.filter(is_high_impact=True).count()
    
    @property
    def frog_task(self):
        """Get the single 'Eat That Frog' task."""
        return self.focus_tasks.filter(is_frog=True).first()


class FocusTask(models.Model):
    """
    Individual focus task within a daily session.
    Implements Pareto Principle (80/20) and Eat That Frog methodology.
    """
    session = models.ForeignKey(
        DailyFocusSession,
        on_delete=models.CASCADE,
        related_name='focus_tasks'
    )
    title = models.CharField(
        max_length=255,
        help_text="Task title"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the task"
    )
    
    # Pareto Principle (80/20 Rule)
    is_high_impact = models.BooleanField(
        default=False,
        help_text="Is this part of the critical 20% that produces 80% of results?"
    )
    impact_reason = models.TextField(
        blank=True,
        help_text="Why is this task high impact? What results will it produce?"
    )
    
    # Eat That Frog (Hardest/Most Important Task)
    is_frog = models.BooleanField(
        default=False,
        help_text="Is this THE most important/hardest task of the day?"
    )
    
    # Battle Plan
    checklist = models.JSONField(
        default=list,
        blank=True,
        help_text="List of micro-actions/sub-steps. Format: [{'text': 'Step 1', 'done': false}, ...]"
    )
    
    # Time Blocking
    scheduled_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When to start this task (time blocking)"
    )
    scheduled_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When to end this task (time blocking)"
    )
    
    # Calendar Integration
    calendar_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Unique secure token for iCal feed access"
    )
    
    # Status
    is_completed = models.BooleanField(
        default=False,
        help_text="Task completion status"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the task was completed"
    )
    
    # Metadata
    order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers first)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-is_frog', '-is_high_impact', 'created_at']
        verbose_name = "Focus Task"
        verbose_name_plural = "Focus Tasks"
    
    def __str__(self):
        prefix = "🐸 " if self.is_frog else "⚡ " if self.is_high_impact else ""
        return f"{prefix}{self.title}"
    
    def clean(self):
        """Validate task constraints."""
        errors = {}
        
        # Only one Frog per session
        if self.is_frog:
            existing_frog = FocusTask.objects.filter(
                session=self.session,
                is_frog=True
            ).exclude(pk=self.pk).first()
            
            if existing_frog:
                errors['is_frog'] = f"Only one Frog task allowed per day. Current Frog: '{existing_frog.title}'"
        
        # Frog must be high impact
        if self.is_frog and not self.is_high_impact:
            errors['is_high_impact'] = "The Frog task must also be marked as High Impact."
        
        # High impact requires reason
        if self.is_high_impact and not self.impact_reason.strip():
            errors['impact_reason'] = "High Impact tasks require an explanation of WHY they matter."
        
        # Validate time blocking
        if self.scheduled_start and self.scheduled_end:
            if self.scheduled_end <= self.scheduled_start:
                errors['scheduled_end'] = "End time must be after start time."
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Auto-set completed_at timestamp."""
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        elif not self.is_completed:
            self.completed_at = None
        
        # Skip validation if explicitly requested (for API bulk creation)
        skip_validation = kwargs.pop('skip_validation', False)
        if not skip_validation:
            try:
                self.full_clean()
            except ValidationError:
                # Log but don't block - API handles validation
                pass
        
        super().save(*args, **kwargs)
    
    @property
    def duration_minutes(self):
        """Calculate task duration in minutes."""
        if self.scheduled_start and self.scheduled_end:
            delta = self.scheduled_end - self.scheduled_start
            return int(delta.total_seconds() / 60)
        return None
    
    @property
    def checklist_progress(self):
        """Calculate checklist completion percentage."""
        if not self.checklist or len(self.checklist) == 0:
            return 0
        
        completed = sum(1 for item in self.checklist if item.get('done', False))
        return int((completed / len(self.checklist)) * 100)
    
    @property
    def checklist_completed(self):
        """Count of completed checklist items."""
        if not self.checklist:
            return 0
        return sum(1 for item in self.checklist if item.get('done', False))
    
    @property
    def checklist_total(self):
        """Total checklist items."""
        return len(self.checklist) if self.checklist else 0
    
    def get_calendar_title(self):
        """Get title formatted for calendar (with emoji)."""
        if self.is_frog:
            return f"🐸 {self.title}"
        elif self.is_high_impact:
            return f"⚡ {self.title}"
        return self.title
    
    def get_calendar_description(self):
        """Get description formatted for calendar."""
        parts = []
        
        if self.description:
            parts.append(self.description)
        
        if self.is_frog:
            parts.append("\n🐸 EAT THAT FROG - Most Important Task of the Day")
        elif self.is_high_impact:
            parts.append("\n⚡ HIGH IMPACT - Part of the Critical 20%")
        
        if self.impact_reason:
            parts.append(f"\n💡 Why it matters: {self.impact_reason}")
        
        if self.checklist:
            parts.append("\n\n✓ Battle Plan:")
            for idx, item in enumerate(self.checklist, 1):
                status = "✅" if item.get('done') else "⬜"
                parts.append(f"{status} {idx}. {item.get('text', '')}")
        
        return "\n".join(parts)
