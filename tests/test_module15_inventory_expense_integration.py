import pytest
from decimal import Decimal
from django.utils import timezone

@pytest.mark.django_db
def test_receive_with_expense_links_and_cost():
    from core.models import InventoryItem, InventoryLocation, InventoryMovement, Expense, Project
    from django.contrib.auth import get_user_model
    User = get_user_model()

    project = Project.objects.create(name="Inv Proj", start_date=timezone.now().date())
    item = InventoryItem.objects.create(name="Thinner", category="OTRO", unit="lt")
    storage = InventoryLocation.objects.create(name="WH", is_storage=True)
    user = User.objects.create_user(username="uexp")

    exp = Expense.objects.create(
        project=project,
        project_name=project.name,
        amount=Decimal("100.00"),
        date=timezone.now().date(),
        category="MATERIALES",
        description="Purchase of thinner"
    )

    # Receive 10 units at total 100 => unit_cost 10
    m = InventoryMovement.objects.create(
        item=item,
        to_location=storage,
        movement_type="RECEIVE",
        quantity=Decimal("10"),
        unit_cost=Decimal("10.00"),
        expense=exp,
        created_by=user,
    )
    m.apply()

    item.refresh_from_db()
    assert item.average_cost == Decimal("10.00")
    assert m.expense_id == exp.id
