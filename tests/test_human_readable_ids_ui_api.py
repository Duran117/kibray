"""
Tests for Human-Readable IDs in UI and API
Tests that project_code, employee_key, and sku appear correctly in:
- API responses (serializers)
- Admin interface (list_display, search)
- Templates (if applicable)
"""
import pytest
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from core.models import Project, Employee, InventoryItem, Income, Expense, TimeEntry
from django.utils import timezone

User = get_user_model()


@pytest.mark.django_db
class TestProjectAPIWithHumanReadableIDs(TestCase):
    """Test that Project API includes project_code in responses"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.force_authenticate(user=self.user)

    def test_project_serializer_includes_project_code(self):
        """Test that ProjectSerializer includes project_code"""
        from core.api.serializers import ProjectSerializer
        
        project = Project.objects.create(
            name="Serializer Test Project",
            client="Test Client",
            start_date=timezone.now().date()
        )
        
        serializer = ProjectSerializer(project)
        data = serializer.data
        
        self.assertIn("project_code", data)
        self.assertEqual(data["project_code"], project.project_code)
        self.assertTrue(data["project_code"].startswith("PRJ-"))


@pytest.mark.django_db
class TestEmployeeAPIWithHumanReadableIDs(TestCase):
    """Test that Employee API includes employee_key in responses"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.force_authenticate(user=self.user)

    def test_employee_serializer_includes_employee_key(self):
        """Test that EmployeeSerializer includes employee_key"""
        from core.api.serializers import EmployeeSerializer
        
        employee = Employee.objects.create(
            first_name="John",
            last_name="Doe",
            social_security_number="123-45-6789",
            hourly_rate=Decimal("30.00")
        )
        
        serializer = EmployeeSerializer(employee)
        data = serializer.data
        
        self.assertIn("employee_key", data)
        self.assertEqual(data["employee_key"], employee.employee_key)
        self.assertTrue(data["employee_key"].startswith("EMP-"))

    def test_employee_key_is_readonly(self):
        """Test that employee_key cannot be modified via API"""
        from core.api.serializers import EmployeeSerializer
        
        employee = Employee.objects.create(
            first_name="Jane",
            last_name="Smith",
            social_security_number="987-65-4321",
            hourly_rate=Decimal("35.00")
        )
        
        original_key = employee.employee_key
        
        # Try to update employee_key (should be ignored)
        serializer = EmployeeSerializer(
            employee,
            data={
                "first_name": "Jane",
                "last_name": "Smith",
                "social_security_number": "987-65-4321",
                "hourly_rate": "35.00",
                "employee_key": "EMP-999"  # This should be ignored
            },
            partial=False
        )
        
        self.assertTrue(serializer.is_valid())
        updated_employee = serializer.save()
        
        # employee_key should remain unchanged
        self.assertEqual(updated_employee.employee_key, original_key)


@pytest.mark.django_db
class TestInventoryAPIWithHumanReadableIDs(TestCase):
    """Test that Inventory API includes sku in responses"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.force_authenticate(user=self.user)

    def test_inventory_serializer_includes_sku(self):
        """Test that InventoryItemSerializer includes sku"""
        from core.api.serializers import InventoryItemSerializer
        
        item = InventoryItem.objects.create(
            name="Test Paint",
            category="PINTURA",
            unit="Galón"
        )
        
        serializer = InventoryItemSerializer(item)
        data = serializer.data
        
        self.assertIn("sku", data)
        self.assertEqual(data["sku"], item.sku)
        self.assertTrue(data["sku"].startswith("PAI-"))

    def test_sku_appears_first_in_fields(self):
        """Test that sku is positioned prominently (first after id)"""
        from core.api.serializers import InventoryItemSerializer
        
        item = InventoryItem.objects.create(
            name="Test Material",
            category="MATERIAL",
            unit="m²"
        )
        
        serializer = InventoryItemSerializer(item)
        fields = list(serializer.data.keys())
        
        # SKU should be early in the field list (second after id)
        self.assertIn("sku", fields[:3])


@pytest.mark.django_db
class TestIncomeExpenseAPIWithProjectCode(TestCase):
    """Test that Income/Expense APIs include project_code"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.force_authenticate(user=self.user)
        
        self.project = Project.objects.create(
            name="Financial Test Project",
            client="Test Client",
            start_date=timezone.now().date()
        )

    def test_income_serializer_includes_project_code(self):
        """Test that IncomeSerializer includes project_code"""
        from core.api.serializers import IncomeSerializer
        
        income = Income.objects.create(
            project=self.project,
            amount=Decimal("5000.00"),
            date=timezone.now().date(),
            payment_method="CHECK"
        )
        
        serializer = IncomeSerializer(income)
        data = serializer.data
        
        self.assertIn("project_code", data)
        self.assertEqual(data["project_code"], self.project.project_code)

    def test_expense_serializer_includes_project_code(self):
        """Test that ExpenseSerializer includes project_code"""
        from core.api.serializers import ExpenseSerializer
        
        expense = Expense.objects.create(
            project=self.project,
            amount=Decimal("1500.00"),
            date=timezone.now().date(),
            category="LABOR"
        )
        
        serializer = ExpenseSerializer(expense)
        data = serializer.data
        
        self.assertIn("project_code", data)
        self.assertEqual(data["project_code"], self.project.project_code)


@pytest.mark.django_db
class TestTimeEntryAPIWithHumanReadableIDs(TestCase):
    """Test that TimeEntry API includes both employee_key and project_code"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.force_authenticate(user=self.user)
        
        self.project = Project.objects.create(
            name="Time Entry Project",
            client="Test Client",
            start_date=timezone.now().date()
        )
        
        self.employee = Employee.objects.create(
            first_name="Worker",
            last_name="Person",
            social_security_number="111-22-3333",
            hourly_rate=Decimal("25.00")
        )

    def test_timeentry_serializer_includes_both_codes(self):
        """Test that TimeEntrySerializer includes both employee_key and project_code"""
        from core.api.serializers import TimeEntrySerializer
        
        time_entry = TimeEntry.objects.create(
            employee=self.employee,
            project=self.project,
            date=timezone.now().date(),
            start_time=timezone.now().time(),
            end_time=timezone.now().time()
        )
        
        serializer = TimeEntrySerializer(time_entry)
        data = serializer.data
        
        self.assertIn("employee_key", data)
        self.assertIn("project_code", data)
        self.assertEqual(data["employee_key"], self.employee.employee_key)
        self.assertEqual(data["project_code"], self.project.project_code)


@pytest.mark.django_db
class TestAdminSearchWithHumanReadableIDs(TestCase):
    """Test that admin search works with human-readable IDs"""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="admin123",
            email="admin@test.com"
        )
        self.client.login(username="admin", password="admin123")

    def test_project_admin_search_by_code(self):
        """Test that project admin can search by project_code"""
        project = Project.objects.create(
            name="Searchable Project",
            client="Test Client",
            start_date=timezone.now().date()
        )
        
        url = reverse("admin:core_project_changelist")
        response = self.client.get(url, {"q": project.project_code})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, project.project_code)

    def test_employee_admin_search_by_key(self):
        """Test that employee admin can search by employee_key"""
        employee = Employee.objects.create(
            first_name="Searchable",
            last_name="Employee",
            social_security_number="555-55-5555",
            hourly_rate=Decimal("28.00")
        )
        
        url = reverse("admin:core_employee_changelist")
        response = self.client.get(url, {"q": employee.employee_key})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, employee.employee_key)

    def test_inventory_admin_search_by_sku(self):
        """Test that inventory admin can search by sku"""
        item = InventoryItem.objects.create(
            name="Searchable Item",
            category="HERRAMIENTA",
            unit="pz"
        )
        
        url = reverse("admin:core_inventoryitem_changelist")
        response = self.client.get(url, {"q": item.sku})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, item.sku)


@pytest.mark.django_db
class TestAdminDisplayFieldsWithHumanReadableIDs(TestCase):
    """Test that admin list views display human-readable IDs prominently"""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="admin123",
            email="admin@test.com"
        )
        self.client.login(username="admin", password="admin123")

    def test_project_admin_displays_project_code(self):
        """Test that project admin list displays project_code"""
        project = Project.objects.create(
            name="Display Test Project",
            client="Test Client",
            start_date=timezone.now().date()
        )
        
        url = reverse("admin:core_project_changelist")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, project.project_code)

    def test_employee_admin_displays_employee_key(self):
        """Test that employee admin list displays employee_key"""
        employee = Employee.objects.create(
            first_name="Display",
            last_name="Test",
            social_security_number="777-77-7777",
            hourly_rate=Decimal("32.00")
        )
        
        url = reverse("admin:core_employee_changelist")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, employee.employee_key)

    def test_inventory_admin_displays_sku(self):
        """Test that inventory admin list displays sku"""
        item = InventoryItem.objects.create(
            name="Display Test Item",
            category="OTRO",
            unit="kg"
        )
        
        url = reverse("admin:core_inventoryitem_changelist")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, item.sku)
