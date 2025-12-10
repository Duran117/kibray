"""
Strategic Future Planning Models
=================================

Models for planning future work days with nested structure:
Day → Item → Task → Subtask

This is the NEW Strategic Planner that replaces the old daily ritual system.
These models are for planning FUTURE days (tomorrow, next week, etc.), 
NOT for today's execution (that's Daily Plan).

Owner Requirements:
- Plan multiple future days in advance
- Nested structure: Item (blocks) → Tasks → Subtasks (micro-steps)
- Material requirements with inventory checking
- PM/Employee assignments
- Auto-export to Daily Plan
- Visual Board (Pizarrón) with day slider, dependencies, approval workflow

Created: December 9, 2025
Phase: A1 - Strategic Planner Models
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class StrategicPlanningSession(models.Model):
    """
    Container for multi-day strategic planning session.
    
    A PM or admin creates one session to plan work for multiple future days.
    Each session covers a date range (e.g., Dec 16-20) and belongs to one project.
    
    The session goes through an approval workflow:
    DRAFT → IN_REVIEW → APPROVED (or REQUIRES_CHANGES)
    
    Once approved and exported, it creates DailyPlan + PlannedActivity records.
    """
    
    STATUS_CHOICES = [
        ('DRAFT', _('Draft')),
        ('IN_REVIEW', _('In Review')),
        ('APPROVED', _('Approved')),
        ('REQUIRES_CHANGES', _('Requires Changes')),
    ]
    
    # Ownership & Project
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='strategic_planning_sessions',
        verbose_name=_('Created By'),
        help_text=_('PM or admin who created this planning session')
    )
    
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='strategic_planning_sessions',
        verbose_name=_('Project'),
        help_text=_('Which project this planning is for')
    )
    
    # Date Range
    date_range_start = models.DateField(
        verbose_name=_('Start Date'),
        help_text=_('First day being planned (e.g., Dec 16)')
    )
    
    date_range_end = models.DateField(
        verbose_name=_('End Date'),
        help_text=_('Last day being planned (e.g., Dec 20)')
    )
    
    # Status & Approval
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        verbose_name=_('Status')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('Planning Notes'),
        help_text=_('General notes about this planning session')
    )
    
    # Approval Tracking
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_strategic_plans',
        verbose_name=_('Approved By')
    )
    
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Approval Date')
    )
    
    # Export Tracking
    exported_to_daily_plan = models.BooleanField(
        default=False,
        verbose_name=_('Exported to Daily Plan'),
        help_text=_('Has this plan been exported to Daily Plan system?')
    )
    
    exported_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Export Date')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Strategic Planning Session')
        verbose_name_plural = _('Strategic Planning Sessions')
        indexes = [
            models.Index(fields=['project', 'date_range_start']),
            models.Index(fields=['status']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.project.name} - {self.date_range_start} to {self.date_range_end} ({self.get_status_display()})"
    
    def clean(self):
        """Validate date range"""
        errors = {}
        
        if self.date_range_start and self.date_range_end:
            if self.date_range_end < self.date_range_start:
                errors['date_range_end'] = _('End date must be after or equal to start date.')
            
            # Warn if planning too far in advance (more than 90 days)
            if self.date_range_start:
                days_ahead = (self.date_range_start - timezone.localdate()).days
                if days_ahead > 90:
                    # This is just a warning, not an error
                    pass  # Could add a soft warning mechanism
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def total_days(self):
        """Calculate number of days in this planning session"""
        if self.date_range_start and self.date_range_end:
            return (self.date_range_end - self.date_range_start).days + 1
        return 0
    
    @property
    def is_approved(self):
        """Check if plan is approved"""
        return self.status == 'APPROVED'
    
    @property
    def can_export(self):
        """Check if plan can be exported to Daily Plan"""
        return self.is_approved and not self.exported_to_daily_plan


class StrategicDay(models.Model):
    """
    One specific day within a strategic planning session.
    
    Example: Monday Dec 16 within a session planning Dec 16-20.
    
    Each day contains multiple Items (work blocks/phases).
    Each day can optionally be linked to an existing calendar ScheduleItem.
    """
    
    # Parent Session
    session = models.ForeignKey(
        StrategicPlanningSession,
        on_delete=models.CASCADE,
        related_name='days',
        verbose_name=_('Planning Session')
    )
    
    # The Day Being Planned
    target_date = models.DateField(
        verbose_name=_('Target Date'),
        help_text=_('The specific day this plan is for')
    )
    
    # Day Notes
    notes = models.TextField(
        blank=True,
        verbose_name=_('Day Notes'),
        help_text=_('Specific notes about this day\'s work')
    )
    
    # Estimated Total Hours
    estimated_total_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Estimated Total Hours'),
        help_text=_('Total estimated hours for all work on this day')
    )
    
    # Link to Existing Calendar Item (Optional)
    linked_schedule_item = models.ForeignKey(
        'ScheduleItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='strategic_days',
        verbose_name=_('Linked Schedule Item'),
        help_text=_('Optional: Link to existing calendar item (e.g., "Exterior Painting - 15 days")')
    )
    
    class Meta:
        unique_together = ['session', 'target_date']
        ordering = ['target_date']
        verbose_name = _('Strategic Day')
        verbose_name_plural = _('Strategic Days')
        indexes = [
            models.Index(fields=['session', 'target_date']),
        ]
    
    def __str__(self):
        return f"{self.target_date} - {self.session.project.name}"
    
    def clean(self):
        """Validate that target_date is within session date range"""
        errors = {}
        
        if self.session and self.target_date:
            if self.target_date < self.session.date_range_start:
                errors['target_date'] = _(
                    f'Target date must be within session range '
                    f'({self.session.date_range_start} to {self.session.date_range_end})'
                )
            
            if self.target_date > self.session.date_range_end:
                errors['target_date'] = _(
                    f'Target date must be within session range '
                    f'({self.session.date_range_start} to {self.session.date_range_end})'
                )
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def day_name(self):
        """Get day of week name (e.g., 'Monday')"""
        return self.target_date.strftime('%A')
    
    @property
    def items_count(self):
        """Count number of items planned for this day"""
        return self.items.count()


class StrategicItem(models.Model):
    """
    One work item (block/phase) within a strategic day.
    
    Examples:
    - "Install kitchen cabinets"
    - "Paint living room walls"
    - "Install electrical outlets in bedroom"
    
    Each item contains multiple Tasks.
    Items can be assigned to specific employees and have material requirements.
    Items represent larger work blocks that are broken down into actionable tasks.
    """
    
    PRIORITY_CHOICES = [
        ('CRITICAL', _('Critical - Must Complete')),
        ('HIGH', _('High Priority')),
        ('MEDIUM', _('Medium Priority')),
        ('LOW', _('Low Priority')),
    ]
    
    # Parent Day
    strategic_day = models.ForeignKey(
        StrategicDay,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Strategic Day')
    )
    
    # Item Details
    title = models.CharField(
        max_length=255,
        verbose_name=_('Item Title'),
        help_text=_('What work needs to be done? (e.g., "Install kitchen cabinets")')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Detailed description of this work item')
    )
    
    # Order & Priority
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Order'),
        help_text=_('Display order within the day (0, 1, 2...)')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='MEDIUM',
        verbose_name=_('Priority')
    )
    
    # Time Estimation
    estimated_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Estimated Hours'),
        help_text=_('Total estimated hours for this item (sum of all tasks)')
    )
    
    # Assignments
    assigned_to = models.ManyToManyField(
        'Employee',
        blank=True,
        related_name='strategic_items',
        verbose_name=_('Assigned To'),
        help_text=_('Which employees will work on this item?')
    )
    
    # Location/Area
    location_area = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Location/Area'),
        help_text=_('Where will this work happen? (e.g., "Kitchen", "Living Room", "Exterior")')
    )
    
    # Link to existing catalog/templates
    linked_activity_template = models.ForeignKey(
        'ActivityTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='strategic_items',
        verbose_name=_('Linked Activity Template'),
        help_text=_('Optional: Use existing activity template as reference')
    )
    
    # Completion Tracking (for export to Daily Plan)
    exported_to_daily_plan = models.BooleanField(
        default=False,
        verbose_name=_('Exported to Daily Plan')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        ordering = ['strategic_day', 'order', 'priority']
        verbose_name = _('Strategic Item')
        verbose_name_plural = _('Strategic Items')
        indexes = [
            models.Index(fields=['strategic_day', 'order']),
            models.Index(fields=['priority']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.strategic_day.target_date})"
    
    def clean(self):
        """Validate item data"""
        errors = {}
        
        # Ensure estimated_hours is positive
        if self.estimated_hours is not None and self.estimated_hours < 0:
            errors['estimated_hours'] = _('Estimated hours cannot be negative.')
        
        # Ensure order is non-negative
        if self.order < 0:
            errors['order'] = _('Order must be 0 or greater.')
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def session(self):
        """Get parent session through strategic_day"""
        return self.strategic_day.session
    
    @property
    def target_date(self):
        """Get target date from parent strategic_day"""
        return self.strategic_day.target_date
    
    @property
    def project(self):
        """Get project through session"""
        return self.strategic_day.session.project
    
    @property
    def tasks_count(self):
        """Count number of tasks within this item"""
        return self.tasks.count()
    
    @property
    def is_critical(self):
        """Check if this is a critical priority item"""
        return self.priority == 'CRITICAL'
    
    def calculate_total_estimated_hours(self):
        """
        Calculate total estimated hours from all child tasks.
        This should be called when tasks are updated.
        """
        total = self.tasks.aggregate(
            total=models.Sum('estimated_hours')
        )['total'] or 0
        return total
    
    def sync_estimated_hours_from_tasks(self):
        """
        Update estimated_hours based on sum of all task hours.
        Call this after tasks are created/updated.
        """
        self.estimated_hours = self.calculate_total_estimated_hours()
        self.save(update_fields=['estimated_hours'])


class StrategicTask(models.Model):
    """
    A specific actionable task within a Strategic Item.
    
    Examples for "Install kitchen cabinets" item:
    - "Unpack cabinets and check for damage"
    - "Install upper cabinets"
    - "Install base cabinets"
    - "Install hardware (handles/knobs)"
    
    Tasks are the unit of work that gets assigned and tracked.
    """
    
    # Parent Item
    strategic_item = models.ForeignKey(
        StrategicItem,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name=_('Strategic Item')
    )
    
    # Task Details
    description = models.CharField(
        max_length=255,
        verbose_name=_('Task Description'),
        help_text=_('Actionable task description (e.g., "Install upper cabinets")')
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Order'),
        help_text=_('Execution order within the item')
    )
    
    # Time Estimation
    estimated_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name=_('Estimated Hours'),
        help_text=_('Estimated time to complete this specific task')
    )
    
    # Assignment Override (Optional)
    assigned_to = models.ManyToManyField(
        'Employee',
        blank=True,
        related_name='strategic_tasks',
        verbose_name=_('Assigned To (Override)'),
        help_text=_('Override item assignment for this specific task (optional)')
    )
    
    # Link to existing template task
    linked_task_template = models.ForeignKey(
        'TaskTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='strategic_tasks',
        verbose_name=_('Linked Task Template')
    )
    
    # Completion Tracking (for export)
    exported_to_daily_plan = models.BooleanField(
        default=False,
        verbose_name=_('Exported to Daily Plan')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        ordering = ['strategic_item', 'order']
        verbose_name = _('Strategic Task')
        verbose_name_plural = _('Strategic Tasks')
        indexes = [
            models.Index(fields=['strategic_item', 'order']),
        ]
    
    def __str__(self):
        return f"{self.description} ({self.strategic_item.title})"
    
    def clean(self):
        """Validate task data"""
        if self.estimated_hours < 0:
            raise ValidationError({'estimated_hours': _('Estimated hours cannot be negative.')})
            
        if self.order < 0:
            raise ValidationError({'order': _('Order must be 0 or greater.')})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Update parent item's total hours
        # Note: We do this in a post_save signal usually, but for simplicity
        # we can rely on explicit calls or signals. 
        # Ideally, the view/serializer handles the sync, or a signal.
    
    @property
    def subtasks_count(self):
        """Count number of subtasks"""
        return self.subtasks.count()


class StrategicSubtask(models.Model):
    """
    A micro-step or checklist item within a Strategic Task.
    
    Examples for "Install upper cabinets" task:
    - "Locate studs"
    - "Mark level line"
    - "Pre-drill holes"
    - "Hang cabinet box"
    
    Subtasks are simple boolean check items.
    """
    
    # Parent Task
    strategic_task = models.ForeignKey(
        StrategicTask,
        on_delete=models.CASCADE,
        related_name='subtasks',
        verbose_name=_('Strategic Task')
    )
    
    # Subtask Details
    description = models.CharField(
        max_length=255,
        verbose_name=_('Description'),
        help_text=_('Micro-step description (e.g., "Locate studs")')
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Order'),
        help_text=_('Checklist order')
    )
    
    # Completion Tracking (for export)
    exported_to_daily_plan = models.BooleanField(
        default=False,
        verbose_name=_('Exported to Daily Plan')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        ordering = ['strategic_task', 'order']
        verbose_name = _('Strategic Subtask')
        verbose_name_plural = _('Strategic Subtasks')
        indexes = [
            models.Index(fields=['strategic_task', 'order']),
        ]
    
    def __str__(self):
        return self.description
    
    def clean(self):
        """Validate subtask data"""
        if self.order < 0:
            raise ValidationError({'order': _('Order must be 0 or greater.')})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class StrategicMaterialRequirement(models.Model):
    """
    Material required for a Strategic Item.
    
    Examples:
    - "2x4 Lumber" (Quantity: 10)
    - "Drywall Screws" (Quantity: 1 Box)
    - "Paint - Alabaster" (Quantity: 2 Gallons)
    
    Can be linked to inventory or catalog items.
    Used to generate pick lists or purchase orders.
    """
    
    # Parent Item
    strategic_item = models.ForeignKey(
        StrategicItem,
        on_delete=models.CASCADE,
        related_name='material_requirements',
        verbose_name=_('Strategic Item')
    )
    
    # Material Details
    name = models.CharField(
        max_length=255,
        verbose_name=_('Material Name'),
        help_text=_('Name of material needed (e.g., "2x4 Lumber")')
    )
    
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Quantity'),
        help_text=_('How much is needed?')
    )
    
    unit = models.CharField(
        max_length=50,
        verbose_name=_('Unit'),
        help_text=_('Unit of measure (e.g., "Each", "Box", "Gallon")')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
        help_text=_('Specific details (brand, color, size)')
    )
    
    # Inventory Links (Optional)
    linked_catalog_item = models.ForeignKey(
        'MaterialCatalog',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='strategic_requirements',
        verbose_name=_('Catalog Item')
    )
    
    linked_inventory_item = models.ForeignKey(
        'InventoryItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='strategic_requirements',
        verbose_name=_('Inventory Item')
    )
    
    # Status
    is_on_hand = models.BooleanField(
        default=False,
        verbose_name=_('Is On Hand?'),
        help_text=_('Do we already have this material available?')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        verbose_name = _('Strategic Material Requirement')
        verbose_name_plural = _('Strategic Material Requirements')
        indexes = [
            models.Index(fields=['strategic_item']),
            models.Index(fields=['is_on_hand']),
        ]
    
    def __str__(self):
        return f"{self.quantity} {self.unit} - {self.name}"
    
    def clean(self):
        """Validate material data"""
        if self.quantity < 0:
            raise ValidationError({'quantity': _('Quantity cannot be negative.')})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class StrategicDependency(models.Model):
    """
    Dependency between two Strategic Items.
    
    Example: "Paint Walls" (Successor) depends on "Install Drywall" (Predecessor).
    Used for the Visual Board to show connections and enforce order.
    """
    
    DEPENDENCY_TYPES = [
        ('FS', _('Finish to Start')),  # Most common: A must finish before B starts
        ('SS', _('Start to Start')),   # A must start before B starts
        ('FF', _('Finish to Finish')), # A must finish before B finishes
        ('SF', _('Start to Finish')),  # A must start before B finishes
    ]
    
    # The item that must happen FIRST
    predecessor = models.ForeignKey(
        StrategicItem,
        on_delete=models.CASCADE,
        related_name='successors',
        verbose_name=_('Predecessor Item'),
        help_text=_('The item that must be completed first')
    )
    
    # The item that happens SECOND (depends on the first)
    successor = models.ForeignKey(
        StrategicItem,
        on_delete=models.CASCADE,
        related_name='predecessors',
        verbose_name=_('Successor Item'),
        help_text=_('The item that is waiting for the predecessor')
    )
    
    dependency_type = models.CharField(
        max_length=2,
        choices=DEPENDENCY_TYPES,
        default='FS',
        verbose_name=_('Dependency Type')
    )
    
    lag_days = models.IntegerField(
        default=0,
        verbose_name=_('Lag (Days)'),
        help_text=_('Optional delay between items (e.g., 1 day for drying)')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['predecessor', 'successor']
        verbose_name = _('Strategic Dependency')
        verbose_name_plural = _('Strategic Dependencies')
        indexes = [
            models.Index(fields=['predecessor']),
            models.Index(fields=['successor']),
        ]
    
    def __str__(self):
        return f"{self.predecessor} -> {self.successor} ({self.dependency_type})"
    
    def clean(self):
        """Validate dependency"""
        if self.predecessor_id == self.successor_id:
            raise ValidationError(_('An item cannot depend on itself.'))
            
        # Basic circular check (direct loop only)
        # Full circular check would require graph traversal, usually done in view/service
        if StrategicDependency.objects.filter(
            predecessor=self.successor, 
            successor=self.predecessor
        ).exists():
            raise ValidationError(_('Circular dependency detected.'))
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
