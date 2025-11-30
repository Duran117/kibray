"""
Navigation System - Phase 1: Serializers

API serializers for ClientOrganization, ClientContact, and Project selector.
These support the new navigation system with corporate client entities.
"""

from rest_framework import serializers

from core.models import ClientContact, ClientOrganization, Project


class ClientOrganizationSerializer(serializers.ModelSerializer):
    """Serializer for ClientOrganization model."""

    active_projects_count = serializers.ReadOnlyField()
    total_contract_value = serializers.ReadOnlyField()
    outstanding_balance = serializers.ReadOnlyField()
    billing_contact_name = serializers.CharField(
        source="billing_contact.get_full_name",
        read_only=True,
        allow_null=True,
    )
    created_by_name = serializers.CharField(
        source="created_by.get_full_name",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = ClientOrganization
        fields = [
            "id",
            "name",
            "legal_name",
            "tax_id",
            "billing_address",
            "billing_city",
            "billing_state",
            "billing_zip",
            "billing_email",
            "billing_phone",
            "billing_contact",
            "billing_contact_name",
            "payment_terms_days",
            "logo",
            "website",
            "notes",
            "is_active",
            "active_projects_count",
            "total_contract_value",
            "outstanding_balance",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "active_projects_count",
            "total_contract_value",
            "outstanding_balance",
        ]


class ClientOrganizationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for organization lists/dropdowns."""

    active_projects_count = serializers.ReadOnlyField()

    class Meta:
        model = ClientOrganization
        fields = ["id", "name", "logo", "active_projects_count", "is_active"]


class ClientContactSerializer(serializers.ModelSerializer):
    """Serializer for ClientContact model."""

    full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
        allow_null=True,
    )
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    contact_method_display = serializers.CharField(
        source="get_preferred_contact_method_display",
        read_only=True,
    )

    class Meta:
        model = ClientContact
        fields = [
            "id",
            "user",
            "username",
            "full_name",
            "email",
            "organization",
            "organization_name",
            "role",
            "role_display",
            "job_title",
            "department",
            "phone_direct",
            "phone_mobile",
            "preferred_contact_method",
            "contact_method_display",
            "can_approve_change_orders",
            "can_view_financials",
            "can_create_tasks",
            "can_approve_colors",
            "receive_daily_reports",
            "receive_invoice_notifications",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ClientContactListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for contact lists/dropdowns."""

    full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = ClientContact
        fields = ["id", "full_name", "organization", "organization_name", "role", "job_title"]


class ProjectSelectorSerializer(serializers.ModelSerializer):
    """Simplified project data for project selector dropdown."""

    billing_organization = ClientOrganizationListSerializer(read_only=True)
    project_lead = ClientContactListSerializer(read_only=True)
    billing_entity = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "project_code",
            "client",
            "address",
            "billing_organization",
            "project_lead",
            "billing_entity",
            "start_date",
            "end_date",
        ]

    def get_billing_entity(self, obj):
        """Return the billing entity for this project."""
        return obj.get_billing_entity()


class ProjectWithClientsSerializer(serializers.ModelSerializer):
    """Project serializer with full client/contact relationships."""

    billing_organization = ClientOrganizationSerializer(read_only=True)
    project_lead = ClientContactSerializer(read_only=True)
    observers = ClientContactListSerializer(many=True, read_only=True)
    billing_entity = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "project_code",
            "client",
            "address",
            "description",
            "start_date",
            "end_date",
            "billing_organization",
            "project_lead",
            "observers",
            "billing_entity",
            "budget_total",
            "budget_labor",
            "budget_materials",
            "budget_other",
            "total_income",
            "total_expenses",
            "created_at",
        ]
        read_only_fields = ["created_at", "project_code"]

    def get_billing_entity(self, obj):
        """Return the billing entity for this project."""
        return obj.get_billing_entity()
