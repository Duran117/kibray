"""
PWA Push Notification Models
Stores push notification subscriptions for Progressive Web App
"""
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class PushSubscription(models.Model):
    """
    Store push notification subscription details for PWA
    Each user can have multiple subscriptions (different devices/browsers)
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
        verbose_name=_("User"),
    )
    endpoint = models.URLField(
        max_length=500,
        verbose_name=_("Push Endpoint"),
        help_text=_("Unique push notification endpoint from browser"),
    )
    p256dh = models.CharField(
        max_length=255,
        verbose_name=_("P256DH Key"),
        help_text=_("Public key for encrypting push messages"),
    )
    auth = models.CharField(
        max_length=255,
        verbose_name=_("Auth Secret"),
        help_text=_("Authentication secret for push messages"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Push Subscription")
        verbose_name_plural = _("Push Subscriptions")
        unique_together = ["user", "endpoint"]
        ordering = ["-created_at"]
        app_label = 'core'

    def __str__(self):
        return f"{self.user.username} - {self.endpoint[:50]}..."
