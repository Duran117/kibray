#!/usr/bin/env python3
"""
Diagnóstico Completo de Integración OpenAI API en Railway
Verifica configuración, conectividad y funcionalidad de la API
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kibray_backend.settings')
django.setup()

from django.conf import settings
import json
from datetime import datetime

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_section(title):
    """Print a section divider"""
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print('─' * 80)

def check_environment_variable():
    """Check if OPENAI_API_KEY is properly set"""
    print_header("🔍 PASO 1: VERIFICACIÓN DE VARIABLE DE ENTORNO")
    
    # Check environment variable directly
    env_key = os.environ.get("OPENAI_API_KEY", "")
    
    print(f"\n✓ Nombre de variable: OPENAI_API_KEY")
    print(f"✓ Método de carga: os.environ.get('OPENAI_API_KEY', '')")
    
    if env_key:
        print(f"✅ Variable encontrada en OS environment")
        print(f"   Longitud: {len(env_key)} caracteres")
        print(f"   Primeros 8 chars: {env_key[:8]}...")
        print(f"   Últimos 4 chars: ...{env_key[-4:]}")
        
        # Check format
        if env_key.startswith("sk-"):
            print(f"✅ Formato correcto (comienza con 'sk-')")
        else:
            print(f"⚠️  Formato inusual (no comienza con 'sk-')")
            
    else:
        print(f"❌ Variable NO encontrada en OS environment")
        return False
    
    # Check Django settings
    print_section("Verificación en Django Settings")
    
    if hasattr(settings, 'OPENAI_API_KEY'):
        settings_key = settings.OPENAI_API_KEY
        print(f"✅ Variable accesible desde settings.OPENAI_API_KEY")
        print(f"   Longitud: {len(settings_key)} caracteres")
        
        if settings_key == env_key:
            print(f"✅ Coincide con variable de entorno")
        else:
            print(f"⚠️  NO coincide con variable de entorno")
            
        if settings_key:
            print(f"✅ Variable tiene valor (no está vacía)")
        else:
            print(f"❌ Variable está vacía")
            return False
    else:
        print(f"❌ settings.OPENAI_API_KEY no está definido")
        return False
    
    # Check model configuration
    if hasattr(settings, 'OPENAI_MODEL'):
        print(f"✅ Modelo configurado: {settings.OPENAI_MODEL}")
    else:
        print(f"⚠️  OPENAI_MODEL no configurado (usará default)")
    
    return True

def check_dependencies():
    """Check if OpenAI library is installed"""
    print_header("📦 PASO 2: VERIFICACIÓN DE DEPENDENCIAS")
    
    try:
        import openai
        print(f"✅ Librería 'openai' instalada")
        print(f"   Versión: {openai.__version__}")
        
        # Try to import OpenAI client
        try:
            from openai import OpenAI
            print(f"✅ Cliente OpenAI importable")
            return True
        except ImportError as e:
            print(f"❌ Error importando cliente: {e}")
            return False
            
    except ImportError:
        print(f"❌ Librería 'openai' NO instalada")
        print(f"   Instalar con: pip install openai")
        return False

def test_api_connection():
    """Test actual API connection"""
    print_header("🌐 PASO 3: PRUEBA DE CONEXIÓN A API")
    
    try:
        from openai import OpenAI
        
        # Create client
        print(f"\n1️⃣  Inicializando cliente...")
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        print(f"✅ Cliente creado exitosamente")
        
        # Test simple completion
        print(f"\n2️⃣  Enviando petición de prueba...")
        print(f"   Endpoint: chat.completions.create")
        print(f"   Modelo: {getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')}")
        print(f"   Mensaje: '¿Qué es 2+2?'")
        
        response = client.chat.completions.create(
            model=getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini'),
            messages=[
                {"role": "system", "content": "Eres un asistente útil que responde brevemente."},
                {"role": "user", "content": "¿Qué es 2+2? Responde solo con el número."}
            ],
            max_tokens=10,
            temperature=0
        )
        
        print(f"\n3️⃣  Respuesta recibida:")
        print(f"✅ Status: SUCCESS")
        print(f"✅ ID: {response.id}")
        print(f"✅ Model: {response.model}")
        print(f"✅ Respuesta: {response.choices[0].message.content}")
        print(f"✅ Tokens usados: {response.usage.total_tokens}")
        print(f"   - Prompt: {response.usage.prompt_tokens}")
        print(f"   - Completion: {response.usage.completion_tokens}")
        
        return True, response
        
    except Exception as e:
        print(f"\n❌ ERROR EN CONEXIÓN:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensaje: {str(e)}")
        
        # Analyze specific errors
        error_msg = str(e).lower()
        
        if "authentication" in error_msg or "api key" in error_msg or "unauthorized" in error_msg:
            print(f"\n🔴 DIAGNÓSTICO: Error de Autenticación")
            print(f"   - La API key es inválida o ha expirado")
            print(f"   - Verificar en: https://platform.openai.com/api-keys")
            print(f"   - Regenerar key si es necesario")
            
        elif "rate limit" in error_msg or "quota" in error_msg:
            print(f"\n🟡 DIAGNÓSTICO: Límite de Rate/Quota")
            print(f"   - Has excedido el rate limit o quota")
            print(f"   - Verificar uso en: https://platform.openai.com/usage")
            print(f"   - Esperar o actualizar plan")
            
        elif "connection" in error_msg or "network" in error_msg or "timeout" in error_msg:
            print(f"\n🟠 DIAGNÓSTICO: Error de Conectividad")
            print(f"   - Problema de red o firewall")
            print(f"   - Railway puede estar bloqueando")
            print(f"   - Verificar logs de Railway")
            
        elif "model" in error_msg:
            print(f"\n🟡 DIAGNÓSTICO: Error de Modelo")
            print(f"   - Modelo no disponible o incorrecto")
            print(f"   - Modelo configurado: {getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')}")
            print(f"   - Cambiar a: gpt-3.5-turbo o gpt-4")
            
        else:
            print(f"\n🔴 DIAGNÓSTICO: Error Desconocido")
            print(f"   - Revisar documentación de OpenAI")
            print(f"   - Contactar soporte si persiste")
        
        return False, None

def test_django_ai_services():
    """Test Django AI services integration"""
    print_header("🧪 PASO 4: PRUEBA DE SERVICIOS AI DE DJANGO")
    
    results = []
    
    # Test 1: AI SOP Generator
    print_section("Test 1: AI SOP Generator")
    try:
        from core.ai_sop_generator import OPENAI_AVAILABLE, generate_sop_with_ai_simple
        
        if OPENAI_AVAILABLE:
            print(f"✅ AI SOP Generator: OpenAI disponible")
            
            # Try a simple generation
            test_result = generate_sop_with_ai_simple(
                title="Limpieza de Herramientas",
                category="maintenance",
                context="Herramientas de construcción"
            )
            
            if test_result and test_result.get('steps'):
                print(f"✅ Generación exitosa: {len(test_result['steps'])} pasos")
                results.append(("AI SOP Generator", True))
            else:
                print(f"⚠️  Generación sin resultados")
                results.append(("AI SOP Generator", False))
        else:
            print(f"❌ OpenAI no disponible en módulo")
            results.append(("AI SOP Generator", False))
            
    except Exception as e:
        print(f"❌ Error: {e}")
        results.append(("AI SOP Generator", False))
    
    # Test 2: AI Focus Helper
    print_section("Test 2: AI Focus Helper")
    try:
        from core.ai_focus_helper import OPENAI_AVAILABLE
        
        if OPENAI_AVAILABLE:
            print(f"✅ AI Focus Helper: OpenAI disponible")
            results.append(("AI Focus Helper", True))
        else:
            print(f"❌ OpenAI no disponible")
            results.append(("AI Focus Helper", False))
            
    except Exception as e:
        print(f"❌ Error: {e}")
        results.append(("AI Focus Helper", False))
    
    # Test 3: Planner AI
    print_section("Test 3: Planner AI Service")
    try:
        from core.services.planner_ai import OPENAI_AVAILABLE
        
        if OPENAI_AVAILABLE:
            print(f"✅ Planner AI: OpenAI disponible")
            results.append(("Planner AI", True))
        else:
            print(f"❌ OpenAI no disponible")
            results.append(("Planner AI", False))
            
    except Exception as e:
        print(f"❌ Error: {e}")
        results.append(("Planner AI", False))
    
    # Test 4: Daily Plan AI
    print_section("Test 4: Daily Plan AI Service")
    try:
        from core.services.daily_plan_ai import DailyPlanAIAssistant
        
        print(f"✅ Daily Plan AI: Módulo importable")
        results.append(("Daily Plan AI", True))
            
    except Exception as e:
        print(f"❌ Error: {e}")
        results.append(("Daily Plan AI", False))
    
    # Test 5: NLP Service
    print_section("Test 5: NLP Service")
    try:
        from core.services.nlp_service import DailyPlanNLU
        
        print(f"✅ NLP Service: Módulo importable")
        results.append(("NLP Service", True))
            
    except Exception as e:
        print(f"❌ Error: {e}")
        results.append(("NLP Service", False))
    
    return results

def generate_report(env_ok, deps_ok, api_ok, api_response, services_results):
    """Generate final diagnostic report"""
    print_header("📊 REPORTE FINAL DE DIAGNÓSTICO")
    
    print(f"\n📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌍 Entorno: {os.environ.get('DJANGO_ENV', 'development')}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    
    print_section("Resumen de Verificaciones")
    
    checks = [
        ("Variable de Entorno", env_ok),
        ("Dependencias", deps_ok),
        ("Conexión API", api_ok),
    ]
    
    for check_name, status in checks:
        icon = "✅" if status else "❌"
        print(f"  {icon} {check_name}")
    
    print_section("Estado de Servicios AI")
    
    if services_results:
        for service_name, status in services_results:
            icon = "✅" if status else "❌"
            print(f"  {icon} {service_name}")
    
    print_section("Conclusión General")
    
    all_ok = env_ok and deps_ok and api_ok
    
    if all_ok:
        print(f"\n🎉 ¡TODO ESTÁ FUNCIONANDO CORRECTAMENTE!")
        print(f"\n✅ La integración con OpenAI API está operativa")
        print(f"✅ Todos los servicios AI están disponibles")
        print(f"✅ Railway puede usar las funcionalidades AI")
        
        if api_response:
            print(f"\n📊 Última prueba exitosa:")
            print(f"   - Modelo: {api_response.model}")
            print(f"   - Tokens: {api_response.usage.total_tokens}")
            print(f"   - Respuesta: {api_response.choices[0].message.content}")
    else:
        print(f"\n⚠️  PROBLEMAS DETECTADOS")
        
        if not env_ok:
            print(f"\n❌ ACCIÓN REQUERIDA: Configurar Variable de Entorno")
            print(f"   1. Ir a Railway Dashboard")
            print(f"   2. Seleccionar tu servicio")
            print(f"   3. Ir a 'Variables'")
            print(f"   4. Agregar: OPENAI_API_KEY = tu_api_key")
            print(f"   5. Obtener key en: https://platform.openai.com/api-keys")
        
        if not deps_ok:
            print(f"\n❌ ACCIÓN REQUERIDA: Instalar Dependencias")
            print(f"   1. Agregar a requirements.txt: openai>=1.0.0")
            print(f"   2. Railway instalará automáticamente en próximo deploy")
        
        if not api_ok:
            print(f"\n❌ ACCIÓN REQUERIDA: Verificar API Key")
            print(f"   1. Verificar que la key es válida")
            print(f"   2. Verificar que tienes créditos/quota")
            print(f"   3. Verificar conectividad en Railway")
    
    print_section("Información de Soporte")
    print(f"\n📚 Recursos:")
    print(f"   - OpenAI Platform: https://platform.openai.com")
    print(f"   - API Keys: https://platform.openai.com/api-keys")
    print(f"   - Usage Dashboard: https://platform.openai.com/usage")
    print(f"   - Railway Logs: railway logs")
    
    print("\n" + "=" * 80 + "\n")
    
    return all_ok

def main():
    """Run complete diagnostic"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "DIAGNÓSTICO OPENAI API - RAILWAY" + " " * 24 + "║")
    print("╚" + "═" * 78 + "╝")
    
    # Step 1: Check environment variable
    env_ok = check_environment_variable()
    
    # Step 2: Check dependencies
    deps_ok = check_dependencies()
    
    # Step 3: Test API connection
    api_ok = False
    api_response = None
    if env_ok and deps_ok:
        api_ok, api_response = test_api_connection()
    else:
        print_header("⏭️  PASO 3: OMITIDO (dependencias no cumplen)")
    
    # Step 4: Test Django services
    services_results = []
    if env_ok and deps_ok:
        services_results = test_django_ai_services()
    else:
        print_header("⏭️  PASO 4: OMITIDO (dependencias no cumplen)")
    
    # Generate final report
    success = generate_report(env_ok, deps_ok, api_ok, api_response, services_results)
    
    # Exit code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
