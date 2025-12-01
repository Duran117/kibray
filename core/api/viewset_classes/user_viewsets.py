"""
User-related viewsets for the Kibray API
"""
from django.contrib.auth.models import User
from django.core.mail import send_mail
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from core.api.serializer_classes import (
    UserListSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    CurrentUserSerializer,
)
from core.models import Profile


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for users - read-only for regular users, full CRUD for admins
    """
    queryset = User.objects.select_related('profile').prefetch_related(
        'groups', 'user_permissions'
    ).filter(is_active=True)
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active', 'is_staff']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['username', 'date_joined', 'last_login']
    ordering = ['username']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        elif self.action == 'me':
            return CurrentUserSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserDetailSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user details"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def invite(self, request):
        """Invite a new user"""
        email = request.data.get('email')
        role = request.data.get('role', 'user')
        
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'User with this email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create inactive user
        username = email.split('@')[0]
        user = User.objects.create_user(
            username=username,
            email=email,
            is_active=False
        )
        
        # Create profile
        Profile.objects.create(user=user, role=role)
        
        # Send invitation email
        try:
            send_mail(
                'Invitation to Kibray',
                f'You have been invited to join Kibray. Please check your email for activation instructions.',
                'noreply@kibray.com',
                [email],
                fail_silently=False,
            )
        except Exception as e:
            # Log error but don't fail the request
            pass
        
        return Response(
            {'message': 'Invitation sent successfully', 'user_id': user.id},
            status=status.HTTP_201_CREATED
        )
