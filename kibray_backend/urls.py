from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
from core import views
from django.shortcuts import redirect

def root_redirect(request):
    return redirect('dashboard')

urlpatterns = [
    # Home redirects to dashboard
    path('', root_redirect, name='home'),

    # Dashboard view
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # Django admin
    path('admin/', admin.site.urls),

    # Project PDF report
    path('project/<int:project_id>/pdf/', views.project_pdf_view, name='project_pdf'),

    # Add Event (Schedule)
    path('schedule/add/', views.schedule_create_view, name='schedule_create'),

    # Add Expense
    path('expense/add/', views.expense_create_view, name='expense_create'),

    # Add Income
    path('income/add/', views.income_create_view, name='income_create'),

    # Add Time Entry (registro de horas)
    path('timeentry/add/', views.timeentry_create_view, name='timeentry_create'),


    # ----------- CLIENTE: Vista de proyecto y formularios -----------
    path('proyecto/<int:project_id>/', views.client_project_view, name='client_project_view'),
    path('proyecto/<int:project_id>/agregar_tarea/', views.agregar_tarea, name='agregar_tarea'),
    path('proyecto/<int:project_id>/agregar_comentario/', views.agregar_comentario, name='agregar_comentario'),

    # Change Order Detail
    path('changeorder/<int:changeorder_id>/', views.changeorder_detail_view, name='changeorder_detail'),

    # Add Change Order
    path('changeorder/add/', views.changeorder_create_view, name='changeorder_create'),

    # Change Order Board
    path('changeorders/board/', views.changeorder_board_view, name='changeorder_board'),

    # Payroll summary
    path('payroll/summary/', views.payroll_summary_view, name='payroll_summary'),
]

# Static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)