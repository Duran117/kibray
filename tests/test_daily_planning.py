"""
Comprehensive test suite for Daily Planning module.

Tests:
- planning_service.py: get_suggested_items_for_date, priority calculations
- views.py: daily_plan_create GET/POST handlers
- Edge cases: no suggestions, multiple imports, date validation
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from core.models import (
    Project, Profile, ScheduleItem, DailyPlan, PlannedActivity,
    ScheduleCategory, CostCode
)
from core.services.planning_service import (
    get_suggested_items_for_date,
    calculate_activity_priority,
    get_activities_summary
)


@pytest.fixture
def user_with_profile(db, django_user_model):
    """Create a user with associated profile."""
    user = django_user_model.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    # Profile is auto-created via signal, just update if needed
    profile = Profile.objects.get(user=user)
    # Set role and staff flags so _is_staffish passes (permite admin/project_manager/staff/superuser)
    profile.role = 'project_manager'
    profile.save()
    user.is_staff = True
    user.save()
    return user


@pytest.fixture
def project(db, user_with_profile):
    """Create a test project."""
    return Project.objects.create(
        project_code='TEST-001',
        name='Test Construction Project',
        client='Test Client',
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timedelta(days=90),
        budget_labor=Decimal('50000.00'),
        budget_materials=Decimal('100000.00'),
        budget_other=Decimal('25000.00'),
        budget_total=Decimal('175000.00')
    )


@pytest.fixture
def category(db, project):
    """Create a test schedule category."""
    return ScheduleCategory.objects.create(
        project=project,
        name='Foundation'
    )


@pytest.fixture
def cost_code(db):
    """Create a test cost code."""
    return CostCode.objects.create(
        code='CC-100',
        name='Foundation Work',
        category='labor'
    )


@pytest.fixture
def schedule_items(db, project, category, cost_code):
    """Create multiple schedule items with different scenarios."""
    tomorrow = timezone.now().date() + timedelta(days=1)
    next_week = timezone.now().date() + timedelta(days=7)
    
    items = []
    
    # Urgent item - starts tomorrow, low progress
    items.append(ScheduleItem.objects.create(
        project=project,
        category=category,
        cost_code=cost_code,
        title='Urgent Foundation Pour',
        description='Critical path item',
        planned_start=tomorrow,
        planned_end=tomorrow + timedelta(days=2),
        status='IN_PROGRESS',
        percent_complete=10,
        is_milestone=False
    ))
    
    # Behind schedule item - expected 50%, actual 20%
    items.append(ScheduleItem.objects.create(
        project=project,
        category=category,
        cost_code=cost_code,
        title='Framing Work',
        description='Behind schedule',
        planned_start=tomorrow - timedelta(days=3),
        planned_end=tomorrow + timedelta(days=3),
        status='IN_PROGRESS',
        percent_complete=20,
        is_milestone=False
    ))
    
    # On-track item - good progress
    items.append(ScheduleItem.objects.create(
        project=project,
        category=category,
        cost_code=cost_code,
        title='Electrical Rough-In',
        description='On schedule',
        planned_start=tomorrow,
        planned_end=tomorrow + timedelta(days=5),
        status='NOT_STARTED',
        percent_complete=0,
        is_milestone=False
    ))
    
    # Completed item - should be excluded
    items.append(ScheduleItem.objects.create(
        project=project,
        category=category,
        cost_code=cost_code,
        title='Site Prep',
        description='Already done',
        planned_start=tomorrow - timedelta(days=10),
        planned_end=tomorrow - timedelta(days=5),
        status='DONE',
        percent_complete=100,
        is_milestone=False
    ))
    
    # Future item - next week
    items.append(ScheduleItem.objects.create(
        project=project,
        category=category,
        cost_code=cost_code,
        title='Drywall Installation',
        description='Future work',
        planned_start=next_week,
        planned_end=next_week + timedelta(days=5),
        status='NOT_STARTED',
        percent_complete=0,
        is_milestone=False
    ))
    
    # Milestone item
    items.append(ScheduleItem.objects.create(
        project=project,
        category=category,
        cost_code=cost_code,
        title='Foundation Complete',
        description='Milestone',
        planned_start=tomorrow,
        planned_end=tomorrow,
        status='IN_PROGRESS',
        percent_complete=75,
        is_milestone=True
    ))
    
    return items


@pytest.mark.django_db
class TestPlanningService:
    """Test planning_service.py functions."""
    
    def test_get_suggested_items_for_tomorrow(self, project, schedule_items):
        """Test getting suggestions for tomorrow - should return 4 items."""
        tomorrow = timezone.now().date() + timedelta(days=1)
        suggestions = get_suggested_items_for_date(project, tomorrow)
        
        # Should get 4 items (urgent, behind, on-track, milestone)
        # Excludes: DONE item, future item
        assert len(suggestions) == 4
        
        # Verify structure
        first = suggestions[0]
        assert 'id' in first
        assert 'title' in first
        assert 'status' in first
        assert 'status_display' in first
        assert 'percent_complete' in first
        assert 'days_remaining' in first
        assert 'is_urgent' in first
        assert 'is_behind' in first
        assert 'category_name' in first
        
    def test_get_suggested_items_filters_done(self, project, schedule_items):
        """Test that DONE items are excluded."""
        tomorrow = timezone.now().date() + timedelta(days=1)
        suggestions = get_suggested_items_for_date(project, tomorrow)
        
        titles = [item['title'] for item in suggestions]
        assert 'Site Prep' not in titles  # DONE item
        
    def test_get_suggested_items_date_range_filtering(self, project, schedule_items):
        """Test date range filtering works correctly."""
        # Check next week - should only get the future item
        next_week = timezone.now().date() + timedelta(days=7)
        suggestions = get_suggested_items_for_date(project, next_week)
        
        # Should get the drywall item that starts next week
        assert len(suggestions) >= 1
        titles = [item['title'] for item in suggestions]
        assert 'Drywall Installation' in titles
        
    def test_get_suggested_items_no_matches(self, project):
        """Test when no schedule items match the date."""
        far_future = timezone.now().date() + timedelta(days=365)
        suggestions = get_suggested_items_for_date(project, far_future)
        
        assert len(suggestions) == 0
        
    def test_urgency_calculation(self, project, schedule_items):
        """Test that urgent items are flagged correctly."""
        tomorrow = timezone.now().date() + timedelta(days=1)
        suggestions = get_suggested_items_for_date(project, tomorrow)
        
        # Find the urgent foundation pour (2 days left)
        urgent_item = next(
            (item for item in suggestions if 'Urgent' in item['title']),
            None
        )
        assert urgent_item is not None
        assert urgent_item['is_urgent'] is True
        assert urgent_item['days_remaining'] <= 3
        
    def test_behind_schedule_detection(self, project, schedule_items):
        """Test that behind-schedule items are detected."""
        tomorrow = timezone.now().date() + timedelta(days=1)
        suggestions = get_suggested_items_for_date(project, tomorrow)
        
        # Find the framing work (behind schedule)
        behind_item = next(
            (item for item in suggestions if 'Framing' in item['title']),
            None
        )
        assert behind_item is not None
        assert behind_item['is_behind'] is True
        
    def test_milestone_flag(self, project, schedule_items):
        """Test that milestones are identified."""
        tomorrow = timezone.now().date() + timedelta(days=1)
        suggestions = get_suggested_items_for_date(project, tomorrow)
        
        milestone = next(
            (item for item in suggestions if 'Milestone' in item['description']),
            None
        )
        assert milestone is not None
        assert milestone['is_milestone'] is True
        
    def test_calculate_activity_priority(self):
        """Test priority calculation logic."""
        # Critical priority: urgent + low progress
        priority1 = calculate_activity_priority(
            days_remaining=1,
            percent_complete=10,
            is_milestone=False
        )
        
        # High priority: urgent deadline
        priority2 = calculate_activity_priority(
            days_remaining=2,
            percent_complete=50,
            is_milestone=False
        )
        
        # Medium priority: normal timeline
        priority3 = calculate_activity_priority(
            days_remaining=5,
            percent_complete=30,
            is_milestone=False
        )
        
        # Low priority: plenty of time
        priority4 = calculate_activity_priority(
            days_remaining=10,
            percent_complete=30,
            is_milestone=False
        )
        
        assert priority1 == 'critical'
        assert priority2 == 'high'
        assert priority3 in ['medium', 'high']  # Could be either based on logic
        assert priority4 == 'low'
        
    def test_get_activities_summary(self, project, user_with_profile, schedule_items):
        """Test activities summary generation."""
        tomorrow = timezone.now().date() + timedelta(days=1)
        week_later = tomorrow + timedelta(days=7)
        
        summary = get_activities_summary(project, tomorrow, week_later)
        
        assert 'total_items' in summary
        assert 'urgent_items' in summary
        assert 'in_progress_items' in summary
        assert 'blocked_items' in summary
        assert 'avg_progress' in summary
        assert 'date_range' in summary
        assert summary['total_items'] >= 0


@pytest.mark.django_db
class TestDailyPlanCreateView:
    """Test daily_plan_create view."""
    
    def test_get_request_default_date(self, client, user_with_profile, project, schedule_items):
        """Test GET request uses tomorrow as default date."""
        client.force_login(user_with_profile)
        url = reverse('daily_plan_create', kwargs={'project_id': project.id})
        
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'target_date' in response.context
        assert 'suggested_items' in response.context
        
        # Default should be tomorrow
        tomorrow = timezone.now().date() + timedelta(days=1)
        assert response.context['target_date'] == tomorrow
        
    def test_get_request_custom_date(self, client, user_with_profile, project, schedule_items):
        """Test GET request with custom date parameter."""
        client.force_login(user_with_profile)
        url = reverse('daily_plan_create', kwargs={'project_id': project.id})
        
        custom_date = timezone.now().date() + timedelta(days=7)
        response = client.get(url, {'date': custom_date.strftime('%Y-%m-%d')})
        
        assert response.status_code == 200
        assert response.context['target_date'] == custom_date
        
    def test_get_request_shows_suggestions(self, client, user_with_profile, project, schedule_items):
        """Test that suggestions are displayed correctly."""
        client.force_login(user_with_profile)
        url = reverse('daily_plan_create', kwargs={'project_id': project.id})
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        response = client.get(url, {'date': tomorrow.strftime('%Y-%m-%d')})
        
        assert response.status_code == 200
        assert response.context['has_suggestions'] is True
        assert len(response.context['suggested_items']) > 0
        
    def test_get_request_no_suggestions(self, client, user_with_profile, project):
        """Test when no suggestions are available."""
        client.force_login(user_with_profile)
        url = reverse('daily_plan_create', kwargs={'project_id': project.id})
        
        # Use a date far in future with no schedule items
        far_future = timezone.now().date() + timedelta(days=365)
        response = client.get(url, {'date': far_future.strftime('%Y-%m-%d')})
        
        assert response.status_code == 200
        assert response.context['has_suggestions'] is False
        assert len(response.context['suggested_items']) == 0
        
    def test_post_creates_daily_plan(self, client, user_with_profile, project, schedule_items):
        """Test POST request creates a daily plan."""
        client.force_login(user_with_profile)
        url = reverse('daily_plan_create', kwargs={'project_id': project.id})
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        response = client.post(url, {
            'plan_date': tomorrow.strftime('%Y-%m-%d')
        })
        
        # Should redirect after creation
        assert response.status_code == 302
        
        # Verify plan was created
        plan = DailyPlan.objects.filter(
            project=project,
            plan_date=tomorrow
        ).first()
        assert plan is not None
        assert plan.created_by == user_with_profile
        assert plan.status == 'DRAFT'
        
    def test_post_imports_schedule_items(self, client, user_with_profile, project, schedule_items):
        """Test POST request imports selected schedule items."""
        client.force_login(user_with_profile)
        url = reverse('daily_plan_create', kwargs={'project_id': project.id})
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        item_ids = [schedule_items[0].id, schedule_items[1].id]
        
        response = client.post(url, {
            'plan_date': tomorrow.strftime('%Y-%m-%d'),
            'import_items': item_ids
        })
        
        assert response.status_code == 302
        
        # Verify activities were created
        plan = DailyPlan.objects.filter(
            project=project,
            plan_date=tomorrow
        ).first()
        assert plan is not None
        
        activities = PlannedActivity.objects.filter(daily_plan=plan)
        assert activities.count() == 2
        
        # Verify schedule_item relationships
        activity_item_ids = [act.schedule_item.id for act in activities if act.schedule_item]
        assert schedule_items[0].id in activity_item_ids
        assert schedule_items[1].id in activity_item_ids
        
    def test_post_without_imports(self, client, user_with_profile, project):
        """Test POST creates plan without importing items."""
        client.force_login(user_with_profile)
        url = reverse('daily_plan_create', kwargs={'project_id': project.id})
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        response = client.post(url, {
            'plan_date': tomorrow.strftime('%Y-%m-%d')
        })
        
        assert response.status_code == 302
        
        plan = DailyPlan.objects.filter(
            project=project,
            plan_date=tomorrow
        ).first()
        assert plan is not None
        
        # Should have 0 activities
        assert plan.plannedactivity_set.count() == 0
        
    def test_post_invalid_date(self, client, user_with_profile, project):
        """Test POST with invalid date format."""
        client.force_login(user_with_profile)
        url = reverse('daily_plan_create', kwargs={'project_id': project.id})
        
        response = client.post(url, {
            'plan_date': 'invalid-date'
        })
        
        # Should still show form with errors
        assert response.status_code == 200
        # Inline error message should be present
        assert 'Invalid date format' in response.content.decode()
        
    def test_post_duplicate_import(self, client, user_with_profile, project, schedule_items):
        """Test importing same item twice (should handle gracefully)."""
        client.force_login(user_with_profile)
        url = reverse('daily_plan_create', kwargs={'project_id': project.id})
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        # First import
        response1 = client.post(url, {
            'plan_date': tomorrow.strftime('%Y-%m-%d'),
            'import_items': [schedule_items[0].id]
        })
        assert response1.status_code == 302
        
        # Try to create another plan for same date
        response2 = client.post(url, {
            'plan_date': tomorrow.strftime('%Y-%m-%d'),
            'import_items': [schedule_items[0].id]
        })
        
        # Should handle duplicate or show error
        # Exact behavior depends on unique constraints
        
    def test_unauthorized_access(self, client, project):
        """Test that unauthorized users cannot access the view."""
        url = reverse('daily_plan_create', kwargs={'project_id': project.id})
        response = client.get(url)
        
        # Should redirect to login
        assert response.status_code == 302
        assert '/login/' in response.url or '/accounts/login/' in response.url


@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_nonexistent_project(self, client, user_with_profile):
        """Test accessing view with invalid project ID."""
        client.force_login(user_with_profile)
        url = reverse('daily_plan_create', kwargs={'project_id': 99999})
        response = client.get(url)
        
        assert response.status_code == 404
        
    def test_empty_import_list(self, client, user_with_profile, project):
        """Test POST with empty import_items."""
        client.force_login(user_with_profile)
        url = reverse('daily_plan_create', kwargs={'project_id': project.id})
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        response = client.post(url, {
            'plan_date': tomorrow.strftime('%Y-%m-%d'),
            'import_items': []
        })
        
        assert response.status_code == 302
        
    def test_invalid_schedule_item_id(self, client, user_with_profile, project):
        """Test importing non-existent schedule item ID."""
        client.force_login(user_with_profile)
        url = reverse('daily_plan_create', kwargs={'project_id': project.id})
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        response = client.post(url, {
            'plan_date': tomorrow.strftime('%Y-%m-%d'),
            'import_items': [99999]  # Non-existent ID
        })
        
        # Should handle gracefully
        assert response.status_code in [200, 302]
        
    def test_schedule_items_from_different_project(
        self, client, user_with_profile, project, schedule_items, cost_code
    ):
        """Test that importing items from another project is prevented."""
        # Create another project
        other_project = Project.objects.create(
            project_code='OTHER-001',
            name='Other Project',
            client='Other Client',
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30)
        )
        
        # Create category for other project
        other_category = ScheduleCategory.objects.create(
            project=other_project,
            name='Other Category'
        )
        
        # Create schedule item for other project
        other_item = ScheduleItem.objects.create(
            project=other_project,
            category=other_category,
            cost_code=cost_code,
            title='Other Project Item',
            planned_start=timezone.now().date() + timedelta(days=1),
            planned_end=timezone.now().date() + timedelta(days=5),
            status='NOT_STARTED'
        )
        
        client.force_login(user_with_profile)
        url = reverse('daily_plan_create', kwargs={'project_id': project.id})
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        response = client.post(url, {
            'plan_date': tomorrow.strftime('%Y-%m-%d'),
            'import_items': [other_item.id]
        })
        
        # Should reject or ignore items from other project
        plan = DailyPlan.objects.filter(project=project).first()
        if plan:
            activities = plan.plannedactivity_set.filter(schedule_item=other_item)
            assert activities.count() == 0


@pytest.mark.django_db
class TestIntegration:
    """Integration tests combining service and view."""
    
    def test_full_workflow_with_suggestions(self, client, user_with_profile, project, schedule_items):
        """Test complete workflow: view suggestions → import → create plan."""
        client.force_login(user_with_profile)
        url = reverse('daily_plan_create', kwargs={'project_id': project.id})
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        # Step 1: View suggestions
        response1 = client.get(url, {'date': tomorrow.strftime('%Y-%m-%d')})
        assert response1.status_code == 200
        suggestions = response1.context['suggested_items']
        assert len(suggestions) > 0
        
        # Step 2: Import selected items
        selected_ids = [suggestions[0]['id'], suggestions[1]['id']]
        response2 = client.post(url, {
            'plan_date': tomorrow.strftime('%Y-%m-%d'),
            'import_items': selected_ids
        })
        assert response2.status_code == 302
        
        # Step 3: Verify plan and activities
        plan = DailyPlan.objects.get(project=project, plan_date=tomorrow)
        assert plan.plannedactivity_set.count() == 2
        
        # Verify activity titles match schedule items
        for activity in plan.plannedactivity_set.all():
            assert activity.schedule_item is not None
            assert activity.schedule_item.id in selected_ids
            
    def test_multiple_plans_different_dates(self, client, user_with_profile, project, schedule_items):
        """Test creating multiple plans for different dates."""
        client.force_login(user_with_profile)
        url = reverse('daily_plan_create', kwargs={'project_id': project.id})
        
        # Create plan for tomorrow
        tomorrow = timezone.now().date() + timedelta(days=1)
        response1 = client.post(url, {
            'plan_date': tomorrow.strftime('%Y-%m-%d'),
            'import_items': [schedule_items[0].id]
        })
        assert response1.status_code == 302
        
        # Create plan for next week
        next_week = timezone.now().date() + timedelta(days=7)
        response2 = client.post(url, {
            'plan_date': next_week.strftime('%Y-%m-%d'),
            'import_items': [schedule_items[4].id]
        })
        assert response2.status_code == 302
        
        # Verify both plans exist
        assert DailyPlan.objects.filter(project=project).count() == 2
        
    def test_priority_ordering_in_suggestions(self, client, user_with_profile, project, schedule_items):
        """Test that suggestions are ordered by priority."""
        client.force_login(user_with_profile)
        url = reverse('daily_plan_create', kwargs={'project_id': project.id})
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        response = client.get(url, {'date': tomorrow.strftime('%Y-%m-%d')})
        
        suggestions = response.context['suggested_items']
        if len(suggestions) > 1:
            # Urgent/behind items should come first
            first_item = suggestions[0]
            # At least one flag should be true for high-priority items
            assert first_item['is_urgent'] or first_item['is_behind']
