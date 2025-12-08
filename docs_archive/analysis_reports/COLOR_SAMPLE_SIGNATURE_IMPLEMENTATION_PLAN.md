# 🎯 Plan de Implementación: Firma Digital de Muestras de Color

## Objetivo
Implementar un flujo completo para que **clientes firmen digitalmente muestras de color** (similiar al sistema de firma de Change Orders que ya existe).

---

## ✅ Checklist de Implementación

### FASE 1: Backend (2-3 horas)

- [ ] **Paso 1.1:** Crear vista `color_sample_client_signature_view` en `core/views.py`
  - [ ] GET: Mostrar formulario de firma
  - [ ] POST: Guardar firma en ColorApproval
  - [ ] Token validation (HMAC)
  - [ ] Error handling
  - **Archivo:** `core/views.py`
  - **Referencia:** Copiar estructura de `changeorder_customer_signature_view` (línea 2592)

- [ ] **Paso 1.2:** Agregar ruta URL en `core/urls.py`
  - [ ] URL: `color-samples/<int:sample_id>/sign/`
  - [ ] Parámetro token opcional
  - **Línea estimada:** `core/urls.py` línea xxx

- [ ] **Paso 1.3:** Extender modelo ColorApproval
  - [ ] Agregar campo `sample = ForeignKey(ColorSample)`
  - [ ] Agregar campo `signed_by = CharField` (nombre del firmante)
  - [ ] Crear migration

- [ ] **Paso 1.4:** Crear función para generar token de firma
  - [ ] `generate_color_approval_token(sample_id)`
  - [ ] HMAC firmado
  - [ ] Expiración 7 días
  - **Ubicación:** `core/utils.py` o similar

---

### FASE 2: Frontend (2-3 horas)

- [ ] **Paso 2.1:** Crear template `core/templates/core/color_sample_signature_form.html`
  - [ ] Mostrar imagen de muestra
  - [ ] Canvas para dibujar firma
  - [ ] Campo para nombre del firmante
  - [ ] Botones: Firmar, Limpiar, Cancelar
  - **Referencia:** `core/templates/core/changeorder_signature_form.html`

- [ ] **Paso 2.2:** Agregar JavaScript para canvas
  - [ ] Libería: signature_pad.js (ya existe)
  - [ ] Funciones: draw, clear, save
  - [ ] Convertir a base64

- [ ] **Paso 2.3:** Crear template de éxito
  - [ ] `core/templates/core/color_sample_signature_success.html`
  - [ ] Mostrar confirmación
  - [ ] Timestamp de firma

---

### FASE 3: Notificaciones (1-2 horas)

- [ ] **Paso 3.1:** Crear función `notify_color_approved_by_client`
  - [ ] Email a PM: "Cliente {name} aprobó muestra {color}"
  - [ ] Email a cliente: "Tu firma fue registrada"
  - **Ubicación:** `core/notifications.py`

- [ ] **Paso 3.2:** Integrar notificación en view
  - [ ] Llamar después de guardar firma
  - [ ] Pasar información de firma

---

### FASE 4: Testing (1 hora)

- [ ] **Paso 4.1:** Tests unitarios
  - [ ] Test token generation
  - [ ] Test token validation
  - [ ] Test signature save
  - **Archivo:** `tests/test_color_sample_signature.py`

- [ ] **Paso 4.2:** Tests de integración
  - [ ] Test flujo completo
  - [ ] Test permisos
  - [ ] Test notificaciones

---

### FASE 5: API Endpoints (1-2 horas)

- [ ] **Paso 5.1:** Crear serializer `ColorApprovalSerializer`
  - **Ubicación:** `core/api/serializers.py`

- [ ] **Paso 5.2:** Crear viewset `ColorApprovalViewSet`
  - [ ] GET: listar aprobaciones
  - [ ] POST: crear aprobación
  - [ ] PATCH: actualizar estado
  - **Ubicación:** `core/api/views.py`

- [ ] **Paso 5.3:** Registrar en router
  - **Ubicación:** `core/api/urls.py`

---

## 📋 Código Base (Copy-Paste)

### 1. Vista (core/views.py)

```python
# Copiar y adaptar de changeorder_customer_signature_view (línea 2592)

@login_required  # Opcional: permitir anónimo con token
def color_sample_client_signature_view(request, sample_id, token=None):
    """
    Vista pública para que clientes firmen digitalmente muestras de color.
    Similar a changeorder_customer_signature_view pero para ColorSample.
    
    URL: /color-samples/{id}/sign/?token=xxx
    
    GET:
    - Mostrar formulario de firma si aún no está firmada
    - Mostrar confirmación si ya está firmada
    
    POST:
    - Validar firma
    - Guardar en ColorApproval
    - Notificar a PM
    """
    from django.core import signing
    from core.models import ColorSample, ColorApproval
    
    sample = get_object_or_404(ColorSample, id=sample_id)
    
    # Validar token
    if token is not None:
        try:
            payload = signing.loads(token, max_age=60 * 60 * 24 * 7)  # 7 días
            if payload.get("sample") != sample.id:
                return HttpResponseForbidden("Token no coincide")
        except signing.SignatureExpired:
            return HttpResponseForbidden("El enlace expiró")
        except signing.BadSignature:
            return HttpResponseForbidden("Token inválido")
    
    # Verificar si ya está firmada
    approval = sample.color_approvals.filter(status="APPROVED").first()
    if approval and approval.client_signature:
        return render(request, "core/color_sample_signature_already_signed.html", 
                     {"sample": sample, "approval": approval})
    
    if request.method == "POST":
        import base64
        import uuid
        from django.core.files.base import ContentFile
        from django.utils import timezone
        from core.notifications import notify_color_approved_by_client
        
        signature_data = request.POST.get("signature_data")
        signer_name = request.POST.get("signer_name", "").strip()
        
        if not signature_data:
            return render(request, "core/color_sample_signature_form.html",
                         {"sample": sample, "error": "Dibuje su firma"})
        if not signer_name:
            return render(request, "core/color_sample_signature_form.html",
                         {"sample": sample, "error": "Ingrese su nombre"})
        
        try:
            # Convertir base64 a archivo
            format_str, imgstr = signature_data.split(";base64,")
            ext = format_str.split("/")[-1]
            signature_file = ContentFile(
                base64.b64decode(imgstr),
                name=f"color_sig_{sample.id}_{uuid.uuid4().hex[:8]}.{ext}"
            )
            
            # Crear o actualizar ColorApproval
            approval, created = ColorApproval.objects.get_or_create(
                project=sample.project,
                color_name=sample.name or f"Color #{sample.id}",
                defaults={
                    "color_code": sample.code,
                    "brand": sample.brand,
                    "location": sample.room_location,
                }
            )
            
            # Guardar firma
            approval.status = "APPROVED"
            approval.approved_by = request.user if request.user.is_authenticated else None
            approval.client_signature = signature_file
            approval.signed_at = timezone.now()
            approval.save()
            
            # Guardar IP para auditoría
            if hasattr(sample, 'approval_ip'):
                sample.approval_ip = request.META.get('REMOTE_ADDR')
                sample.save(update_fields=['approval_ip'])
            
            # Notificar
            notify_color_approved_by_client(approval, signer_name)
            
            return render(request, "core/color_sample_signature_success.html",
                         {"sample": sample, "signer_name": signer_name})
            
        except Exception as e:
            return render(request, "core/color_sample_signature_form.html",
                         {"sample": sample, "error": f"Error: {str(e)}"})
    
    else:
        # GET: Mostrar formulario
        return render(request, "core/color_sample_signature_form.html",
                     {"sample": sample})
```

### 2. URL (core/urls.py)

```python
# Agregar a urlpatterns

path('color-samples/<int:sample_id>/sign/', 
     views.color_sample_client_signature_view, 
     name='color_sample_sign'),

# Con token opcional:
path('color-samples/<int:sample_id>/sign/<str:token>/', 
     views.color_sample_client_signature_view, 
     name='color_sample_sign_with_token'),
```

### 3. Template (core/templates/core/color_sample_signature_form.html)

```html
<!-- Copiar estructura de changeorder_signature_form.html -->

{% extends "base.html" %}
{% block title %}Firmar Muestra de Color - {{ sample.name }}{% endblock %}

{% block content %}
<div class="container mt-5">
    <div class="row">
        <div class="col-md-8 offset-md-2">
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h5>Aprobación de Muestra de Color</h5>
                </div>
                <div class="card-body">
                    
                    <!-- Mostrar muestra -->
                    <div class="mb-4">
                        <h6>{{ sample.name }}</h6>
                        {% if sample.sample_image %}
                            <img src="{{ sample.sample_image.url }}" 
                                 alt="{{ sample.name }}"
                                 class="img-fluid" 
                                 style="max-height: 300px;">
                        {% endif %}
                        <p class="text-muted mt-2">
                            <strong>Ubicación:</strong> {{ sample.room_location }}<br>
                            <strong>Marca:</strong> {{ sample.brand }}<br>
                            <strong>Código:</strong> {{ sample.code }}
                        </p>
                    </div>
                    
                    <!-- Formulario de firma -->
                    <form method="post" id="signatureForm">
                        {% csrf_token %}
                        
                        {% if error %}
                            <div class="alert alert-danger">{{ error }}</div>
                        {% endif %}
                        
                        <!-- Canvas para firma -->
                        <div class="form-group mb-3">
                            <label for="canvas"><strong>Su Firma</strong></label>
                            <canvas id="signaturePad" 
                                    class="border rounded"
                                    width="500" 
                                    height="150"
                                    style="display: block; border: 1px solid #ccc; 
                                           cursor: crosshair; background: white;">
                            </canvas>
                        </div>
                        
                        <!-- Botones para canvas -->
                        <div class="mb-3">
                            <button type="button" class="btn btn-secondary btn-sm" 
                                    onclick="clearSignature()">
                                Limpiar
                            </button>
                        </div>
                        
                        <!-- Nombre del firmante -->
                        <div class="form-group mb-3">
                            <label for="signer_name"><strong>Nombre Completo</strong></label>
                            <input type="text" 
                                   class="form-control" 
                                   id="signer_name"
                                   name="signer_name"
                                   placeholder="Su nombre completo"
                                   required>
                        </div>
                        
                        <!-- Campo oculto para datos de firma -->
                        <input type="hidden" id="signature_data" name="signature_data">
                        
                        <!-- Botones -->
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary">
                                Firmar y Aprobar
                            </button>
                            <a href="javascript:history.back()" class="btn btn-outline-secondary">
                                Cancelar
                            </a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/signature_pad@4.1.5/dist/signature_pad.umd.min.js"></script>
<script>
    const canvas = document.getElementById('signaturePad');
    const signaturePad = new SignaturePad(canvas);
    
    // Ajustar resolución
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    
    function clearSignature() {
        signaturePad.clear();
    }
    
    document.getElementById('signatureForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (signaturePad.isEmpty()) {
            alert('Por favor, dibuje su firma');
            return;
        }
        
        // Guardar firma como base64
        document.getElementById('signature_data').value = 
            signaturePad.toDataURL('image/png');
        
        // Enviar formulario
        this.submit();
    });
</script>
{% endblock %}
```

### 4. Notificaciones (core/notifications.py)

```python
def notify_color_approved_by_client(approval, signer_name):
    """Notificar a PM cuando cliente firma muestra"""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    
    # Email a PM
    pm_emails = [
        u.email for u in approval.project.pm_assignments.values_list('user', flat=True)
        if u.email
    ]
    
    if pm_emails:
        context = {
            'approval': approval,
            'signer_name': signer_name,
            'project': approval.project,
        }
        
        html_message = render_to_string(
            'emails/color_approval_signed.html',
            context
        )
        
        send_mail(
            subject=f'Muestra de color aprobada: {approval.color_name}',
            message=f'Cliente {signer_name} aprobó la muestra',
            from_email='noreply@kibray.com',
            recipient_list=pm_emails,
            html_message=html_message,
        )
```

---

## 🔗 Flujo Completo

```
1. PM crea ColorSample (subir imagen)
   ↓
2. PM crea ColorApproval (solicitar aprobación)
   ↓
3. PM genera token:
   token = signing.dumps({'sample': sample_id})
   ↓
4. PM envía email al cliente con link:
   https://kibray.com/color-samples/{id}/sign/?token={token}
   ↓
5. Cliente abre link (sin login necesario)
   ↓
6. Cliente ve muestra + dibuja firma
   ↓
7. Cliente ingresa nombre
   ↓
8. Submit → Guarda en ColorApproval.client_signature
   ↓
9. Notificar a PM: "Cliente X aprobó muestra Y"
   ↓
10. Mostrar pantalla de éxito
```

---

## 📊 Estimación de Tiempo

| Tarea | Horas | Dependencias |
|-------|-------|-------------|
| Backend (view + url) | 2-3 | Core models ✅ |
| Frontend (templates) | 2-3 | Bootstrap, signature_pad |
| Notificaciones | 1-2 | Email setup |
| Tests | 1 | Backend |
| API endpoints | 1-2 | DRF |
| **TOTAL** | **7-11 horas** | |

---

## 🚀 Prioridad vs Esfuerzo

```
Alta Prioridad, Medio Esfuerzo ← Implementar primero

Ventajas:
✅ Reutiliza código existente (changeorder_signature)
✅ Modelos ya existen
✅ Seguridad probada (token HMAC)
✅ Impacto alto en UX (cliente puede firmar remotamente)
```

---

## ✅ Siguientes Pasos

1. ¿Quieres que comience la implementación ahora?
2. ¿O prefieres que primero revise otro aspecto de muestras?
3. ¿Necesitas integrar con algo más (ej. notificaciones por SMS)?

---

**Documentado:** 3 de Diciembre, 2025  
**Autor:** GitHub Copilot
