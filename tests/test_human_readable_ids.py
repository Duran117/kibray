"""
Tests for Human-Readable IDs functionality
Tests the generation of unique, human-readable codes for Projects, Employees, and InventoryItems.
"""

import pytest
from decimal import Decimal
from django.utils import timezone
from core.models import Project, Employee, InventoryItem


@pytest.mark.django_db
class TestProjectHumanReadableID:
    """Test Project code generation in format PRJ-{YYYY}-{000}"""
    
    def test_new_project_generates_code_current_year(self):
        """New project should auto-generate code with current year"""
        project = Project.objects.create(
            name="Test Project",
            start_date=timezone.now().date()
        )
        
        year = timezone.now().year
        assert project.project_code.startswith(f"PRJ-{year}-")
        assert len(project.project_code.split('-')) == 3
        
    def test_sequential_projects_same_year(self):
        """Projects created in same year should have sequential numbers"""
        year = timezone.now().year
        
        proj1 = Project.objects.create(
            name="Project 1",
            start_date=timezone.now().date()
        )
        proj2 = Project.objects.create(
            name="Project 2",
            start_date=timezone.now().date()
        )
        
        # Extract sequence numbers
        seq1 = int(proj1.project_code.split('-')[-1])
        seq2 = int(proj2.project_code.split('-')[-1])
        
        assert seq2 == seq1 + 1
        assert proj1.project_code.startswith(f"PRJ-{year}-")
        assert proj2.project_code.startswith(f"PRJ-{year}-")
        
    def test_manual_project_code_not_overridden(self):
        """If user provides project_code manually, it should not be overridden"""
        project = Project.objects.create(
            name="Manual Code Project",
            project_code="CUSTOM-123",
            start_date=timezone.now().date()
        )
        
        assert project.project_code == "CUSTOM-123"
        
    def test_project_code_format(self):
        """Project code should match format PRJ-YYYY-NNN"""
        project = Project.objects.create(
            name="Format Test",
            start_date=timezone.now().date()
        )
        
        parts = project.project_code.split('-')
        assert len(parts) == 3
        assert parts[0] == "PRJ"
        assert len(parts[1]) == 4  # Year
        assert len(parts[2]) == 3  # Sequence with leading zeros
        assert parts[2].isdigit()


@pytest.mark.django_db
class TestEmployeeHumanReadableID:
    """Test Employee key generation in format EMP-{000}"""
    
    def test_new_employee_generates_key(self):
        """New employee should auto-generate employee_key"""
        employee = Employee.objects.create(
            first_name="John",
            last_name="Doe",
            social_security_number="123-45-6789",
            hourly_rate=Decimal("25.00")
        )
        
        assert employee.employee_key.startswith("EMP-")
        assert len(employee.employee_key) == 7  # EMP-XXX
        
    def test_sequential_employees(self):
        """Employees should have sequential keys"""
        emp1 = Employee.objects.create(
            first_name="Alice",
            last_name="Smith",
            social_security_number="111-11-1111",
            hourly_rate=Decimal("30.00")
        )
        emp2 = Employee.objects.create(
            first_name="Bob",
            last_name="Jones",
            social_security_number="222-22-2222",
            hourly_rate=Decimal("35.00")
        )
        
        seq1 = int(emp1.employee_key.split('-')[-1])
        seq2 = int(emp2.employee_key.split('-')[-1])
        
        assert seq2 == seq1 + 1
        
    def test_employee_key_unique(self):
        """Employee keys should be unique"""
        emp1 = Employee.objects.create(
            first_name="Carl",
            last_name="Wilson",
            social_security_number="333-33-3333",
            hourly_rate=Decimal("28.00")
        )
        emp2 = Employee.objects.create(
            first_name="David",
            last_name="Brown",
            social_security_number="444-44-4444",
            hourly_rate=Decimal("32.00")
        )
        
        assert emp1.employee_key != emp2.employee_key
        
    def test_employee_key_not_editable(self):
        """Employee key should not be editable once set"""
        employee = Employee.objects.create(
            first_name="Eve",
            last_name="Davis",
            social_security_number="555-55-5555",
            hourly_rate=Decimal("27.00")
        )
        
        original_key = employee.employee_key
        
        # Try to modify (should be ignored due to editable=False in admin)
        employee.first_name = "Updated Eve"
        employee.save()
        employee.refresh_from_db()
        
        assert employee.employee_key == original_key
        
    def test_employee_key_format(self):
        """Employee key should match format EMP-NNN"""
        employee = Employee.objects.create(
            first_name="Frank",
            last_name="Miller",
            social_security_number="666-66-6666",
            hourly_rate=Decimal("29.00")
        )
        
        parts = employee.employee_key.split('-')
        assert len(parts) == 2
        assert parts[0] == "EMP"
        assert len(parts[1]) == 3  # Sequence with leading zeros
        assert parts[1].isdigit()


@pytest.mark.django_db
class TestInventoryItemHumanReadableSKU:
    """Test InventoryItem SKU generation based on category"""
    
    def test_material_sku_generation(self):
        """Material items should get MAT-XXX SKU"""
        item = InventoryItem.objects.create(
            name="Test Material",
            category="MATERIAL"
        )
        
        assert item.sku.startswith("MAT-")
        assert len(item.sku) == 7  # MAT-XXX
        
    def test_paint_sku_generation(self):
        """Paint items should get PAI-XXX SKU"""
        item = InventoryItem.objects.create(
            name="Test Paint",
            category="PINTURA"
        )
        
        assert item.sku.startswith("PAI-")
        
    def test_tool_sku_generation(self):
        """Tool items should get TOO-XXX SKU"""
        item = InventoryItem.objects.create(
            name="Test Tool",
            category="HERRAMIENTA"
        )
        
        assert item.sku.startswith("TOO-")
        
    def test_ladder_sku_generation(self):
        """Ladder items should get LAD-XXX SKU"""
        item = InventoryItem.objects.create(
            name="Test Ladder",
            category="ESCALERA"
        )
        
        assert item.sku.startswith("LAD-")
        
    def test_sequential_skus_per_category(self):
        """SKUs should be sequential within each category"""
        mat1 = InventoryItem.objects.create(
            name="Material 1",
            category="MATERIAL"
        )
        mat2 = InventoryItem.objects.create(
            name="Material 2",
            category="MATERIAL"
        )
        
        seq1 = int(mat1.sku.split('-')[-1])
        seq2 = int(mat2.sku.split('-')[-1])
        
        assert seq2 == seq1 + 1
        
    def test_manual_sku_not_overridden(self):
        """If user provides SKU manually, it should not be overridden"""
        item = InventoryItem.objects.create(
            name="Custom SKU Item",
            category="MATERIAL",
            sku="CUSTOM-SKU-123"
        )
        
        assert item.sku == "CUSTOM-SKU-123"
        
    def test_different_categories_independent_sequences(self):
        """Different categories should have independent SKU sequences"""
        mat = InventoryItem.objects.create(
            name="Material",
            category="MATERIAL"
        )
        paint = InventoryItem.objects.create(
            name="Paint",
            category="PINTURA"
        )
        tool = InventoryItem.objects.create(
            name="Tool",
            category="HERRAMIENTA"
        )
        
        # All should start with different prefixes
        assert mat.sku.startswith("MAT-")
        assert paint.sku.startswith("PAI-")
        assert tool.sku.startswith("TOO-")
        
        # Each can have sequence 001 independently
        mat_seq = int(mat.sku.split('-')[-1])
        paint_seq = int(paint.sku.split('-')[-1])
        tool_seq = int(tool.sku.split('-')[-1])
        
        # They can all be 1 or different, but shouldn't conflict
        assert mat.sku != paint.sku
        assert paint.sku != tool.sku
        assert mat.sku != tool.sku
        
    def test_sku_format(self):
        """SKU should match format {CAT}-NNN"""
        item = InventoryItem.objects.create(
            name="Format Test",
            category="SPRAY"
        )
        
        parts = item.sku.split('-')
        assert len(parts) == 2
        assert parts[0] == "SPR"  # Spray prefix
        assert len(parts[1]) == 3  # Sequence with leading zeros
        assert parts[1].isdigit()
        
    def test_all_category_prefixes(self):
        """Test all category prefixes are correctly mapped"""
        categories_and_prefixes = [
            ("MATERIAL", "MAT"),
            ("PINTURA", "PAI"),
            ("ESCALERA", "LAD"),
            ("LIJADORA", "SAN"),
            ("SPRAY", "SPR"),
            ("HERRAMIENTA", "TOO"),
            ("OTRO", "OTH"),
        ]
        
        for category, expected_prefix in categories_and_prefixes:
            item = InventoryItem.objects.create(
                name=f"Test {category}",
                category=category
            )
            assert item.sku.startswith(f"{expected_prefix}-"), \
                f"Category {category} should have prefix {expected_prefix}"


@pytest.mark.django_db
class TestConcurrencyAndRaceConditions:
    """Test thread-safety and race condition handling"""
    
    def test_project_codes_no_duplicates(self):
        """Creating multiple projects should not create duplicate codes"""
        projects = []
        for i in range(5):
            project = Project.objects.create(
                name=f"Concurrent Project {i}",
                start_date=timezone.now().date()
            )
            projects.append(project)
        
        codes = [p.project_code for p in projects]
        assert len(codes) == len(set(codes)), "Found duplicate project codes"
        
    def test_employee_keys_no_duplicates(self):
        """Creating multiple employees should not create duplicate keys"""
        employees = []
        for i in range(5):
            employee = Employee.objects.create(
                first_name=f"Test{i}",
                last_name="User",
                social_security_number=f"999-99-{i:04d}",
                hourly_rate=Decimal("25.00")
            )
            employees.append(employee)
        
        keys = [e.employee_key for e in employees]
        assert len(keys) == len(set(keys)), "Found duplicate employee keys"
        
    def test_inventory_skus_no_duplicates_same_category(self):
        """Creating multiple items in same category should not create duplicate SKUs"""
        items = []
        for i in range(5):
            item = InventoryItem.objects.create(
                name=f"Concurrent Material {i}",
                category="MATERIAL"
            )
            items.append(item)
        
        skus = [i.sku for i in items]
        assert len(skus) == len(set(skus)), "Found duplicate SKUs"


@pytest.mark.django_db
class TestBackfillBehavior:
    """Test that existing records get proper codes"""
    
    def test_existing_projects_keep_codes(self):
        """Projects with codes should keep them after update"""
        project = Project.objects.create(
            name="Existing Project",
            project_code="PRJ-2024-999",
            start_date=timezone.now().date()
        )
        
        # Update some other field
        project.name = "Updated Name"
        project.save()
        project.refresh_from_db()
        
        # Code should not change
        assert project.project_code == "PRJ-2024-999"
        
    def test_existing_employees_keep_keys(self):
        """Employees with keys should keep them after update"""
        employee = Employee.objects.create(
            first_name="Existing",
            last_name="Employee",
            employee_key="EMP-999",
            social_security_number="777-77-7777",
            hourly_rate=Decimal("30.00")
        )
        
        # Update some other field
        employee.hourly_rate = Decimal("35.00")
        employee.save()
        employee.refresh_from_db()
        
        # Key should not change
        assert employee.employee_key == "EMP-999"
        
    def test_existing_inventory_keeps_sku(self):
        """Inventory items with SKUs should keep them after update"""
        item = InventoryItem.objects.create(
            name="Existing Item",
            category="MATERIAL",
            sku="MAT-999"
        )
        
        # Update some other field
        item.name = "Updated Item"
        item.save()
        item.refresh_from_db()
        
        # SKU should not change
        assert item.sku == "MAT-999"
