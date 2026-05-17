"""Contract sharing UX upgrade.

Adds three things to make sending a contract to a (typically elderly,
non-tech-savvy) client one-click easy and tamper-proof:

1. ``Contract.signing_link_active`` — defaults to True; flipped to
   False the moment the client signs. The public /contracts/<token>/
   page checks this and short-circuits to a "Contract signed — closed"
   notice. Prevents accidental duplicate or modified signatures.

2. ``Contract.last_sent_to_email`` + ``Contract.last_sent_at`` —
   bookkeeping for the new "Send by Email" admin button so staff can
   see *who* the link was emailed to and *when*.

3. ``ContractAttachment`` — reference files (proposal PDF, plans,
   inspiration photos) attached to a contract and rendered on the
   client's public signing page so they have full context before
   signing. One contract → many attachments.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0183_hoa_resident_portal"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="contract",
            name="signing_link_active",
            field=models.BooleanField(
                default=True,
                help_text=(
                    "If False, the public signing link returns a "
                    "'closed' page and the signature form is hidden."
                ),
            ),
        ),
        migrations.AddField(
            model_name="contract",
            name="last_sent_to_email",
            field=models.EmailField(
                blank=True,
                max_length=254,
                help_text="Last email address the signing link was sent to.",
            ),
        ),
        migrations.AddField(
            model_name="contract",
            name="last_sent_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="When the signing link was last emailed.",
            ),
        ),
        migrations.CreateModel(
            name="ContractAttachment",
            fields=[
                ("id", models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name="ID",
                )),
                ("file", models.FileField(
                    upload_to="contracts/attachments/%Y/%m/",
                )),
                ("label", models.CharField(
                    blank=True,
                    max_length=200,
                    help_text=(
                        "Friendly name shown to the client "
                        "(e.g. 'Original Proposal')."
                    ),
                )),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("contract", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="attachments",
                    to="core.contract",
                )),
                ("uploaded_by", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="uploaded_contract_attachments",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "verbose_name": "Contract Attachment",
                "verbose_name_plural": "Contract Attachments",
                "ordering": ["-uploaded_at"],
            },
        ),
        # Backfill: any contract already signed should have its
        # public link closed too (so old shared URLs become inert).
        migrations.RunSQL(
            sql=(
                "UPDATE core_contract "
                "SET signing_link_active = FALSE "
                "WHERE client_signed_at IS NOT NULL;"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
