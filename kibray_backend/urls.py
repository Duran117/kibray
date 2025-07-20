from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('', views.dashboard_view, name='home'),  # Acceso a dashboard desde /
    path('admin/', admin.site.urls),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]

# Solo en modo desarrollo: servir archivos de media (subidas de usuario)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
