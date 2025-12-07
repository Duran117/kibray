"""
Natural Language Processing Service for Daily Planning

Handles text and voice command parsing for activity creation and management.

Features:
- Parse natural language commands
- Extract entities (activities, employees, dates, materials)
- Support Spanish and English
- Command execution
"""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from django.db.models import Q
from django.utils import timezone

from core.models import ActivityTemplate, DailyPlan, Employee, PlannedActivity, Project


# ===== DATA STRUCTURES =====


@dataclass
class ParsedCommand:
    """Represents a parsed natural language command"""

    command_type: str  # 'add_activity', 'assign_employee', 'check_materials', 'create_plan'
    raw_text: str
    confidence: float  # 0-1
    entities: Dict  # Extracted entities
    validation_errors: List[str]
    suggested_action: str

    @property
    def is_valid(self) -> bool:
        return len(self.validation_errors) == 0 and self.confidence > 0.5

    def to_dict(self) -> Dict:
        return {
            "command_type": self.command_type,
            "raw_text": self.raw_text,
            "confidence": self.confidence,
            "entities": self.entities,
            "validation_errors": self.validation_errors,
            "suggested_action": self.suggested_action,
            "is_valid": self.is_valid,
        }


@dataclass
class ActivityEntity:
    """Extracted activity information"""

    title: str
    description: str = ""
    estimated_hours: Optional[float] = None
    employees: List[str] = None  # Employee names
    materials: List[str] = None  # Material descriptions
    template_name: Optional[str] = None

    def __post_init__(self):
        if self.employees is None:
            self.employees = []
        if self.materials is None:
            self.materials = []


# ===== NLP SERVICE =====


class DailyPlanNLU:
    """
    Natural Language Understanding for Daily Planning

    Parses commands in Spanish and English.
    """

    # Command patterns (Spanish and English)
    PATTERNS = {
        "add_activity": [
            # Spanish
            r"(?:agregar|crear|añadir|nueva?)\s+(?:actividad|tarea)[:.]?\s*(.+)",
            r"(?:necesitamos?|hay que|tenemos que)\s+(.+)",
            r"(?:mañana|hoy|siguiente)\s+(?:necesitamos?|vamos a|hay que)\s+(.+)",
            # English
            r"(?:add|create|new)\s+(?:activity|task)[:.]?\s*(.+)",
            r"(?:we need to|need to|have to|must)\s+(.+)",
            r"(?:tomorrow|today|next)\s+(?:we need|need to|will)\s+(.+)",
        ],
        "assign_employee": [
            # Spanish
            r"(?:asignar|dar|poner)\s+(?:a|para)\s+(\w+)",
            r"(\w+)\s+(?:va a|debe|tiene que)\s+(.+)",
            r"(\w+)\s+(?:y|,)\s+(\w+)\s+(?:van a|deben|tienen que)\s+(.+)",
            # English
            r"(?:assign|give)\s+(?:to|)\s+(\w+)",
            r"(\w+)\s+(?:will|should|must)\s+(.+)",
        ],
        "set_duration": [
            # Spanish
            r"(\d+)\s*(?:horas?|hrs?|h)",
            # English
            r"(\d+)\s*(?:hours?|hrs?|h)",
        ],
        "set_date": [
            # Spanish
            r"(?:mañana|tomorrow)",
            r"(?:hoy|today)",
            r"(?:pasado mañana|day after tomorrow)",
            r"(?:el|on)\s+(\d{1,2})\s+(?:de\s+)?(\w+)",
            # English
            r"(?:on|for)\s+(\w+)",
        ],
        "materials": [
            # Spanish
            r"(?:materiales?|necesitamos?|usar|con)\s+(.+)",
            r"(\d+)\s*(?:galones?|litros?|piezas?|unidades?)\s+(?:de\s+)?(.+)",
            # English
            r"(?:materials?|using|with)\s+(.+)",
            r"(\d+)\s*(?:gallons?|gal|liters?|pieces?|pcs|units?)\s+(?:of\s+)?(.+)",
        ],
    }

    # Common activity verbs
    ACTIVITY_VERBS = {
        # Spanish
        "pintar": "paint",
        "instalar": "install",
        "construir": "build",
        "reparar": "repair",
        "limpiar": "clean",
        "demoler": "demolish",
        "excavar": "excavate",
        "soldar": "weld",
        "cortar": "cut",
        "medir": "measure",
        # English
        "paint": "paint",
        "install": "install",
        "build": "build",
        "repair": "repair",
        "clean": "clean",
        "demolish": "demolish",
        "excavate": "excavate",
        "weld": "weld",
        "cut": "cut",
        "measure": "measure",
    }

    # Date keywords
    DATE_KEYWORDS = {
        "mañana": 1,
        "tomorrow": 1,
        "hoy": 0,
        "today": 0,
        "pasado mañana": 2,
        "day after tomorrow": 2,
    }

    def __init__(self):
        """Initialize NLU service"""
        pass

    def parse_command(self, text: str, context: Optional[Dict] = None) -> ParsedCommand:
        """
        Parse natural language command

        Args:
            text: Command text (Spanish or English)
            context: Optional context (project, date, etc.)

        Returns:
            ParsedCommand with extracted entities
        """
        text = text.strip()
        context = context or {}

        # Detect command type
        command_type = self._detect_command_type(text)

        # Extract entities based on command type
        entities = {}
        validation_errors = []
        confidence = 0.5

        if command_type == "add_activity":
            entities, confidence = self._extract_activity_entities(text)

            # Validate
            if not entities.get("title"):
                validation_errors.append("No activity title detected")
            else:
                confidence += 0.2

        elif command_type == "assign_employee":
            employees = self._extract_employees(text)
            if employees:
                entities["employees"] = employees
                confidence += 0.3

        elif command_type == "unknown":
            # Try to extract activities anyway
            entities, confidence = self._extract_activity_entities(text)
            if entities.get("title"):
                command_type = "add_activity"
            else:
                validation_errors.append("Could not understand command")

        # Generate suggested action
        suggested_action = self._generate_suggestion(command_type, entities, validation_errors)

        return ParsedCommand(
            command_type=command_type,
            raw_text=text,
            confidence=min(1.0, confidence),
            entities=entities,
            validation_errors=validation_errors,
            suggested_action=suggested_action,
        )

    def _detect_command_type(self, text: str) -> str:
        """Detect the type of command from text"""
        text_lower = text.lower()

        # Check for add activity patterns
        for pattern in self.PATTERNS["add_activity"]:
            if re.search(pattern, text_lower):
                return "add_activity"

        # Check for employee assignment
        for pattern in self.PATTERNS["assign_employee"]:
            if re.search(pattern, text_lower):
                return "assign_employee"

        # Check for activity verbs
        for verb in self.ACTIVITY_VERBS.keys():
            if verb in text_lower:
                return "add_activity"

        return "unknown"

    def _extract_activity_entities(self, text: str) -> Tuple[Dict, float]:
        """
        Extract activity-related entities from text

        Returns:
            (entities dict, confidence score)
        """
        entities = {}
        confidence = 0.5
        text_lower = text.lower()

        # Extract title
        title = self._extract_activity_title(text)
        if title:
            entities["title"] = title
            confidence += 0.2

        # Extract employees
        employees = self._extract_employees(text)
        if employees:
            entities["employees"] = employees
            confidence += 0.1

        # Extract duration
        hours = self._extract_duration(text)
        if hours:
            entities["estimated_hours"] = hours
            confidence += 0.1

        # Extract materials
        materials = self._extract_materials(text)
        if materials:
            entities["materials"] = materials
            confidence += 0.1

        return entities, confidence

    def _extract_activity_title(self, text: str) -> Optional[str]:
        """Extract activity title from text"""
        text_lower = text.lower()

        # Try patterns
        for pattern in self.PATTERNS["add_activity"]:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                # Get the captured activity description
                activity_text = match.group(1).strip()

                # Clean up common endings
                activity_text = re.sub(r"\s+y\s+.+(?:va|debe|tiene)", "", activity_text)
                activity_text = re.sub(r"\s+and\s+.+(?:will|should|must)", "", activity_text)

                # Capitalize first letter
                if activity_text:
                    return activity_text[0].upper() + activity_text[1:]

        # Fallback: look for activity verbs
        for verb_es, verb_en in self.ACTIVITY_VERBS.items():
            if verb_es in text_lower:
                # Extract text after verb
                parts = text_lower.split(verb_es, 1)
                if len(parts) > 1:
                    activity_text = parts[1].strip()
                    # Remove employee names
                    activity_text = re.sub(r",?\s*y\s+\w+\s+van?\s+a\s*", "", activity_text)
                    if activity_text:
                        return f"{verb_en.capitalize()} {activity_text}"

        return None

    def _extract_employees(self, text: str) -> List[str]:
        """Extract employee names from text"""
        employees = []

        # Common Spanish names pattern
        name_pattern = r"\b([A-Z][a-z]+)\b"

        # Look for assignment patterns
        assignment_patterns = [
            r"(?:asignar|dar|poner)\s+(?:a|para)\s+(\w+(?:\s+y\s+\w+)*)",
            r"(\w+(?:\s+y\s+\w+)*)\s+(?:va|debe|tiene)",
            r"(?:assign|give)\s+(?:to|)\s+(\w+(?:\s+and\s+\w+)*)",
        ]

        for pattern in assignment_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                names_text = match.group(1)
                # Split by 'y' (Spanish) or 'and' (English)
                names = re.split(r"\s+(?:y|and|,)\s+", names_text)
                employees.extend([n.strip().capitalize() for n in names if n.strip()])

        # Fallback: extract any capitalized names
        if not employees:
            matches = re.findall(name_pattern, text)
            # Filter out common non-name words
            exclude = {"Mañana", "Hoy", "Tomorrow", "Today", "Add", "Create", "New"}
            employees = [m for m in matches if m not in exclude]

        return employees

    def _extract_duration(self, text: str) -> Optional[float]:
        """Extract duration in hours from text"""
        for pattern in self.PATTERNS["set_duration"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    pass
        return None

    def _extract_materials(self, text: str) -> List[str]:
        """Extract materials from text"""
        materials = []

        for pattern in self.PATTERNS["materials"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                material_text = match.group(match.lastindex).strip()
                # Split by commas or 'y'/'and'
                parts = re.split(r",|\s+y\s+|\s+and\s+", material_text)
                materials.extend([p.strip() for p in parts if p.strip()])

        return materials

    def _generate_suggestion(self, command_type: str, entities: Dict, errors: List[str]) -> str:
        """Generate human-readable suggestion for user"""
        if errors:
            return f"⚠️ {', '.join(errors)}"

        if command_type == "add_activity":
            title = entities.get("title", "Unknown activity")
            employees = entities.get("employees", [])
            hours = entities.get("estimated_hours")

            suggestion = f"✨ Create activity: '{title}'"
            if employees:
                suggestion += f"\n👤 Assign to: {', '.join(employees)}"
            if hours:
                suggestion += f"\n⏱️ Duration: {hours} hours"

            return suggestion

        return "No suggestion available"

    def execute_command(
        self, parsed_command: ParsedCommand, daily_plan: DailyPlan, user
    ) -> Tuple[bool, str, Optional[PlannedActivity]]:
        """
        Execute a parsed command

        Args:
            parsed_command: Parsed command to execute
            daily_plan: Target daily plan
            user: User executing command

        Returns:
            (success, message, created_activity)
        """
        if not parsed_command.is_valid:
            return False, f"Invalid command: {', '.join(parsed_command.validation_errors)}", None

        if parsed_command.command_type == "add_activity":
            return self._execute_add_activity(parsed_command, daily_plan)

        return False, f"Command type '{parsed_command.command_type}' not supported yet", None

    def _execute_add_activity(
        self, parsed_command: ParsedCommand, daily_plan: DailyPlan
    ) -> Tuple[bool, str, Optional[PlannedActivity]]:
        """Execute 'add_activity' command"""
        entities = parsed_command.entities

        # Create activity
        activity = PlannedActivity.objects.create(
            daily_plan=daily_plan,
            title=entities["title"],
            description=f"Created by AI from: '{parsed_command.raw_text}'",
            estimated_hours=entities.get("estimated_hours", 0),
            order=daily_plan.activities.count(),
            status="PENDING",
        )

        # Assign employees
        employees_assigned = []
        for employee_name in entities.get("employees", []):
            # Try to find employee
            employees = Employee.objects.filter(
                Q(first_name__iexact=employee_name) | Q(last_name__iexact=employee_name)
            )
            if employees.exists():
                emp = employees.first()
                activity.assigned_employees.add(emp)
                employees_assigned.append(f"{emp.first_name} {emp.last_name}")

        # Set materials
        if entities.get("materials"):
            activity.materials_needed = entities["materials"]
            activity.save()

        message = f"✅ Activity created: '{activity.title}'"
        if employees_assigned:
            message += f"\n👤 Assigned: {', '.join(employees_assigned)}"

        return True, message, activity


# ===== SINGLETON =====

nlp_service = DailyPlanNLU()
