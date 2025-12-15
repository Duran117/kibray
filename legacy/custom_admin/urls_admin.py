"""
URLs para el panel administrativo avanzado
"""

from django.urls import path

# Admin panel views (lightweight wrappers)
from . import views_admin

urlpatterns = [
    # Dashboard principal
    path("", views_admin.admin_dashboard_main, name="admin_panel_main"),
    # Gestión de usuarios
    path("users/", views_admin.admin_users_list, name="admin_users_list"),
    path("users/create/", views_admin.admin_user_create, name="admin_user_create"),
    path("users/<int:user_id>/", views_admin.admin_user_detail, name="admin_user_detail"),
    path("users/<int:user_id>/delete/", views_admin.admin_user_delete, name="admin_user_delete"),
    # Gestión de grupos y permisos
    path("groups/", views_admin.admin_groups_list, name="admin_groups_list"),
    path("groups/create/", views_admin.admin_group_create, name="admin_group_create"),
    path("groups/<int:group_id>/", views_admin.admin_group_detail, name="admin_group_detail"),
    # Gestión genérica de modelos
    path("models/<str:model_name>/", views_admin.admin_model_list, name="admin_model_list"),
    # Gestión de proyectos (CRUD)
    path("projects/create/", views_admin.admin_project_create, name="admin_project_create"),
    path("projects/<int:project_id>/edit/", views_admin.admin_project_edit, name="admin_project_edit"),
    path("projects/<int:project_id>/delete/", views_admin.admin_project_delete, name="admin_project_delete"),
    # Gestión de gastos (CRUD parcial)
    path("expenses/create/", views_admin.admin_expense_create, name="admin_expense_create"),
    path("expenses/<int:expense_id>/edit/", views_admin.admin_expense_edit, name="admin_expense_edit"),
    path("expenses/<int:expense_id>/delete/", views_admin.admin_expense_delete, name="admin_expense_delete"),
    # Gestión de ingresos (CRUD)
    path("incomes/create/", views_admin.admin_income_create, name="admin_income_create"),
    path("incomes/<int:income_id>/edit/", views_admin.admin_income_edit, name="admin_income_edit"),
    path("incomes/<int:income_id>/delete/", views_admin.admin_income_delete, name="admin_income_delete"),
    # Logs y auditoría
    path("logs/", views_admin.admin_activity_logs, name="admin_activity_logs"),
]
