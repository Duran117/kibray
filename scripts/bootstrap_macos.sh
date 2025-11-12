#!/usr/bin/env bash
set -e

echo "[1/8] Comprobando Xcode Command Line Tools..."
if ! xcode-select -p >/dev/null 2>&1; then
  echo "Instalando CLT (aparecerá un popup)...";
  xcode-select --install || true
  echo "Espera a que termine la instalación y vuelve a correr este script si falla aquí."
fi

echo "[2/8] Comprobando Homebrew..."
if ! command -v brew >/dev/null 2>&1; then
  echo "Instalando Homebrew...";
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$($(brew --prefix)/bin/brew shellenv)"
fi

# Python
PY_VERSION="3.11"
echo "[3/8] Instalando Python ${PY_VERSION} (si falta)..."
brew list python@${PY_VERSION} >/dev/null 2>&1 || brew install python@${PY_VERSION}

# Node via nvm (preferido)
echo "[4/8] Instalando nvm (si falta)..."
if ! command -v nvm >/dev/null 2>&1; then
  brew install nvm
  mkdir -p ~/.nvm
  if ! grep -q 'NVM_DIR' ~/.zshrc 2>/dev/null; then
    {
      echo 'export NVM_DIR="$HOME/.nvm"'
      echo '[ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && . "/opt/homebrew/opt/nvm/nvm.sh"'
      echo '[ -s "/opt/homebrew/opt/nvm/etc/bash_completion" ] && . "/opt/homebrew/opt/nvm/etc/bash_completion"'
    } >> ~/.zshrc
  fi
  # shellcheck disable=SC1091
  source ~/.zshrc || true
fi

if command -v nvm >/dev/null 2>&1; then
  echo "[4.1] Instalando Node LTS via nvm..."
  nvm install --lts
else
  echo "nvm no disponible, instalando node LTS directo con brew..."
  brew list node >/dev/null 2>&1 || brew install node
fi

echo "[5/8] Creando entorno virtual Python..."
cd "$(dirname "$0")/.."  # mover a raíz del repo
if [ ! -d .venv ]; then
  python${PY_VERSION} -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

pip install --upgrade pip

if [ -f requirements.txt ]; then
  echo "[6/8] Instalando dependencias Python..."
  pip install -r requirements.txt
else
  echo "requirements.txt no encontrado";
fi

echo "[7/8] Migraciones Django..."
python manage.py migrate

if [ -f seed_schedule_demo.py ]; then
  echo "(Opcional) Sembrando datos demo Gantt..."
  python manage.py shell -c "exec(open('seed_schedule_demo.py').read())" || echo "Seed opcional omitido"
fi

echo "[8/8] Configurando frontend..."
if [ -d frontend ]; then
  cd frontend
  if [ -f package.json ]; then
    npm install
    echo "Puedes iniciar el dev server con: npm run dev"
  fi
fi

echo "Listo ✅\nComandos útiles:\n  source .venv/bin/activate\n  python manage.py runserver 0.0.0.0:8000\n  (en otra terminal) cd frontend && npm run dev\nAbrir: http://localhost:8000/projects/1/schedule/gantt/"
