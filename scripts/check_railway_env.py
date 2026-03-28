#!/usr/bin/env python3
"""
Railway Environment Variables Checker
Verifica que todas las variables necesarias estén configuradas
"""
import os
import sys


def check_env_vars():
    """Check if all required environment variables are set"""

    print("🔍 VERIFICANDO VARIABLES DE ENTORNO PARA RAILWAY\n")
    print("=" * 60)

    # Required variables
    required_vars = {
        "DJANGO_SECRET_KEY": "Clave secreta de Django",
        "DJANGO_ENV": "Entorno de ejecución (debe ser 'production')",
        "DATABASE_URL": "URL de PostgreSQL (creada por Railway)",
        "ALLOWED_HOSTS": "Dominios permitidos",
    }

    # Optional but recommended
    optional_vars = {
        "USE_S3": "Usar AWS S3 para archivos (False para local)",
        "CSRF_TRUSTED_ORIGINS": "Orígenes confiables para CSRF",
        "CORS_ALLOWED_ORIGINS": "Orígenes permitidos para CORS",
        "REDIS_URL": "URL de Redis para cache",
        "OPENAI_API_KEY": "API key de OpenAI (para features AI)",
    }

    # AWS S3 variables (needed if USE_S3=True)
    s3_vars = {
        "AWS_ACCESS_KEY_ID": "ID de acceso AWS",
        "AWS_SECRET_ACCESS_KEY": "Clave secreta AWS",
        "AWS_STORAGE_BUCKET_NAME": "Nombre del bucket S3",
        "AWS_S3_REGION_NAME": "Región del bucket S3",
    }

    missing_required = []
    missing_optional = []
    missing_s3 = []

    print("\n✅ VARIABLES REQUERIDAS:")
    print("-" * 60)
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "SECRET" in var or "PASSWORD" in var:
                display_value = value[:8] + "..." if len(value) > 8 else "***"
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: NO CONFIGURADA")
            missing_required.append((var, description))

    print("\n⚠️  VARIABLES OPCIONALES:")
    print("-" * 60)
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            if "SECRET" in var or "PASSWORD" in var or "KEY" in var:
                display_value = value[:8] + "..." if len(value) > 8 else "***"
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ⚠️  {var}: No configurada")
            missing_optional.append((var, description))

    # Check S3 if USE_S3 is True
    use_s3 = os.getenv("USE_S3", "True")
    if use_s3 == "True":
        print("\n☁️  VARIABLES AWS S3 (USE_S3=True):")
        print("-" * 60)
        for var, description in s3_vars.items():
            value = os.getenv(var)
            if value:
                if "SECRET" in var or "KEY" in var:
                    display_value = value[:8] + "..." if len(value) > 8 else "***"
                else:
                    display_value = value
                print(f"  ✅ {var}: {display_value}")
            else:
                print(f"  ❌ {var}: NO CONFIGURADA")
                missing_s3.append((var, description))

    print("\n" + "=" * 60)
    print("📋 RESUMEN:")
    print("=" * 60)

    if not missing_required and not missing_s3:
        print("✅ Todas las variables requeridas están configuradas!")
    else:
        print("❌ FALTAN VARIABLES REQUERIDAS:\n")

        if missing_required:
            print("🔴 Variables obligatorias faltantes:")
            for var, desc in missing_required:
                print(f"   - {var}: {desc}")

        if missing_s3:
            print("\n🟡 Variables AWS S3 faltantes (USE_S3=True):")
            for var, desc in missing_s3:
                print(f"   - {var}: {desc}")
            print("\n💡 SOLUCIÓN: Configura USE_S3=False en Railway si no usas AWS S3")

    if missing_optional:
        print("\n⚠️  Variables opcionales no configuradas:")
        for var, desc in missing_optional:
            print(f"   - {var}: {desc}")

    print("\n" + "=" * 60)

    # Recommendations
    if missing_s3 and use_s3 == "True":
        print("\n🚨 PROBLEMA DETECTADO:")
        print("   USE_S3=True pero faltan credenciales AWS")
        print("\n🔧 SOLUCIÓN RÁPIDA:")
        print("   En Railway → Variables → Agregar:")
        print("   Name:  USE_S3")
        print("   Value: False")
        print("\n   Esto usará almacenamiento local en lugar de S3")
        print("=" * 60)
        return False

    if missing_required:
        print("\n🚨 ACCIÓN REQUERIDA:")
        print("   Configura las variables obligatorias en Railway")
        print("   Railway → Tu servicio → Variables → + New Variable")
        print("=" * 60)
        return False

    return True

if __name__ == "__main__":
    # Set DJANGO_ENV to production for testing
    if not os.getenv("DJANGO_ENV"):
        os.environ["DJANGO_ENV"] = "production"

    try:
        success = check_env_vars()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
