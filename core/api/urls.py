from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    NotificationViewSet, ChatChannelViewSet, ChatMessageViewSet,
    TaskViewSet, DamageReportViewSet, FloorPlanViewSet, PlanPinViewSet,
    ColorSampleViewSet, ProjectViewSet, ScheduleCategoryViewSet, ScheduleItemViewSet,
    global_search, save_changeorder_photo_annotations, delete_changeorder_photo
)

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'chat/channels', ChatChannelViewSet, basename='chat-channel')
router.register(r'chat/messages', ChatMessageViewSet, basename='chat-message')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'damage-reports', DamageReportViewSet, basename='damage-report')
router.register(r'floor-plans', FloorPlanViewSet, basename='floor-plan')
router.register(r'plan-pins', PlanPinViewSet, basename='plan-pin')
router.register(r'color-samples', ColorSampleViewSet, basename='color-sample')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'schedule/categories', ScheduleCategoryViewSet, basename='schedule-category')
router.register(r'schedule/items', ScheduleItemViewSet, basename='schedule-item')

urlpatterns = [
    # JWT Auth
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Global Search
    path('search/', global_search, name='global_search'),
    # ChangeOrder Photos
    path('changeorder-photo/<int:photo_id>/annotations/', save_changeorder_photo_annotations, name='save_photo_annotations'),
    path('changeorder-photo/<int:photo_id>/delete/', delete_changeorder_photo, name='delete_photo'),
    # API routes
    path('', include(router.urls)),
]
