from django.contrib import admin
from django.urls import path
from core.views import home, resumen_proyectos, public_schedule_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),  # ← Esta línea muestra la página principal
    path('resumen/', resumen_proyectos, name='resumen_proyectos'),
    path('schedule/', public_schedule_view, name='public_schedule'),
]