#!/bin/bash

# Detener cualquier servidor Django corriendo
pkill -f "python.*runserver" 2>/dev/null

# Esperar un momento
sleep 1

# Limpiar puerto 8000
lsof -ti :8000 | xargs kill -9 2>/dev/null

# Ir al directorio correcto
cd /Users/jesus/Documents/kibray

# Activar virtualenv e iniciar servidor
source .venv/bin/activate

echo "🚀 Iniciando servidor Django en http://127.0.0.1:8000/"
echo "📝 Presiona Ctrl+C para detener"
echo ""

python manage.py runserver 8000
