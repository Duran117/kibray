import pytest
from datetime import date
from django.core.exceptions import ValidationError

from core.models import Employee, Project, ResourceAssignment


@pytest.fixture
def employee():
    return Employee.objects.create(
        first_name="Ana",
        last_name="Lopez",
        social_security_number="111-22-3333",
        hourly_rate=25,
    )


@pytest.fixture
def projects():
    p1 = Project.objects.create(name="Proyecto Uno", project_code="PRJ-A")
    p2 = Project.objects.create(name="Proyecto Dos", project_code="PRJ-B")
    p3 = Project.objects.create(name="Proyecto Tres", project_code="PRJ-C")
    return p1, p2, p3


@pytest.mark.django_db
def test_allows_two_shifts_same_day(employee, projects):
    today = date.today()
    p1, p2, _ = projects
    ResourceAssignment.objects.create(employee=employee, project=p1, date=today, shift="MORNING")
    ResourceAssignment.objects.create(employee=employee, project=p2, date=today, shift="AFTERNOON")
    assert ResourceAssignment.objects.filter(employee=employee, date=today).count() == 2


@pytest.mark.django_db
def test_third_assignment_same_day_rejected(employee, projects):
    today = date.today()
    p1, p2, p3 = projects
    ResourceAssignment.objects.create(employee=employee, project=p1, date=today, shift="MORNING")
    ResourceAssignment.objects.create(employee=employee, project=p2, date=today, shift="AFTERNOON")
    with pytest.raises(ValidationError):
        ResourceAssignment.objects.create(employee=employee, project=p3, date=today, shift="MORNING")


@pytest.mark.django_db
def test_full_day_blocks_other_shifts(employee, projects):
    today = date.today()
    p1, p2, _ = projects
    ResourceAssignment.objects.create(employee=employee, project=p1, date=today, shift="FULL_DAY")
    with pytest.raises(ValidationError):
        ResourceAssignment.objects.create(employee=employee, project=p2, date=today, shift="MORNING")


@pytest.mark.django_db
def test_cannot_add_full_day_when_shifts_exist(employee, projects):
    today = date.today()
    p1, p2, _ = projects
    ResourceAssignment.objects.create(employee=employee, project=p1, date=today, shift="MORNING")
    with pytest.raises(ValidationError):
        ResourceAssignment.objects.create(employee=employee, project=p2, date=today, shift="FULL_DAY")
