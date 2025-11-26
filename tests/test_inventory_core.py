import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from core.models import (
    InventoryItem, InventoryLocation, ProjectInventory,
    InventoryMovement, Project
)

@pytest.mark.django_db
def test_inventory_item_avg_cost_calculation():
    """Test average cost calculation with multiple purchases."""
    item = InventoryItem.objects.create(
        name='Paint Gallon',
        category='PINTURA',
        valuation_method='AVG',
        average_cost=Decimal('0')
    )
    
    # First purchase: 10 units @ $20 each
    item.update_average_cost(Decimal('20'), Decimal('10'))
    assert item.average_cost == Decimal('20')
    
    # Second purchase: 5 units @ $30 each
    # Weighted avg: (10*20 + 5*30) / (10+5) = 350/15 = 23.33...
    item.update_average_cost(Decimal('30'), Decimal('5'))
    assert item.average_cost > Decimal('23') and item.average_cost < Decimal('24')


@pytest.mark.django_db
def test_inventory_fifo_cost_calculation():
    """Test FIFO cost calculation."""
    user = User.objects.create_user(username='admin', password='pass')
    warehouse = InventoryLocation.objects.create(name='Warehouse', is_storage=True)
    
    item = InventoryItem.objects.create(
        name='Brush Set',
        category='HERRAMIENTA',
        valuation_method='FIFO'
    )
    
    # Create purchase movements with different costs
    # Purchase 1: 10 units @ $5
    mov1 = InventoryMovement.objects.create(
        item=item,
        to_location=warehouse,
        movement_type='RECEIVE',
        quantity=Decimal('10'),
        unit_cost=Decimal('5'),
        created_by=user,
        applied=True
    )
    
    # Purchase 2: 10 units @ $7
    mov2 = InventoryMovement.objects.create(
        item=item,
        to_location=warehouse,
        movement_type='RECEIVE',
        quantity=Decimal('10'),
        unit_cost=Decimal('7'),
        created_by=user,
        applied=True
    )
    
    # Calculate FIFO cost for 15 units (should use 10 @ $5 + 5 @ $7 = 50 + 35 = 85)
    total_cost, remaining = item.get_fifo_cost(Decimal('15'))
    assert total_cost == Decimal('85')
    assert remaining == Decimal('0')


@pytest.mark.django_db
def test_inventory_transfer_multi_location():
    """Test bulk transfer between locations."""
    user = User.objects.create_user(username='pm', password='pass')
    warehouse = InventoryLocation.objects.create(name='Main Warehouse', is_storage=True)
    project = Project.objects.create(name='Site A', start_date='2025-01-01')
    site = InventoryLocation.objects.create(name='Site Storage', project=project)
    
    # Create item with stock in warehouse
    item = InventoryItem.objects.create(
        name='Roller',
        category='HERRAMIENTA',
        valuation_method='AVG',
        average_cost=Decimal('15')
    )
    
    warehouse_stock = ProjectInventory.objects.create(
        item=item,
        location=warehouse,
        quantity=Decimal('50')
    )
    
    # Transfer 20 units to site
    movement = InventoryMovement.objects.create(
        item=item,
        from_location=warehouse,
        to_location=site,
        movement_type='TRANSFER',
        quantity=Decimal('20'),
        reason='Initial site setup',
        created_by=user
    )
    
    movement.apply()
    
    # Verify warehouse reduced
    warehouse_stock.refresh_from_db()
    assert warehouse_stock.quantity == Decimal('30')
    
    # Verify site stock increased
    site_stock = ProjectInventory.objects.get(item=item, location=site)
    assert site_stock.quantity == Decimal('20')


@pytest.mark.django_db
def test_inventory_negative_prevention():
    """Test that negative inventory is prevented."""
    user = User.objects.create_user(username='worker', password='pass')
    warehouse = InventoryLocation.objects.create(name='Storage', is_storage=True)
    
    item = InventoryItem.objects.create(
        name='Tape',
        category='MATERIAL',
        valuation_method='AVG'
    )
    
    # Only 10 units available
    ProjectInventory.objects.create(
        item=item,
        location=warehouse,
        quantity=Decimal('10')
    )
    
    # Try to issue 15 units (should fail)
    movement = InventoryMovement.objects.create(
        item=item,
        from_location=warehouse,
        movement_type='ISSUE',
        quantity=Decimal('15'),
        reason='Project consumption',
        created_by=user
    )
    
    with pytest.raises(ValidationError) as exc:
        movement.apply()
    
    assert 'insuficiente' in str(exc.value).lower()


@pytest.mark.django_db
def test_inventory_stock_adjustment():
    """Test manual stock adjustment after physical count."""
    user = User.objects.create_user(username='manager', password='pass')
    warehouse = InventoryLocation.objects.create(name='Warehouse', is_storage=True)
    
    item = InventoryItem.objects.create(
        name='Ladder',
        category='ESCALERA',
        is_equipment=True
    )
    
    # Initial stock: 5 units
    stock = ProjectInventory.objects.create(
        item=item,
        location=warehouse,
        quantity=Decimal('5')
    )
    
    # Physical count shows 4 units (1 lost/damaged)
    adjustment = Decimal('4') - Decimal('5')  # -1
    
    movement = InventoryMovement.objects.create(
        item=item,
        to_location=warehouse,
        movement_type='ADJUST',
        quantity=adjustment,
        reason='Physical count correction',
        created_by=user
    )
    
    movement.apply()
    
    stock.refresh_from_db()
    assert stock.quantity == Decimal('4')


@pytest.mark.django_db
def test_low_stock_detection():
    """Test reorder point detection."""
    item = InventoryItem.objects.create(
        name='Brush',
        category='HERRAMIENTA',
        low_stock_threshold=Decimal('20')
    )
    
    warehouse = InventoryLocation.objects.create(name='Main', is_storage=True)
    
    # Stock below threshold
    ProjectInventory.objects.create(
        item=item,
        location=warehouse,
        quantity=Decimal('15')
    )
    
    alert = item.check_reorder_point()
    
    assert alert['needs_reorder'] is True
    assert alert['shortage'] == Decimal('5')
    assert alert['current_qty'] == Decimal('15')


@pytest.mark.django_db
def test_inventory_valuation_methods():
    """Test different valuation methods return correct costs."""
    # FIFO item
    fifo_item = InventoryItem.objects.create(
        name='FIFO Item',
        category='MATERIAL',
        valuation_method='FIFO',
        average_cost=Decimal('10')
    )
    
    # AVG item
    avg_item = InventoryItem.objects.create(
        name='AVG Item',
        category='MATERIAL',
        valuation_method='AVG',
        average_cost=Decimal('15')
    )
    
    # LIFO item
    lifo_item = InventoryItem.objects.create(
        name='LIFO Item',
        category='MATERIAL',
        valuation_method='LIFO',
        average_cost=Decimal('20')
    )
    
    # Test AVG (simplest case)
    cost_avg = avg_item.get_cost_for_quantity(Decimal('5'))
    assert cost_avg == Decimal('75')  # 5 * 15
    
    # Test FIFO and LIFO (will use average_cost since no purchase history)
    cost_fifo = fifo_item.get_cost_for_quantity(Decimal('10'))
    assert cost_fifo == Decimal('100')  # Falls back to avg: 10 * 10
    
    cost_lifo = lifo_item.get_cost_for_quantity(Decimal('3'))
    assert cost_lifo == Decimal('60')  # Falls back to avg: 3 * 20
