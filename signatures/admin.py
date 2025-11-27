from django.contrib import admin

from .models import Signature


@admin.register(Signature)
class SignatureAdmin(admin.ModelAdmin):
    list_display = ("id", "signer", "title", "signed_at")
    list_filter = ("signed_at", "signer")
    search_fields = ("title", "note", "signer__username", "signer__email")
