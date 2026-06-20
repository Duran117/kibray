"""Profit-share module models (Phase 2).

Greenfield, additive models for the per-project profit distribution system.
They live in their own module and are re-exported from ``core.models`` so the
rest of the app can do ``from core.models import RateConfig`` etc.

Design goals (per owner): clarity & simplicity, no coupling to payroll, and
balances that MAY go negative (advances / real end-of-project losses) without
ever corrupting an employee's payroll data.

Money flow recap:
  net = contract − materials − other_labor − overhead − direction_overhead
        − callback_reserve − bad_debt_reserve
  director_share = net × director_split_pct           (the owner)
  partner_pool   = net − director_share                (split among active socios)
  direction_overhead → DIRECTOR or BUSINESS account (configurable, default BUSINESS)
"""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class RateConfig(models.Model):
    """Singleton configuration of all profit-share rates and the cutoff date.

    Only ONE row exists (pk=1). Use :meth:`load` to fetch/create it. All
    percentages are stored as whole numbers (e.g. 8.00 means 8%).
    """

    DESTINATION_DIRECTOR = "DIRECTOR"
    DESTINATION_BUSINESS = "BUSINESS"
    DESTINATION_CHOICES = [
        (DESTINATION_DIRECTOR, "Director"),
        (DESTINATION_BUSINESS, "Business"),
    ]

    company_overhead_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("8.00"),
        help_text="Company overhead % of contract (raise to ~9 if projected sales < $350k).",
    )
    direction_overhead_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("8.00"),
        help_text="Direction overhead % of contract (shown neutrally as 'overhead').",
    )
    callback_reserve_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("5.00"),
        help_text="Callback/warranty reserve % of contract.",
    )
    bad_debt_reserve_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.50"),
        help_text="Bad-debt reserve % of contract.",
    )
    director_split_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("40.00"),
        help_text="Director (owner) share of net. Remainder splits among active socios.",
    )
    direction_overhead_destination = models.CharField(
        max_length=10, choices=DESTINATION_CHOICES, default=DESTINATION_BUSINESS,
        help_text="Where the direction overhead accrues: the DIRECTOR account or the BUSINESS account.",
    )
    profit_share_start_date = models.DateField(
        help_text="Cutoff date. Only client payments on/after this date, on included "
                  "projects, generate accrual. Older payments never accrue.",
    )
    planning_annual_revenue = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Optional projected annual revenue used for planning (informational).",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rate Configuration"
        verbose_name_plural = "Rate Configuration"

    def __str__(self):
        return f"RateConfig (start {self.profit_share_start_date}, director {self.director_split_pct}%)"

    def save(self, *args, **kwargs):
        # Enforce singleton: always pk=1.
        self.pk = 1
        if self.profit_share_start_date is None:
            self.profit_share_start_date = timezone.localdate()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        for field in [
            "company_overhead_pct", "direction_overhead_pct",
            "callback_reserve_pct", "bad_debt_reserve_pct", "director_split_pct",
        ]:
            val = getattr(self, field)
            if val is not None and (val < 0 or val > 100):
                raise ValidationError({field: "Percentage must be between 0 and 100."})

    @classmethod
    def load(cls) -> "RateConfig":
        """Return the singleton row, creating it with defaults if missing.

        On first creation, the cutoff date defaults to *today* (the owner can
        edit it later from the director panel).
        """
        obj, _created = cls.objects.get_or_create(
            pk=1,
            defaults={"profit_share_start_date": timezone.localdate()},
        )
        return obj


class PartnerAccount(models.Model):
    """A ledger account: one per active socio, plus a single BUSINESS account.

    ``balance`` MAY be negative (advances / real end-of-project losses). This is
    completely independent from payroll; nothing here can mutate an employee's
    wage data.
    """

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="partner_account",
        help_text="The socio/director user. NULL for the business account.",
    )
    is_business = models.BooleanField(
        default=False,
        help_text="True for the single company 'caja' account (owner is NULL).",
    )
    is_active_socio = models.BooleanField(
        default=True,
        help_text="True if this partner participates in the current 60% pool split.",
    )
    balance = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00"),
        help_text="Current balance. CAN be negative (advance/loan or real loss).",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Partner Account"
        verbose_name_plural = "Partner Accounts"
        ordering = ["-is_business", "owner__first_name", "owner__last_name"]

    def __str__(self):
        if self.is_business:
            return "Business Account"
        if self.owner:
            full = self.owner.get_full_name() or self.owner.username
            return f"Partner: {full}"
        return f"PartnerAccount #{self.pk}"

    def clean(self):
        super().clean()
        if self.is_business and self.owner_id:
            raise ValidationError("The business account must not have an owner.")
        if not self.is_business and not self.owner_id:
            raise ValidationError("A non-business account requires an owner.")

    @classmethod
    def business(cls) -> "PartnerAccount":
        """Fetch/create the single business account."""
        obj, _ = cls.objects.get_or_create(
            is_business=True,
            defaults={"owner": None, "is_active_socio": False},
        )
        return obj

    @classmethod
    def for_partner(cls, user) -> "PartnerAccount":
        """Fetch/create the account for a given socio/director user."""
        obj, _ = cls.objects.get_or_create(
            owner=user,
            defaults={"is_business": False, "is_active_socio": True},
        )
        return obj

    @classmethod
    def director(cls):
        """Fetch/create the DIRECTOR account (the owner-role user's account).

        The director receives the 40% director_share and, when configured,
        the direction overhead. Identified by the single user with role
        'owner' (no hardcoded names). Returns ``None`` if no owner user
        exists yet. The director is NOT a pool socio, so is_active_socio
        defaults to False here.
        """
        from django.contrib.auth import get_user_model

        from core.access import ROLE_OWNER

        owner_user = (
            get_user_model()
            .objects.filter(profile__role=ROLE_OWNER)
            .order_by("id")
            .first()
        )
        if owner_user is None:
            return None
        obj, _ = cls.objects.get_or_create(
            owner=owner_user,
            defaults={"is_business": False, "is_active_socio": False},
        )
        return obj


class LedgerEntry(models.Model):
    """Immutable movement on a :class:`PartnerAccount`.

    ``amount`` is signed: positive accrues earnings; negative records an advance
    or a downward adjustment. ``running_balance`` is the account balance right
    after this entry (snapshot for transparent statements).
    """

    TYPE_ACCRUAL = "ACCRUAL"
    TYPE_ADVANCE = "ADVANCE"
    TYPE_ADJUSTMENT = "ADJUSTMENT"
    TYPE_CHOICES = [
        (TYPE_ACCRUAL, "Accrual"),
        (TYPE_ADVANCE, "Advance"),
        (TYPE_ADJUSTMENT, "Adjustment"),
    ]

    account = models.ForeignKey(
        PartnerAccount, on_delete=models.CASCADE, related_name="entries"
    )
    project = models.ForeignKey(
        "Project", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="ledger_entries",
        help_text="Source project for accruals; NULL for advances/adjustments.",
    )
    type = models.CharField(max_length=12, choices=TYPE_CHOICES)
    amount = models.DecimalField(
        max_digits=14, decimal_places=2,
        help_text="Signed: + accrues earnings, − advance/adjustment.",
    )
    date = models.DateTimeField(default=timezone.now)
    note = models.CharField(max_length=255, blank=True)
    running_balance = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00"),
        help_text="Account balance immediately after this entry.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ledger Entry"
        verbose_name_plural = "Ledger Entries"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["account", "date"]),
            models.Index(fields=["project", "type"]),
        ]

    def __str__(self):
        sign = "+" if self.amount >= 0 else ""
        return f"{self.account} | {self.type} {sign}{self.amount} | {self.date:%Y-%m-%d}"


class ProjectAccrualState(models.Model):
    """How much has already been accrued for a given (project, account) pair.

    This is the idempotency anchor: accrual recomputes a *target* and only posts
    the delta vs. ``accrued`` here, so re-running on the same payments never
    double-counts.
    """

    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="accrual_states"
    )
    account = models.ForeignKey(
        PartnerAccount, on_delete=models.CASCADE, related_name="accrual_states"
    )
    accrued = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00"),
        help_text="Cumulative amount already posted to this account for this project.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Project Accrual State"
        verbose_name_plural = "Project Accrual States"
        unique_together = ("project", "account")
        indexes = [models.Index(fields=["project", "account"])]

    def __str__(self):
        return f"{self.project} / {self.account}: accrued {self.accrued}"
