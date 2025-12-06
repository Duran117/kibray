# 🚨 ARREGLO RÁPIDO - Railway Deployment

## ⚡ FIX INMEDIATO

### 1️⃣ Configurar USE_S3=False en Railway

**Problema**: La app busca credenciales AWS S3 que no existen.

**Solución**:
1. Ve a Railway Dashboard → Tu proyecto `lovely-adventure`
2. Click en servicio `web`
3. Click en pestaña `Variables`
4. Click en `+ New Variable`
5. Agrega:
   ```
   Name:  USE_S3
   Value: False
   ```
6. Click `Add` y espera que se redeploy automáticamente

---

### 2️⃣ Verificar que DATABASE_URL existe

1. En la misma pestaña `Variables`
2. Busca la variable `DATABASE_URL`
3. Si NO existe:
   - Ve a tu proyecto → Click `+ New`
   - Selecciona `Database` → `Add PostgreSQL`
   - Railway creará `DATABASE_URL` automáticamente

---

### 3️⃣ Verificar DJANGO_SECRET_KEY

1. En `Variables`, busca `DJANGO_SECRET_KEY`
2. Si NO existe, agrega:
   ```
   Name:  DJANGO_SECRET_KEY
   Value: h9igi_p7yxtv2zh6!pbz@_py467lszlrp(a5)b90f@_-q!j@a#
   ```

---

### 4️⃣ Verificar DJANGO_ENV

1. En `Variables`, busca `DJANGO_ENV`
2. Si NO existe, agrega:
   ```
   Name:  DJANGO_ENV
   Value: production
   ```

---

### 5️⃣ Agregar ALLOWED_HOSTS con tu dominio

1. En Railway → Tu servicio → Pestaña `Settings`
2. Busca tu dominio (algo como: `lovely-adventure-production-xyz.up.railway.app`)
3. Copia ese dominio
4. Ve a `Variables` y agrega:
   ```
   Name:  ALLOWED_HOSTS
   Value: TU-DOMINIO-AQUI.up.railway.app,*.railway.app,localhost
   ```
   
   **Ejemplo**:
   ```
   Value: lovely-adventure-production-1a2b.up.railway.app,*.railway.app,localhost
   ```

---

## 🔄 Después de agregar las variables

Railway hará **redeploy automático**. Espera 2-3 minutos y verifica los logs nuevamente.

---

## 📋 Checklist Mínimo

- [ ] ✅ Variable `USE_S3` = `False`
- [ ] ✅ Variable `DATABASE_URL` existe (agregada por PostgreSQL)
- [ ] ✅ Variable `DJANGO_SECRET_KEY` configurada
- [ ] ✅ Variable `DJANGO_ENV` = `production`
- [ ] ✅ Variable `ALLOWED_HOSTS` con tu dominio de Railway

---

## 🆘 Si sigue fallando

Comparte el error exacto de los logs de Railway y te ayudo con el problema específico.
