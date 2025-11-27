from decimal import Decimal

import pytest
from django.utils import timezone


@pytest.mark.django_db
class TestInventoryMovements:
    def setup_method(self):
        from core.models import InventoryItem, InventoryLocation

        self.item = InventoryItem.objects.create(
            name="Latex Paint", category="PINTURA", unit="gal", low_stock_threshold=Decimal("5")
        )
        self.storage = InventoryLocation.objects.create(name="Main Warehouse", is_storage=True)
        self.site = InventoryLocation.objects.create(name="Project A", project=None, is_storage=False)

    def test_receive_increases_stock_and_updates_avg_cost(self, django_user_model):
        from core.models import InventoryItem, InventoryMovement, ProjectInventory

        user = django_user_model.objects.create_user(username="invuser")

        m = InventoryMovement.objects.create(
            item=self.item,
            to_location=self.storage,
            movement_type="RECEIVE",
            quantity=Decimal("10"),
            unit_cost=Decimal("20.00"),
            created_by=user,
        )
        m.apply()
        stock = ProjectInventory.objects.get(item=self.item, location=self.storage)
        assert stock.quantity == Decimal("10")
        self.item.refresh_from_db()
        assert isinstance(self.item.average_cost, Decimal)
        assert self.item.average_cost == Decimal("20.00")
        assert m.applied is True

    def test_issue_decreases_stock_and_prevents_negative(self, django_user_model):
        from core.models import InventoryMovement, ProjectInventory

        user = django_user_model.objects.create_user(username="invuser2")

        # Seed stock
        m_seed = InventoryMovement.objects.create(
            item=self.item,
            to_location=self.storage,
            movement_type="RECEIVE",
            quantity=Decimal("3"),
            unit_cost=Decimal("10.00"),
            created_by=user,
        )
        m_seed.apply()
        # Try to issue more than available
        from django.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            InventoryMovement.objects.create(
                item=self.item,
                from_location=self.storage,
                movement_type="ISSUE",
                quantity=Decimal("5"),
                created_by=user,
            ).apply()
        # Issue allowed amount
        im = InventoryMovement.objects.create(
            item=self.item,
            from_location=self.storage,
            movement_type="ISSUE",
            quantity=Decimal("2"),
            created_by=user,
        )
        im.apply()
        stock = ProjectInventory.objects.get(item=self.item, location=self.storage)
        assert stock.quantity == Decimal("1")
        assert im.applied is True

    def test_transfer_moves_between_locations(self, django_user_model):
        from core.models import InventoryMovement, ProjectInventory

        user = django_user_model.objects.create_user(username="invuser3")

        # Seed stock in storage
        m_recv = InventoryMovement.objects.create(
            item=self.item,
            to_location=self.storage,
            movement_type="RECEIVE",
            quantity=Decimal("8"),
            unit_cost=Decimal("15.00"),
            created_by=user,
        )
        m_recv.apply()
        # Transfer 3 to site
        m_tr = InventoryMovement.objects.create(
            item=self.item,
            from_location=self.storage,
            to_location=self.site,
            movement_type="TRANSFER",
            quantity=Decimal("3"),
            created_by=user,
        )
        m_tr.apply()
        s_from = ProjectInventory.objects.get(item=self.item, location=self.storage)
        s_to = ProjectInventory.objects.get(item=self.item, location=self.site)
        assert s_from.quantity == Decimal("5")
        assert s_to.quantity == Decimal("3")

    def test_adjust_never_goes_negative(self, django_user_model):
        from core.models import InventoryMovement, ProjectInventory

        user = django_user_model.objects.create_user(username="invuser4")

        # Seed stock 1
        m_recv = InventoryMovement.objects.create(
            item=self.item,
            to_location=self.storage,
            movement_type="RECEIVE",
            quantity=Decimal("1"),
            unit_cost=Decimal("9.00"),
            created_by=user,
        )
        m_recv.apply()
        # Adjust -5 (should clamp to 0)
        m_adj = InventoryMovement.objects.create(
            item=self.item,
            to_location=self.storage,
            movement_type="ADJUST",
            quantity=Decimal("-5"),
            created_by=user,
        )
        m_adj.apply()
        stock = ProjectInventory.objects.get(item=self.item, location=self.storage)
        assert stock.quantity == Decimal("0")

    def test_low_stock_alert_on_issue(self, django_user_model):
        from core.models import InventoryMovement, Notification, ProjectInventory

        user = django_user_model.objects.create_user(username="invuser5", is_staff=True)

        # Seed stock 6, threshold 5 -> after issue 2 -> 4 < 5 triggers alert
        m_recv = InventoryMovement.objects.create(
            item=self.item,
            to_location=self.storage,
            movement_type="RECEIVE",
            quantity=Decimal("6"),
            unit_cost=Decimal("12.00"),
            created_by=user,
        )
        m_recv.apply()
        m_issue = InventoryMovement.objects.create(
            item=self.item,
            from_location=self.storage,
            movement_type="ISSUE",
            quantity=Decimal("2"),
            created_by=user,
        )
        m_issue.apply()
        # There should be at least one notification created for staff
        assert Notification.objects.filter(title__icontains="Stock bajo").exists()

    def test_idempotent_apply(self, django_user_model):
        from core.models import InventoryMovement, ProjectInventory

        user = django_user_model.objects.create_user(username="invuser6")
        m = InventoryMovement.objects.create(
            item=self.item,
            to_location=self.storage,
            movement_type="RECEIVE",
            quantity=Decimal("2"),
            unit_cost=Decimal("11.00"),
            created_by=user,
        )
        m.apply()
        before = ProjectInventory.objects.get(item=self.item, location=self.storage).quantity
        # Calling apply again should do nothing
        m.apply()
        after = ProjectInventory.objects.get(item=self.item, location=self.storage).quantity
        assert before == after


@pytest.mark.django_db
class TestInventoryAPILists:
    def test_list_endpoints(self, client, django_user_model):
        from core.models import InventoryItem, InventoryLocation

        user = django_user_model.objects.create_user(username="apiuser", password="x", is_staff=True)
        client.force_login(user)

        item = InventoryItem.objects.create(name="Brush", category="HERRAMIENTA")
        loc = InventoryLocation.objects.create(name="WH1", is_storage=True)
        r1 = client.get("/api/v1/inventory/items/")
        assert r1.status_code == 200
        r2 = client.get("/api/v1/inventory/locations/")
        assert r2.status_code == 200
        r3 = client.get("/api/v1/inventory/stocks/")
        assert r3.status_code == 200
        r4 = client.get("/api/v1/inventory/movements/")
        assert r4.status_code == 200
