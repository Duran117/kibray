from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    # Página principal (redirige al dashboard)
    path('', views.dashboard_view, name='home'),

    # Dashboard principal
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Autenticación
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Administración
    path('admin/', admin.site.urls),

    # PDF: Reporte por proyecto
    path('project/<int:project_id>/pdf/', views.project_pdf_view, name='project_pdf'),
]

# Servir archivos media en modo desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # (opcional) también servir archivos estáticos si usas STATICFILES_DIRS en desarrollo
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
