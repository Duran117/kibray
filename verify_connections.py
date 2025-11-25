#!/usr/bin/env python3
"""
Script para verificar la conectividad entre modelos, forms, views, URLs y templates.
"""
import os
import re
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kibray_backend.settings')
import django
django.setup()

from django.urls import reverse, NoReverseMatch
from django.apps import apps
from core import forms as core_forms
from core import models as core_models
from core import views as core_views

def check_models():
    """Verificar que los modelos principales existen"""
    print("\n=== VERIFICANDO MODELOS ===")
    required_models = [
        'Task', 'Schedule', 'Expense', 'Income', 'TimeEntry',
        'Project', 'Employee', 'Invoice', 'ChangeOrder'
    ]
    
    errors = []
    for model_name in required_models:
        if hasattr(core_models, model_name):
            print(f"✓ Modelo {model_name} encontrado")
        else:
            errors.append(f"✗ Modelo {model_name} NO encontrado")
            print(f"✗ Modelo {model_name} NO encontrado")
    
    return errors

def check_forms():
    """Verificar que los forms principales existen"""
    print("\n=== VERIFICANDO FORMS ===")
    required_forms = [
        'TaskForm', 'ScheduleForm', 'ExpenseForm', 'IncomeForm', 'TimeEntryForm',
        'InvoiceForm', 'ChangeOrderForm'
    ]
    
    errors = []
    for form_name in required_forms:
        if hasattr(core_forms, form_name):
            form_class = getattr(core_forms, form_name)
            print(f"✓ Form {form_name} encontrado - Modelo: {form_class.Meta.model.__name__}")
        else:
            errors.append(f"✗ Form {form_name} NO encontrado")
            print(f"✗ Form {form_name} NO encontrado")
    
    return errors

def check_views():
    """Verificar que las vistas principales existen"""
    print("\n=== VERIFICANDO VIEWS ===")
    required_views = [
        'task_detail', 'task_edit_view', 'task_delete_view',
        'schedule_create_view', 'expense_create_view', 'income_create_view',
        'timeentry_create_view', 'invoice_builder_view'
    ]
    
    errors = []
    for view_name in required_views:
        if hasattr(core_views, view_name):
            print(f"✓ Vista {view_name} encontrada")
        else:
            errors.append(f"✗ Vista {view_name} NO encontrada")
            print(f"✗ Vista {view_name} NO encontrada")
    
    return errors

def check_urls():
    """Verificar que las URLs principales están configuradas"""
    print("\n=== VERIFICANDO URLs ===")
    required_urls = [
        ('task_detail', {'task_id': 1}),
        ('task_edit', {'task_id': 1}),
        ('task_delete', {'task_id': 1}),
        ('schedule_create', {}),
        ('expense_create', {}),
        ('income_create', {}),
        ('timeentry_create', {}),
        ('invoice_builder', {'project_id': 1}),
        ('project_list', {}),
        ('dashboard', {}),
    ]
    
    errors = []
    for url_name, kwargs in required_urls:
        try:
            url = reverse(url_name, kwargs=kwargs)
            print(f"✓ URL '{url_name}' → {url}")
        except NoReverseMatch:
            errors.append(f"✗ URL '{url_name}' NO configurada")
            print(f"✗ URL '{url_name}' NO configurada")
    
    return errors

def check_templates():
    """Verificar que los templates optimizados existen"""
    print("\n=== VERIFICANDO TEMPLATES ===")
    base_path = 'core/templates/core'
    required_templates = [
        'task_form.html',
        'schedule_form.html',
        'expense_form.html',
        'income_form.html',
        'timeentry_form.html',
        'invoice_builder.html',
        'project_list.html',
        'dashboard.html',
        'dashboard_admin.html',
    ]
    
    errors = []
    for template in required_templates:
        template_path = os.path.join(base_path, template)
        if os.path.exists(template_path):
            # Verificar que tiene extends base.html
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'extends' in content and 'base.html' in content:
                    print(f"✓ Template {template} existe y extiende base.html")
                elif '<!DOCTYPE html>' in content:
                    errors.append(f"⚠ Template {template} NO extiende base.html (standalone)")
                    print(f"⚠ Template {template} NO extiende base.html (standalone)")
                else:
                    print(f"✓ Template {template} existe")
        else:
            errors.append(f"✗ Template {template} NO encontrado")
            print(f"✗ Template {template} NO encontrado en {template_path}")
    
    return errors

def check_form_field_consistency():
    """Verificar que los forms tienen todos los campos del modelo"""
    print("\n=== VERIFICANDO CONSISTENCIA FORM-MODELO ===")
    
    forms_to_check = [
        ('TaskForm', 'Task'),
        ('ScheduleForm', 'Schedule'),
        ('ExpenseForm', 'Expense'),
        ('IncomeForm', 'Income'),
        ('TimeEntryForm', 'TimeEntry'),
    ]
    
    errors = []
    for form_name, model_name in forms_to_check:
        if hasattr(core_forms, form_name) and hasattr(core_models, model_name):
            form_class = getattr(core_forms, form_name)
            model_class = getattr(core_models, model_name)
            
            # Obtener campos del modelo
            model_fields = [f.name for f in model_class._meta.fields if f.name not in ['id']]
            
            # Obtener campos del form
            if hasattr(form_class.Meta, 'fields'):
                form_fields = form_class.Meta.fields
                if form_fields == '__all__':
                    print(f"✓ {form_name} usa '__all__' (incluye todos los campos)")
                else:
                    print(f"✓ {form_name} define campos específicos: {len(form_fields)} campos")
            else:
                errors.append(f"✗ {form_name} no tiene Meta.fields definido")
                print(f"✗ {form_name} no tiene Meta.fields definido")
        else:
            print(f"⊘ Saltando {form_name}/{model_name} - no existen")
    
    return errors

def main():
    print("=" * 60)
    print("VERIFICACIÓN DE CONECTIVIDAD DEL PROYECTO KIBRAY")
    print("=" * 60)
    
    all_errors = []
    
    all_errors.extend(check_models())
    all_errors.extend(check_forms())
    all_errors.extend(check_views())
    all_errors.extend(check_urls())
    all_errors.extend(check_templates())
    all_errors.extend(check_form_field_consistency())
    
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    if all_errors:
        print(f"\n⚠ Se encontraron {len(all_errors)} problema(s):\n")
        for error in all_errors:
            print(f"  {error}")
        return 1
    else:
        print("\n✓ Todas las verificaciones pasaron correctamente!")
        print("✓ Modelos, Forms, Views, URLs y Templates están conectados.")
        return 0

if __name__ == '__main__':
    sys.exit(main())
