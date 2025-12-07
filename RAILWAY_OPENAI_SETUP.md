# 🚂 Guía de Configuración OpenAI API en Railway

**Fecha:** Diciembre 6, 2024  
**Propósito:** Configuración correcta de la integración OpenAI en Railway para funcionalidades AI

---

## 📋 RESUMEN EJECUTIVO

Esta guía te ayudará a configurar correctamente la **API Key de OpenAI** en Railway para que todas las funcionalidades de Inteligencia Artificial funcionen correctamente.

**Funcionalidades AI que requieren configuración:**
- ✨ AI SOP Generator (Generación automática de procedimientos)
- 🤖 Daily Plan AI Assistant (Asistente de planificación diaria)
- ⚡ Quick Planner AI (Planificador rápido con IA)
- 🎯 Strategic Planner AI (Planificador estratégico)
- 💬 NLP Command Processing (Procesamiento de lenguaje natural)

---

## 🔑 PASO 1: OBTENER API KEY DE OPENAI

### 1.1 Crear Cuenta en OpenAI

1. Ve a: https://platform.openai.com/signup
2. Registra tu cuenta con email
3. Verifica tu correo electrónico
4. Configura método de pago (tarjeta de crédito)

### 1.2 Generar API Key

1. Inicia sesión en: https://platform.openai.com
2. Ve a: https://platform.openai.com/api-keys
3. Click en "**+ Create new secret key**"
4. Dale un nombre descriptivo: `Kibray-Production`
5. Copia la key inmediatamente (comienza con `sk-`)
6. ⚠️ **IMPORTANTE**: La key solo se muestra UNA VEZ

**Formato esperado:** `sk-proj-abc123...xyz789` (51-55 caracteres)

### 1.3 Configurar Límites y Créditos

1. Ve a: https://platform.openai.com/usage
2. Revisa tu balance de créditos
3. Configura límites de uso mensuales (recomendado: $10-20/mes)
4. Habilita alertas de uso

---

## 🚂 PASO 2: CONFIGURAR VARIABLE EN RAILWAY

### 2.1 Acceder a tu Proyecto

1. Ve a: https://railway.app
2. Inicia sesión
3. Selecciona tu proyecto **Kibray**
4. Click en el servicio **Django** / **Backend**

### 2.2 Agregar Variable de Entorno

1. En el menú lateral, click en "**Variables**"
2. Click en "**+ New Variable**"
3. Agregar la variable:

```
Variable Name: OPENAI_API_KEY
Value: sk-proj-abc123...xyz789  (tu key real)
```

4. Click "**Add**"

### 2.3 (Opcional) Configurar Modelo

Si quieres usar un modelo específico diferente al default:

```
Variable Name: OPENAI_MODEL
Value: gpt-4o-mini  (o gpt-3.5-turbo, gpt-4, gpt-4-turbo)
```

**Modelos recomendados y costos:**
- `gpt-4o-mini`: **RECOMENDADO** - Más barato, muy bueno ($0.15 / 1M tokens)
- `gpt-3.5-turbo`: Barato pero menos capaz ($0.50 / 1M tokens)
- `gpt-4-turbo`: Más caro pero mejor ($10 / 1M tokens)
- `gpt-4`: Más caro ($30 / 1M tokens)

### 2.4 Redesplegar

Railway automáticamente redespleará tu aplicación al agregar variables.

1. Ve a "**Deployments**"
2. Espera a que el nuevo deployment termine
3. Verifica que el status sea "**Active**"

---

## ✅ PASO 3: VERIFICAR CONFIGURACIÓN

### 3.1 Método Automático (Recomendado)

Ejecuta el script de diagnóstico que creamos:

```bash
# En Railway (usando Railway CLI)
railway run python diagnose_openai_api.py

# O via SSH si tienes acceso
python diagnose_openai_api.py
```

**Salida esperada:**
```
✅ Variable de Entorno: OPENAI_API_KEY encontrada
✅ Dependencias: openai instalada
✅ Conexión API: SUCCESS
✅ Todos los servicios AI disponibles
```

### 3.2 Método Manual (Logs de Railway)

1. Ve a tu servicio en Railway
2. Click en "**Logs**"
3. Busca en los logs al iniciar:

```
✅ OpenAI API Key configured
✅ AI features enabled
```

Si ves:
```
⚠️ OPENAI_API_KEY not set - AI features disabled
```
Entonces la variable no está configurada correctamente.

### 3.3 Prueba Real desde la App

1. Accede a tu aplicación: `https://tu-app.railway.app`
2. Ve a: `/planning/sop/express/` (SOP Express Creator)
3. Intenta generar un SOP con AI
4. Si funciona, verás el contenido generado
5. Si falla, verás el error específico

---

## 🐛 RESOLUCIÓN DE PROBLEMAS

### Problema 1: Variable no encontrada

**Síntoma:**
```
❌ Variable NO encontrada en OS environment
```

**Solución:**
1. Verifica que escribiste el nombre exacto: `OPENAI_API_KEY` (case-sensitive)
2. Verifica que agregaste la variable al servicio correcto
3. Espera a que Railway redesplegue (1-2 minutos)
4. Revisa los logs de deployment

### Problema 2: API Key inválida

**Síntoma:**
```
❌ ERROR EN CONEXIÓN: Incorrect API key provided
```

**Solución:**
1. Verifica que copiaste la key completa (no la cortaste)
2. Verifica que la key comienza con `sk-`
3. Genera una nueva key en OpenAI Platform
4. Actualiza la variable en Railway

### Problema 3: Sin créditos / Quota excedida

**Síntoma:**
```
❌ ERROR: You exceeded your current quota
```

**Solución:**
1. Ve a: https://platform.openai.com/usage
2. Revisa tu balance
3. Agrega créditos a tu cuenta
4. Aumenta tu límite mensual

### Problema 4: Rate Limit

**Síntoma:**
```
❌ ERROR: Rate limit exceeded
```

**Solución:**
1. Espera 1-2 minutos
2. Reduce frecuencia de llamadas
3. Actualiza tu tier en OpenAI (para más requests/min)

### Problema 5: Conectividad desde Railway

**Síntoma:**
```
❌ ERROR: Connection timeout
```

**Solución:**
1. Verifica que Railway no tiene restricciones de red
2. Verifica el status de OpenAI: https://status.openai.com
3. Contacta soporte de Railway si persiste

### Problema 6: Modelo no disponible

**Síntoma:**
```
❌ ERROR: Model gpt-4 not found
```

**Solución:**
1. Verifica que tu cuenta tiene acceso al modelo
2. Usa `gpt-4o-mini` o `gpt-3.5-turbo` como alternativa
3. Actualiza OPENAI_MODEL en Railway Variables

---

## 📊 MONITOREO Y COSTOS

### Monitorear Uso

1. **Dashboard de OpenAI:**
   - Ve a: https://platform.openai.com/usage
   - Revisa uso diario/mensual
   - Configura alertas

2. **Logs de Railway:**
   - Busca errores de API
   - Monitorea frecuencia de llamadas

### Estimación de Costos

**Uso típico mensual con `gpt-4o-mini`:**

| Funcionalidad | Tokens/Req | Requests/Día | Costo/Mes |
|---------------|------------|--------------|-----------|
| SOP Generator | 1,500 | 10 | $0.68 |
| Daily Plan AI | 800 | 50 | $1.80 |
| Quick Planner | 1,200 | 20 | $1.08 |
| NLP Commands | 400 | 30 | $0.54 |
| **TOTAL** | - | 110 | **~$4.10** |

**Recomendación:** Configurar límite de $10/mes para uso seguro.

---

## 🔒 SEGURIDAD

### Mejores Prácticas

✅ **SÍ hacer:**
- Usar variables de entorno en Railway
- Rotar la API key cada 90 días
- Configurar límites de uso
- Monitorear logs regularmente
- Usar rate limiting en tu app

❌ **NO hacer:**
- Hardcodear la key en código
- Commitear la key a Git
- Compartir la key públicamente
- Usar la misma key en dev y prod
- Dejar límites ilimitados

### Rotación de API Key

**Cada 3 meses o si se compromete:**

1. Genera nueva key en OpenAI Platform
2. Actualiza OPENAI_API_KEY en Railway
3. Espera deployment
4. Verifica que funciona
5. Elimina la key antigua en OpenAI

---

## 📚 REFERENCIAS

### Documentación Oficial

- **OpenAI API:** https://platform.openai.com/docs
- **OpenAI Pricing:** https://openai.com/pricing
- **Railway Docs:** https://docs.railway.app
- **Railway Variables:** https://docs.railway.app/develop/variables

### Soporte

- **OpenAI Support:** https://help.openai.com
- **Railway Support:** https://railway.app/help
- **Status Pages:**
  - OpenAI: https://status.openai.com
  - Railway: https://status.railway.app

### Recursos Internos

- **Script de Diagnóstico:** `/diagnose_openai_api.py`
- **Variables de Ejemplo:** `/.env.example`
- **Settings de Django:** `/kibray_backend/settings/base.py` (línea 181)

---

## ✅ CHECKLIST DE VERIFICACIÓN

Use esta checklist para asegurarte de que todo está configurado:

- [ ] Cuenta de OpenAI creada
- [ ] Método de pago configurado
- [ ] API Key generada (empieza con `sk-`)
- [ ] API Key guardada en lugar seguro
- [ ] Variable `OPENAI_API_KEY` agregada en Railway
- [ ] Variable `OPENAI_MODEL` configurada (opcional)
- [ ] Railway redesplegó automáticamente
- [ ] Logs de Railway muestran "AI features enabled"
- [ ] Script de diagnóstico ejecutado exitosamente
- [ ] Prueba real desde la app funciona
- [ ] Límites de uso configurados en OpenAI
- [ ] Alertas de uso habilitadas
- [ ] Documentación revisada

---

## 🎉 RESULTADO ESPERADO

Una vez completada la configuración, deberías ver:

```bash
$ python diagnose_openai_api.py

╔════════════════════════════════════════════╗
║   DIAGNÓSTICO OPENAI API - RAILWAY         ║
╚════════════════════════════════════════════╝

✅ Variable de Entorno: OPENAI_API_KEY configurada
✅ Dependencias: openai 2.7.2 instalada
✅ Conexión API: SUCCESS
✅ Model: gpt-4o-mini
✅ Respuesta: 4
✅ Tokens usados: 23

✅ AI SOP Generator: OpenAI disponible
✅ AI Focus Helper: OpenAI disponible
✅ Planner AI: OpenAI disponible
✅ Daily Plan AI: Módulo importable
✅ NLP Service: Módulo importable

🎉 ¡TODO ESTÁ FUNCIONANDO CORRECTAMENTE!

✅ La integración con OpenAI API está operativa
✅ Todos los servicios AI están disponibles
✅ Railway puede usar las funcionalidades AI
```

---

**¿Necesitas ayuda?**
- Revisa la sección de "Resolución de Problemas"
- Ejecuta el script de diagnóstico
- Revisa los logs de Railway
- Contacta al equipo de desarrollo

**Última actualización:** Diciembre 6, 2024
