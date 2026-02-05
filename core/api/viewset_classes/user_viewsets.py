"""
User-related viewsets for the Kibray API
"""

import contextlib

from django.contrib.auth.models import User
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from core.api.serializer_classes import (
    CurrentUserSerializer,
    UserCreateSerializer,
    UserDetailSerializer,
    UserListSerializer,
    UserUpdateSerializer,
)
from core.models import Profile


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for users - read-only for regular users, full CRUD for admins
    """

    queryset = (
        User.objects.select_related("profile")
        .prefetch_related("groups", "user_permissions")
        .filter(is_active=True)
    )
    permission_classes = [IsAuthenticated]
    filterset_fields = ["is_active", "is_staff"]
    search_fields = ["username", "first_name", "last_name", "email"]
    ordering_fields = ["username", "date_joined", "last_login"]
    ordering = ["username"]

    def get_serializer_class(self):
        if self.action == "list":
            return UserListSerializer
        elif self.action == "retrieve":
            return UserDetailSerializer
        elif self.action == "me":
            return CurrentUserSerializer
        elif self.action == "create":
            return UserCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserDetailSerializer

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Get current user details"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["patch"])
    def preferred_language(self, request):
        """Update current user's preferred UI language (en or es)."""
        lang = (request.data.get("preferred_language") or "").split("-")[0]
        if lang not in ["en", "es"]:
            return Response({"error": "Invalid language"}, status=status.HTTP_400_BAD_REQUEST)

        profile, _ = Profile.objects.get_or_create(user=request.user, defaults={"role": "employee"})
        profile.language = lang
        profile.save(update_fields=["language"])
        return Response({"message": "Language updated", "preferred_language": lang})

    @action(detail=False, methods=["post"], permission_classes=[IsAdminUser])
    def invite(self, request):
        """Invite a new user"""
        email = request.data.get("email")
        role = request.data.get("role", "user")

        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Create inactive user
        username = email.split("@")[0]
        user = User.objects.create_user(username=username, email=email, is_active=False)

        # Create profile
        Profile.objects.create(user=user, role=role)

        # Send invitation email
        with contextlib.suppress(Exception):
            from core.services.email_service import KibrayEmailService
            KibrayEmailService.send_simple_notification(
                to_emails=[email],
                subject="Invitation to Kibray Painting",
                message="You have been invited to join Kibray Painting. Please check your email for activation instructions.",
            )

        return Response(
            {"message": "Invitation sent successfully", "user_id": user.id},
            status=status.HTTP_201_CREATED,
        )
