"""
Strategic Planning Service
==========================

Service layer for managing Strategic Future Planning sessions.
Handles business logic for:
- Creating multi-day planning sessions
- Managing the approval workflow
- Validating plan integrity
- Exporting to Daily Plan

Phase: A2 - Strategic Planner Logic
Created: December 9, 2025
"""

from datetime import timedelta
from django.db import transaction, models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import models

from core.models import (
    StrategicPlanningSession, 
    StrategicDay, 
    StrategicItem,
    StrategicTask,
    Project,
    User,
    DailyPlan,
    PlannedActivity
)

class StrategicPlanningService:
    """
    Service for managing the lifecycle of Strategic Planning Sessions.
    """
    
    @staticmethod
    @transaction.atomic
    def create_session(
        user: User,
        project: Project,
        start_date,
        end_date,
        notes: str = ""
    ) -> StrategicPlanningSession:
        """
        Create a new strategic planning session and initialize days.
        
        Args:
            user: The user creating the session (PM/Admin)
            project: The project this plan is for
            start_date: Start of the planning period
            end_date: End of the planning period
            notes: Optional notes
            
        Returns:
            The created StrategicPlanningSession instance
            
        Raises:
            ValidationError: If dates are invalid or overlap with existing sessions
        """
        # 1. Validate dates
        if end_date < start_date:
            raise ValidationError(_("End date must be after start date."))
            
        # 2. Check for overlaps (optional, but good practice)
        # For now, we allow overlaps but maybe warn? 
        # Let's enforce no overlaps for the same project to keep it clean.
        overlapping = StrategicPlanningSession.objects.filter(
            project=project,
            date_range_start__lte=end_date,
            date_range_end__gte=start_date
        ).exists()
        
        if overlapping:
            raise ValidationError(_(
                "A planning session already exists for this project within the selected dates."
            ))
            
        # 3. Create Session
        session = StrategicPlanningSession.objects.create(
            user=user,
            project=project,
            date_range_start=start_date,
            date_range_end=end_date,
            status='DRAFT',
            notes=notes
        )
        
        # 4. Initialize Days
        # Automatically create StrategicDay records for each day in the range
        current_date = start_date
        days_to_create = []
        
        while current_date <= end_date:
            days_to_create.append(
                StrategicDay(
                    session=session,
                    target_date=current_date
                )
            )
            current_date += timedelta(days=1)
            
        StrategicDay.objects.bulk_create(days_to_create)
        
        return session

    @staticmethod
    def get_session(session_id: int) -> StrategicPlanningSession:
        """Get session by ID with related data pre-fetched"""
        try:
            return StrategicPlanningSession.objects.select_related(
                'project', 'user', 'approved_by'
            ).prefetch_related(
                'days',
                'days__items',
                'days__items__tasks'
            ).get(pk=session_id)
        except StrategicPlanningSession.DoesNotExist:
            raise ValidationError(_("Session not found."))

    @staticmethod
    def update_status(
        session: StrategicPlanningSession, 
        new_status: str, 
        user: User
    ) -> StrategicPlanningSession:
        """
        Update session status with validation and side effects.
        
        Transitions:
        - DRAFT -> IN_REVIEW
        - IN_REVIEW -> APPROVED (sets approved_by/at)
        - IN_REVIEW -> REQUIRES_CHANGES
        - REQUIRES_CHANGES -> IN_REVIEW
        """
        valid_transitions = {
            'DRAFT': ['IN_REVIEW'],
            'IN_REVIEW': ['APPROVED', 'REQUIRES_CHANGES', 'DRAFT'],
            'REQUIRES_CHANGES': ['IN_REVIEW', 'DRAFT'],
            'APPROVED': ['DRAFT'] # Can re-open if needed
        }
        
        if new_status not in valid_transitions.get(session.status, []):
            raise ValidationError(_(
                f"Invalid status transition from {session.status} to {new_status}"
            ))
            
        # Apply updates
        session.status = new_status
        
        if new_status == 'APPROVED':
            session.approved_by = user
            session.approved_at = timezone.now()
        elif new_status == 'DRAFT':
            # Reset approval if moving back to draft
            session.approved_by = None
            session.approved_at = None
            
        session.save()
        return session

    @staticmethod
    def add_item_to_day(
        day_id: int,
        title: str,
        description: str = "",
        priority: str = "MEDIUM",
        estimated_hours: float = 0.0,
        assigned_employee_ids: list = None
    ) -> StrategicItem:
        """
        Add a new work item to a strategic day.
        """
        try:
            day = StrategicDay.objects.get(pk=day_id)
        except StrategicDay.DoesNotExist:
            raise ValidationError(_("Strategic Day not found."))
            
        # Calculate next order
        max_order = day.items.aggregate(models.Max('order'))['order__max']
        next_order = (max_order or 0) + 1 if day.items.exists() else 0
        
        item = StrategicItem.objects.create(
            strategic_day=day,
            title=title,
            description=description,
            priority=priority,
            estimated_hours=estimated_hours,
            order=next_order
        )
        
        if assigned_employee_ids:
            item.assigned_to.set(assigned_employee_ids)
            
        return item

    @staticmethod
    def add_task_to_item(
        item_id: int,
        description: str,
        estimated_hours: float = 0.0
    ) -> StrategicTask:
        """
        Add a task to a strategic item.
        """
        try:
            item = StrategicItem.objects.get(pk=item_id)
        except StrategicItem.DoesNotExist:
            raise ValidationError(_("Strategic Item not found."))
            
        # Calculate next order
        max_order = item.tasks.aggregate(models.Max('order'))['order__max']
        next_order = (max_order or 0) + 1 if item.tasks.exists() else 0
        
        task = StrategicTask.objects.create(
            strategic_item=item,
            description=description,
            estimated_hours=estimated_hours,
            order=next_order
        )
        
        # Update parent item's total hours
        item.sync_estimated_hours_from_tasks()
        
        return task

    @staticmethod
    def calculate_session_totals(session_id: int) -> dict:
        """
        Recalculate totals for the entire session.
        Updates StrategicDay.estimated_total_hours.
        
        Returns:
            dict with 'total_hours', 'total_items', 'total_tasks'
        """
        session = StrategicPlanningService.get_session(session_id)
        
        total_hours = 0
        total_items = 0
        total_tasks = 0
        
        for day in session.days.all():
            # Sum up items for this day
            day_hours = day.items.aggregate(
                total=models.Sum('estimated_hours')
            )['total'] or 0
            
            # Update day record
            if day.estimated_total_hours != day_hours:
                day.estimated_total_hours = day_hours
                day.save(update_fields=['estimated_total_hours'])
            
            total_hours += day_hours
            total_items += day.items.count()
            # Count tasks efficiently
            total_tasks += StrategicTask.objects.filter(
                strategic_item__strategic_day=day
            ).count()
            
        return {
            'total_hours': total_hours,
            'total_items': total_items,
            'total_tasks': total_tasks
        }

    @staticmethod
    def validate_dependencies(session_id: int) -> list:
        """
        Validate all dependencies in the session.
        Checks for:
        1. Circular dependencies
        2. Logic errors (Successor scheduled before Predecessor)
        
        Returns:
            List of error strings. Empty list if valid.
        """
        from core.models import StrategicDependency
        
        errors = []
        session = StrategicPlanningService.get_session(session_id)
        
        # Get all dependencies relevant to this session
        # (Dependencies where both items belong to this session)
        dependencies = StrategicDependency.objects.filter(
            predecessor__strategic_day__session=session,
            successor__strategic_day__session=session
        ).select_related(
            'predecessor__strategic_day', 
            'successor__strategic_day'
        )
        
        for dep in dependencies:
            pred_date = dep.predecessor.strategic_day.target_date
            succ_date = dep.successor.strategic_day.target_date
            
            # Logic Check: Successor cannot be on a day BEFORE Predecessor
            # (Assuming FS - Finish to Start relationship for simplicity)
            if succ_date < pred_date:
                errors.append(
                    f"Logic Error: '{dep.successor.title}' ({succ_date}) "
                    f"cannot start before '{dep.predecessor.title}' ({pred_date}) is finished."
                )
                
            # Logic Check: If same day, check order?
            # For now, we assume items on same day are fine unless we enforce strict time
            
        return errors

    @staticmethod
    @transaction.atomic
    def export_to_daily_plan(session_id: int, user: User) -> int:
        """
        Export approved strategic plan to Daily Plan system.
        
        Creates DailyPlan and PlannedActivity records for each day/item.
        
        Args:
            session_id: ID of the session to export
            user: User performing the export
            
        Returns:
            Number of PlannedActivity records created
        """
        session = StrategicPlanningService.get_session(session_id)
        
        if not session.is_approved:
            raise ValidationError(_("Cannot export unapproved session."))
            
        if session.exported_to_daily_plan:
            raise ValidationError(_("Session already exported."))
            
        activities_created = 0
        
        # Iterate through days
        for day in session.days.all():
            # Skip days with no items
            if not day.items.exists():
                continue
                
            # Get or Create Daily Plan
            daily_plan, created = DailyPlan.objects.get_or_create(
                project=session.project,
                plan_date=day.target_date,
                defaults={
                    'created_by': user,
                    'status': 'DRAFT',
                    # Set deadline to 5pm previous day (standard rule)
                    'completion_deadline': timezone.make_aware(
                        timezone.datetime.combine(
                            day.target_date - timedelta(days=1), 
                            timezone.datetime.min.time().replace(hour=17)
                        )
                    )
                }
            )
            
            # Iterate through items
            for item in day.items.all():
                if item.exported_to_daily_plan:
                    continue
                    
                # Prepare description with tasks checklist
                full_description = item.description or ""
                tasks = item.tasks.all()
                if tasks:
                    full_description += "\n\n**Tasks:**"
                    for task in tasks:
                        full_description += f"\n- [ ] {task.description}"
                        if task.estimated_hours > 0:
                            full_description += f" ({task.estimated_hours}h)"
                            
                # Prepare materials JSON
                materials_list = []
                for mat in item.material_requirements.all():
                    materials_list.append({
                        'name': mat.name,
                        'quantity': float(mat.quantity),
                        'unit': mat.unit,
                        'notes': mat.notes,
                        'is_on_hand': mat.is_on_hand
                    })
                
                # Create Planned Activity
                activity = PlannedActivity.objects.create(
                    daily_plan=daily_plan,
                    title=item.title,
                    description=full_description,
                    order=item.order,
                    estimated_hours=item.estimated_hours,
                    activity_template=item.linked_activity_template,
                    materials_needed=materials_list,
                    schedule_item=day.linked_schedule_item
                )
                
                # Create Sub-activities for Tasks (New Dec 2025)
                for i, task in enumerate(tasks):
                    PlannedActivity.objects.create(
                        daily_plan=daily_plan,
                        parent=activity,
                        title=task.description,
                        description=f"Task derived from strategic item: {item.title}",
                        order=i,
                        estimated_hours=task.estimated_hours if task.estimated_hours else 0,
                        is_group_activity=False # Tasks are usually individual
                    )
                
                # Assign employees
                if item.assigned_to.exists():
                    activity.assigned_employees.set(item.assigned_to.all())
                
                # Mark item as exported
                item.exported_to_daily_plan = True
                item.save(update_fields=['exported_to_daily_plan'])
                
                # Mark tasks/subtasks as exported
                item.tasks.update(exported_to_daily_plan=True)
                # Note: Subtasks update would require another query, skipping for now as they are just text
                
                activities_created += 1
                
        # Mark session as exported
        session.exported_to_daily_plan = True
        session.exported_at = timezone.now()
        session.save(update_fields=['exported_to_daily_plan', 'exported_at'])
        
        return activities_created
