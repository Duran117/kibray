"""
Daily Plan AI Assistant

Provides intelligent analysis, suggestions, and auto-creation capabilities
for daily planning system.

Features:
- Material availability checking with predictions
- Employee conflict detection
- Schedule coherence validation
- Safety & compliance checking
- Natural language command processing
- Activity auto-creation
"""

from dataclasses import dataclass
from datetime import datetime

from django.db.models import Sum
from django.utils import timezone

from core.models import (
    DailyPlan,
    Employee,
    InventoryItem,
    PlannedActivity,
    Project,
)

# ===== DATA STRUCTURES =====


@dataclass
class MaterialIssue:
    """Represents a material availability issue"""

    material_name: str
    required: float
    available: float
    unit: str
    severity: str  # 'critical', 'warning', 'info'
    suggestion: str
    auto_fixable: bool = False


@dataclass
class EmployeeIssue:
    """Represents an employee assignment issue"""

    employee_name: str
    issue_type: str  # 'double_booking', 'overtime', 'skill_mismatch', 'unavailable'
    description: str
    severity: str
    suggestion: str
    affected_activities: list[int]  # Activity IDs


@dataclass
class ScheduleIssue:
    """Represents a schedule coherence issue"""

    issue_type: str  # 'dependency', 'time_estimate', 'bottleneck', 'missing_link'
    description: str
    severity: str
    suggestion: str
    affected_activities: list[int]


@dataclass
class SafetyIssue:
    """Represents a safety or compliance issue"""

    issue_type: str  # 'missing_sop', 'certification', 'equipment', 'weather'
    description: str
    severity: str
    suggestion: str
    required_action: str


@dataclass
class ActivitySuggestion:
    """Represents an AI-suggested activity"""

    title: str
    description: str
    estimated_hours: float
    suggested_employees: list[str]  # Employee names
    required_materials: list[str]
    schedule_item_id: int | None = None
    activity_template_id: int | None = None
    confidence: float = 0.8  # 0-1


@dataclass
class AnalysisReport:
    """Complete AI analysis report"""

    daily_plan_id: int
    timestamp: datetime
    overall_score: int  # 0-100
    passed_checks: list[str]
    material_issues: list[MaterialIssue]
    employee_issues: list[EmployeeIssue]
    schedule_issues: list[ScheduleIssue]
    safety_issues: list[SafetyIssue]
    suggestions: list[ActivitySuggestion]

    @property
    def has_critical_issues(self) -> bool:
        return any(
            issue.severity == "critical"
            for issue in (
                self.material_issues
                + self.employee_issues
                + self.schedule_issues
                + self.safety_issues
            )
        )

    @property
    def total_issues(self) -> int:
        return (
            len(self.material_issues)
            + len(self.employee_issues)
            + len(self.schedule_issues)
            + len(self.safety_issues)
        )

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        return {
            "daily_plan_id": self.daily_plan_id,
            "timestamp": self.timestamp.isoformat(),
            "overall_score": self.overall_score,
            "passed_checks": self.passed_checks,
            "material_issues": [
                {
                    "material": i.material_name,
                    "required": i.required,
                    "available": i.available,
                    "unit": i.unit,
                    "severity": i.severity,
                    "suggestion": i.suggestion,
                    "auto_fixable": i.auto_fixable,
                }
                for i in self.material_issues
            ],
            "employee_issues": [
                {
                    "employee": i.employee_name,
                    "type": i.issue_type,
                    "description": i.description,
                    "severity": i.severity,
                    "suggestion": i.suggestion,
                    "affected_activities": i.affected_activities,
                }
                for i in self.employee_issues
            ],
            "schedule_issues": [
                {
                    "type": i.issue_type,
                    "description": i.description,
                    "severity": i.severity,
                    "suggestion": i.suggestion,
                    "affected_activities": i.affected_activities,
                }
                for i in self.schedule_issues
            ],
            "safety_issues": [
                {
                    "type": i.issue_type,
                    "description": i.description,
                    "severity": i.severity,
                    "suggestion": i.suggestion,
                    "required_action": i.required_action,
                }
                for i in self.safety_issues
            ],
            "suggestions": [
                {
                    "title": s.title,
                    "description": s.description,
                    "estimated_hours": s.estimated_hours,
                    "suggested_employees": s.suggested_employees,
                    "required_materials": s.required_materials,
                    "confidence": s.confidence,
                }
                for s in self.suggestions
            ],
            "total_issues": self.total_issues,
            "has_critical": self.has_critical_issues,
        }


# ===== MAIN AI ASSISTANT CLASS =====


class DailyPlanAIAssistant:
    """
    AI Assistant for Daily Planning

    Provides intelligent analysis and suggestions for daily plans.
    """

    def analyze_plan(self, daily_plan: DailyPlan) -> AnalysisReport:
        """
        Run comprehensive analysis on a daily plan

        Returns:
            AnalysisReport with all findings
        """
        passed_checks = []
        material_issues = []
        employee_issues = []
        schedule_issues = []
        safety_issues = []

        activities = daily_plan.activities.all()

        # Run all checks
        passed, mat_issues = self._check_materials(activities, daily_plan.project)
        passed_checks.extend(passed)
        material_issues.extend(mat_issues)

        passed, emp_issues = self._check_employees(activities, daily_plan.plan_date)
        passed_checks.extend(passed)
        employee_issues.extend(emp_issues)

        passed, sched_issues = self._check_schedule(activities)
        passed_checks.extend(passed)
        schedule_issues.extend(sched_issues)

        passed, safe_issues = self._check_safety(activities, daily_plan)
        passed_checks.extend(passed)
        safety_issues.extend(safe_issues)

        # Calculate overall score
        total_checks = (
            len(passed_checks)
            + len(material_issues)
            + len(employee_issues)
            + len(schedule_issues)
            + len(safety_issues)
        )
        score = int(len(passed_checks) / total_checks * 100) if total_checks > 0 else 100

        # Penalize for critical issues
        critical_count = sum(
            1
            for issue in (material_issues + employee_issues + schedule_issues + safety_issues)
            if getattr(issue, "severity", "") == "critical"
        )
        score = max(0, score - (critical_count * 15))

        return AnalysisReport(
            daily_plan_id=daily_plan.id,
            timestamp=timezone.now(),
            overall_score=score,
            passed_checks=passed_checks,
            material_issues=material_issues,
            employee_issues=employee_issues,
            schedule_issues=schedule_issues,
            safety_issues=safety_issues,
            suggestions=[],  # TODO: Implement smart suggestions
        )

    def _check_materials(
        self, activities: list[PlannedActivity], project: Project
    ) -> tuple[list[str], list[MaterialIssue]]:
        """Check material availability for all activities"""
        passed = []
        issues = []

        # Aggregate all materials needed
        materials_needed = {}  # {material_name: total_quantity}

        for activity in activities:
            if activity.materials_needed:
                for material_str in activity.materials_needed:
                    # Parse material string: "Paint:White:5gal" or "Screws:100"
                    parts = material_str.split(":")
                    if len(parts) >= 2:
                        material_name = parts[0].strip()
                        try:
                            quantity = float(
                                parts[-1]
                                .replace("gal", "")
                                .replace("lb", "")
                                .replace("pcs", "")
                                .strip()
                            )
                            materials_needed[material_name] = (
                                materials_needed.get(material_name, 0) + quantity
                            )
                        except ValueError:
                            continue

        if not materials_needed:
            passed.append("No materials required")
            return passed, issues

        # Check inventory
        for material_name, required_qty in materials_needed.items():
            # Find in inventory
            inventory_items = InventoryItem.objects.filter(
                name__icontains=material_name, project=project
            )

            if not inventory_items.exists():
                issues.append(
                    MaterialIssue(
                        material_name=material_name,
                        required=required_qty,
                        available=0,
                        unit="units",
                        severity="critical",
                        suggestion=f"Material '{material_name}' not found in inventory. Please add to inventory or order from supplier.",
                        auto_fixable=False,
                    )
                )
                continue

            # Sum available quantity
            available_qty = inventory_items.aggregate(total=Sum("quantity"))["total"] or 0

            if available_qty < required_qty:
                shortage = required_qty - available_qty
                issues.append(
                    MaterialIssue(
                        material_name=material_name,
                        required=required_qty,
                        available=available_qty,
                        unit="units",
                        severity="critical" if available_qty < required_qty * 0.5 else "warning",
                        suggestion=f"Order {shortage:.1f} units of {material_name}. Current stock: {available_qty:.1f}, needed: {required_qty:.1f}",
                        auto_fixable=True,  # Could auto-create purchase order
                    )
                )
            else:
                passed.append(f"Material '{material_name}' available ({available_qty:.1f} units)")

        return passed, issues

    def _check_employees(
        self, activities: list[PlannedActivity], plan_date
    ) -> tuple[list[str], list[EmployeeIssue]]:
        """Check employee assignments and conflicts"""
        passed = []
        issues = []

        # Check for unassigned activities
        unassigned = [a for a in activities if not a.assigned_employees.exists()]
        if unassigned:
            issues.append(
                EmployeeIssue(
                    employee_name="Unassigned",
                    issue_type="missing_assignment",
                    description=f"{len(unassigned)} activities have no assigned employees",
                    severity="critical",
                    suggestion="Assign at least one employee to each activity",
                    affected_activities=[a.id for a in unassigned],
                )
            )
        else:
            passed.append("All activities have assigned employees")

        # Check for double-bookings
        employee_hours = {}  # {employee_id: total_hours}
        for activity in activities:
            for emp in activity.assigned_employees.all():
                hours = activity.estimated_hours or 0
                employee_hours[emp.id] = employee_hours.get(emp.id, 0) + hours

        # Check for overtime (> 8 hours per day)
        for emp_id, total_hours in employee_hours.items():
            if total_hours > 8:
                try:
                    employee = Employee.objects.get(id=emp_id)
                    issues.append(
                        EmployeeIssue(
                            employee_name=f"{employee.first_name} {employee.last_name}",
                            issue_type="overtime",
                            description=f"Scheduled for {total_hours:.1f} hours (exceeds 8-hour limit)",
                            severity="warning",
                            suggestion="Reduce workload or split tasks among multiple employees",
                            affected_activities=[
                                a.id for a in activities if employee in a.assigned_employees.all()
                            ],
                        )
                    )
                except Employee.DoesNotExist:
                    pass
            else:
                if emp_id not in [issue.employee_name for issue in issues]:
                    try:
                        employee = Employee.objects.get(id=emp_id)
                        passed.append(
                            f"Employee {employee.first_name} {employee.last_name} workload is reasonable"
                        )
                    except Employee.DoesNotExist:
                        pass

        # TODO: Check for conflicts with other projects on same date

        return passed, issues

    def _check_schedule(
        self, activities: list[PlannedActivity]
    ) -> tuple[list[str], list[ScheduleIssue]]:
        """Check schedule coherence and dependencies"""
        passed = []
        issues = []

        # Check if activities are linked to schedule
        unlinked = [a for a in activities if not a.schedule_item]
        if unlinked:
            issues.append(
                ScheduleIssue(
                    issue_type="missing_link",
                    description=f"{len(unlinked)} activities not linked to schedule items",
                    severity="warning",
                    suggestion="Link activities to schedule items for better tracking",
                    affected_activities=[a.id for a in unlinked],
                )
            )
        else:
            passed.append("All activities linked to schedule")

        # Check time estimates
        activities_without_time = [
            a for a in activities if not a.estimated_hours or a.estimated_hours <= 0
        ]
        if activities_without_time:
            issues.append(
                ScheduleIssue(
                    issue_type="time_estimate",
                    description=f"{len(activities_without_time)} activities missing time estimates",
                    severity="warning",
                    suggestion="Add estimated hours for better planning",
                    affected_activities=[a.id for a in activities_without_time],
                )
            )
        else:
            passed.append("All activities have time estimates")

        # Check for unrealistic time estimates (> 12 hours single activity)
        long_activities = [a for a in activities if a.estimated_hours and a.estimated_hours > 12]
        if long_activities:
            issues.append(
                ScheduleIssue(
                    issue_type="time_estimate",
                    description=f"{len(long_activities)} activities have unrealistically long estimates (> 12 hours)",
                    severity="warning",
                    suggestion="Break down long activities into smaller tasks",
                    affected_activities=[a.id for a in long_activities],
                )
            )

        return passed, issues

    def _check_safety(
        self, activities: list[PlannedActivity], daily_plan: DailyPlan
    ) -> tuple[list[str], list[SafetyIssue]]:
        """Check safety and compliance requirements"""
        passed = []
        issues = []

        # Check for SOPs
        activities_without_sop = [a for a in activities if not a.activity_template]
        if activities_without_sop:
            issues.append(
                SafetyIssue(
                    issue_type="missing_sop",
                    description=f"{len(activities_without_sop)} activities missing SOP templates",
                    severity="warning",
                    suggestion="Link activities to SOP templates for standardized procedures",
                    required_action="Review SOP library and assign templates",
                )
            )
        else:
            passed.append("All activities have SOP templates")

        # Check weather conditions
        if daily_plan.weather_data:
            weather = daily_plan.weather_data
            temp = weather.get("temperature")
            conditions = weather.get("conditions", "").lower()

            # Check for extreme conditions
            if temp and (temp < 32 or temp > 100):
                issues.append(
                    SafetyIssue(
                        issue_type="weather",
                        description=f"Extreme temperature: {temp}°F",
                        severity="critical",
                        suggestion="Consider rescheduling outdoor work or providing temperature safety measures",
                        required_action="Review outdoor activities and worker safety protocols",
                    )
                )
            elif "rain" in conditions or "storm" in conditions:
                issues.append(
                    SafetyIssue(
                        issue_type="weather",
                        description=f"Adverse weather conditions: {conditions}",
                        severity="warning",
                        suggestion="Postpone outdoor activities or ensure adequate protection",
                        required_action="Review outdoor work schedule",
                    )
                )
            else:
                passed.append("Weather conditions are suitable for planned work")

        # TODO: Check employee certifications
        # TODO: Check required safety equipment

        return passed, issues

    def generate_checklist(self, daily_plan: DailyPlan) -> dict:
        """
        Generate AI checklist for display

        Returns:
            Dict with passed, warnings, and critical sections
        """
        report = self.analyze_plan(daily_plan)

        return {
            "overall_score": report.overall_score,
            "passed": report.passed_checks,
            "warnings": [
                {
                    "title": f"Material Issue: {i.material_name}",
                    "description": f"Required: {i.required} {i.unit}, Available: {i.available} {i.unit}",
                    "suggestion": i.suggestion,
                    "auto_fixable": i.auto_fixable,
                }
                for i in report.material_issues
                if i.severity == "warning"
            ]
            + [
                {
                    "title": f"Employee Issue: {i.employee_name}",
                    "description": i.description,
                    "suggestion": i.suggestion,
                    "auto_fixable": False,
                }
                for i in report.employee_issues
                if i.severity == "warning"
            ]
            + [
                {
                    "title": "Schedule Issue",
                    "description": i.description,
                    "suggestion": i.suggestion,
                    "auto_fixable": False,
                }
                for i in report.schedule_issues
                if i.severity == "warning"
            ]
            + [
                {
                    "title": "Safety Issue",
                    "description": i.description,
                    "suggestion": i.suggestion,
                    "auto_fixable": False,
                }
                for i in report.safety_issues
                if i.severity == "warning"
            ],
            "critical": [
                {
                    "title": f"Critical Material Shortage: {i.material_name}",
                    "description": f"Required: {i.required} {i.unit}, Available: {i.available} {i.unit}",
                    "action": i.suggestion,
                    "auto_fixable": i.auto_fixable,
                }
                for i in report.material_issues
                if i.severity == "critical"
            ]
            + [
                {
                    "title": f"Critical Employee Issue: {i.employee_name}",
                    "description": i.description,
                    "action": i.suggestion,
                    "auto_fixable": False,
                }
                for i in report.employee_issues
                if i.severity == "critical"
            ]
            + [
                {
                    "title": "Critical Schedule Issue",
                    "description": i.description,
                    "action": i.suggestion,
                    "auto_fixable": False,
                }
                for i in report.schedule_issues
                if i.severity == "critical"
            ]
            + [
                {
                    "title": "Critical Safety Issue",
                    "description": i.description,
                    "action": i.required_action,
                    "auto_fixable": False,
                }
                for i in report.safety_issues
                if i.severity == "critical"
            ],
        }


# ===== SINGLETON INSTANCE =====

daily_plan_ai = DailyPlanAIAssistant()
