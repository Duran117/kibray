# 🎨 Muestras de Color (Samples) - Análisis Técnico

## ✅ QUE EXISTE AHORA

### 1. Modelo ColorSample
**Ubicación:** `core/models.py` línea 3315

```python
class ColorSample(models.Model):
    STATUS_CHOICES = [
        ("proposed", "Propuesto"),
        ("review", "En Revisión"),
        ("approved", "Aprobado"),
        ("rejected", "Rechazado"),
        ("archived", "Archivado"),
    ]
    
    # Campos principales
    project = ForeignKey(Project)
    code = CharField(max_length=60)              # SW xxxx, Milesi xxx, etc
    name = CharField(max_length=120)
    brand = CharField(max_length=120)
    finish = CharField(max_length=120)
    gloss = CharField(max_length=50)
    version = PositiveIntegerField              # Incrementa con variantes
    status = CharField(choices=STATUS_CHOICES)
    
    # Imágenes
    sample_image = ImageField                    # Foto de la muestra
    reference_photo = ImageField                 # Foto de referencia
    
    # Notas
    notes = TextField                            # Notas internas
    client_notes = TextField                     # Notas para cliente
    annotations = JSONField                      # Marcadores/comentarios
    
    # Ubicación
    room_location = CharField                    # "Kitchen", "Master Bedroom"
    room_group = CharField                       # Agrupar por habitación
    sample_number = CharField                    # KPISM10001
    
    # Actores & Timestamps
    created_by = ForeignKey(User)
    approved_by = ForeignKey(User)
    approved_at = DateTimeField
    rejected_by = ForeignKey(User)
    rejected_at = DateTimeField
    rejection_reason = TextField
    
    # Firma digital
    approval_signature = TextField               # Hash de firma criptográfica
    approval_ip = GenericIPAddressField         # IP del aprobador
    
    # Relaciones
    linked_tasks = ManyToManyField(Task)
    parent_sample = ForeignKey(self)             # Para variantes
    
    # Timestamps
    created_at = DateTimeField
    updated_at = DateTimeField
```

**Capacidades:**
- ✅ Subir imágenes de muestras
- ✅ Versioning (múltiples variantes)
- ✅ Estados de flujo (proposed → review → approved/rejected)
- ✅ Notas interno y para cliente
- ✅ Firma digital criptográfica
- ✅ Auditoría de IP address
- ✅ Enlazar con tareas
- ✅ Agrupar por habitación

---

### 2. Modelo ColorApproval
**Ubicación:** `core/models.py` línea 252

```python
class ColorApproval(models.Model):
    """Aprobación/rechazo de muestras de color con evidencia de firma digital."""
    
    STATUS_CHOICES = [
        ("PENDING", "Pendiente"),
        ("APPROVED", "Aprobado"),
        ("REJECTED", "Rechazado"),
    ]
    
    project = ForeignKey(Project)
    requested_by = ForeignKey(User)              # Quién solicita
    approved_by = ForeignKey(User)               # Quién aprueba
    status = CharField(choices=STATUS_CHOICES)
    
    color_name = CharField(max_length=100)
    color_code = CharField(max_length=50)
    brand = CharField(max_length=100)
    location = CharField(max_length=200)
    notes = TextField
    
    # FIRMA DIGITAL
    client_signature = FileField                 # Archivo de firma
    signed_at = DateTimeField
    
    created_at = DateTimeField
    
    def approve(self, approver: User, signature_file=None):
        """Marca como aprobado + captura firma"""
        self.status = "APPROVED"
        self.approved_by = approver
        if signature_file:
            self.client_signature = signature_file
        self.signed_at = timezone.now()
        self.save()
        # Notificar a PMs y cliente
```

**Capacidades:**
- ✅ Crear solicitudes de aprobación
- ✅ Registrar firma digital
- ✅ Registrar timestamp de firma
- ✅ Notificar cambios

---

### 3. Vistas de ColorSample
**Ubicación:** `core/views.py` líneas 1496-1800

#### color_sample_list (línea 1496)
```python
def color_sample_list(request, project_id):
    # Lista todas las muestras del proyecto
    # Filtros: brand, status
    # Template: color_sample_list.html
```
**Capacidades:** ✅ Listar, filtrar por marca y estado

#### color_sample_create (línea 1522)
```python
def color_sample_create(request, project_id):
    # Crear nueva muestra
    # Acceso: staff, client, project_manager
    # Campos: code, name, brand, finish, gloss, images, notes, location
```
**Capacidades:** ✅ Subir muestra con imagen

#### color_sample_detail (línea 1551)
```python
def color_sample_detail(request, sample_id):
    # Ver detalles de muestra
    # Mostrar: imagen, metadata, notas, estado
```
**Capacidades:** ✅ Ver detalles

#### color_sample_review (línea 1567)
```python
def color_sample_review(request, sample_id):
    # Cambiar estado de muestra
    # Validaciones: solo staff puede aprobar/rechazar
    # Notificaciones: cambios de estado
```
**Capacidades:** ✅ Revisar y cambiar estado

#### color_sample_quick_action (línea 1614)
```python
def color_sample_quick_action(request, sample_id):
    # AJAX: aprobar/rechazar rápido
    # Registra: signature, timestamp
    # Notifica: a cliente y PMs
```
**Capacidades:** ✅ Aprobación rápida con firma criptográfica

#### color_sample_edit (línea 1656)
```python
def color_sample_edit(request, sample_id):
    # Editar muestra existente
    # Permite crear variantes
```
**Capacidades:** ✅ Editar y crear variantes

#### color_sample_delete (línea 1688)
```python
def color_sample_delete(request, sample_id):
    # Eliminar muestra
    # Acceso: staff, project_manager
```
**Capacidades:** ✅ Eliminar

---

### 4. Sistema de Firma Digital (Existente)
**Ubicación:** `changeorder_customer_signature_view` (línea 2592)

```python
def changeorder_customer_signature_view(request, changeorder_id, token=None):
    # Sistema de firma para Change Orders
    # Características:
    # - Token firmado (HMAC) con expiración (7 días)
    # - Captura de firma con canvas digital
    # - Nombre del firmante
    # - Base64 encoding de imagen
    # - IP tracking para auditoría
    # - Timestamp de firma
    
    # POST: guarda firma en changeorder.signature_image
    # Flujo:
    # 1. Generar token único
    # 2. Enviar link al cliente
    # 3. Cliente abre link (sin login necesario)
    # 4. Dibuja firma en canvas
    # 5. Ingresa su nombre
    # 6. Submit → guarda imagen base64
```

**Está 100% funcional para Change Orders**

---

## ⏳ QUE FALTA

### 1. Vista Pública para Firma de Muestras de Color
**No existe aún:** `color_sample_client_signature_view`

Necesitaría:
```python
def color_sample_client_signature_view(request, sample_id, token=None):
    """
    Similar a changeorder_customer_signature_view pero para ColorSample
    
    Flujo:
    1. PM crea ColorApproval para cliente
    2. Genera token HMAC con expiración
    3. Envía link: /color-approval/{id}/sign/?token=xxx
    4. Cliente abre link (sin login)
    5. Ve muestra de color (imagen, descripción, ubicación)
    6. Dibuja firma en canvas digital
    7. Ingresa nombre completo
    8. Submit → guarda en ColorApproval.client_signature
    """
```

**Estado actual:** ❌ No existe

---

### 2. Integración ColorSample ↔ ColorApproval
**No existe aún:** Relación automática

Necesitaría:
```python
class ColorSample(models.Model):
    # AGREGAR:
    approval = ForeignKey(ColorApproval, null=True, blank=True)
    # Para enlazar la muestra con su aprobación
```

**Estado actual:** ❌ No conectado

---

### 3. Endpoints de API para Firma
**No existen aún:**
- ✅ POST `/api/color-samples/{id}/approve/` ← Esta existe (quick_action)
- ❌ POST `/api/color-approvals/{id}/sign/` ← No existe
- ❌ GET  `/api/color-approvals/{id}/status/` ← No existe

**Estado actual:** Parcial

---

### 4. Notificaciones de Firma
**No existe aún:** Notificación cuando cliente firma muestra

Necesitaría:
```python
from core.notifications import notify_color_approval_signed

def notify_color_approval_signed(approval: ColorApproval, signed_by: str):
    """Notificar a PM y cliente cuando se firma"""
    # Email a PM: "Cliente {signed_by} aprobó muestra {color_name}"
    # Email a cliente: "Tu firma fue registrada"
```

**Estado actual:** ❌ No existe

---

## 📊 Matriz de Funcionalidad

| Función | Modelo | Vista | Frontend | API | Estado |
|---------|--------|-------|----------|-----|--------|
| Subir muestra | ✅ | ✅ | ✅ | ❓ | ✅ Complete |
| Listar muestras | ✅ | ✅ | ✅ | ❓ | ✅ Complete |
| Revisar muestra | ✅ | ✅ | ✅ | ❓ | ✅ Complete |
| Aprobar muestra (staff) | ✅ | ✅ | ✅ | ✅ | ✅ Complete |
| Crear solicitud aprobación | ✅ | ❌ | ❌ | ❌ | ⏳ Partial |
| **Firma cliente** | ✅ | ❌ | ❌ | ❌ | ❌ **FALTA** |
| Notificar firma | ❌ | ❌ | ❌ | ❌ | ❌ **FALTA** |
| Auditoría de firma | ✅ | ❌ | ❌ | ❌ | ⏳ Partial |
| Enlazar con tareas | ✅ | ✅ | ✅ | ❓ | ✅ Complete |
| Versiones/variantes | ✅ | ✅ | ✅ | ❓ | ✅ Complete |

---

## 🎯 Propuesta: Implementación de Firma de Cliente

### Opción A: Extender desde Change Order (RECOMENDADO)
```python
# core/views.py - agregar función similar a changeorder_customer_signature_view

def color_sample_client_signature_view(request, sample_id, token=None):
    """
    Permite que el cliente firme digitalmente una muestra de color
    
    URL: /color-samples/{id}/sign/?token=xxx
    Requisitos:
    - Token HMAC válido (7 días)
    - Cliente debe ser el que tiene acceso al proyecto
    
    Pasos:
    1. Validar token
    2. Mostrar información de muestra
    3. Canvas para firma
    4. Capturar nombre
    5. Guardar en ColorApproval.client_signature
    6. Notificar a PM
    """
    ...
```

**Ventajas:**
- Código reutilizado (ya existe en changeorder)
- Token security probado
- Canvas digital + base64 ya implementado
- Auditoría IP address

**Tiempo estimado:** 3-4 horas

---

### Opción B: Integración con Panel de Cliente
```python
# Agregar a dashboard_client
# Mostrar "Muestras pendientes de aprobación"
# Cliente puede aprobar directamente desde dashboard
```

**Ventajas:**
- Mejor UX (no necesita click en email)
- Integrado en su workflow

**Tiempo estimado:** 2-3 horas adicionales

---

## 🚀 Plan de Acción

### Fase 1 (Alta Prioridad)
- [ ] Crear `color_sample_client_signature_view` (basado en changeorder)
- [ ] Agregar ruta URL
- [ ] Crear template HTML con canvas
- [ ] Guardar firma en ColorApproval

### Fase 2 (Media Prioridad)
- [ ] Agregar notificaciones
- [ ] API endpoint POST /api/color-samples/sign/
- [ ] Tests de firma

### Fase 3 (Baja Prioridad)
- [ ] Integrar en dashboard_client
- [ ] Listado de "muestras por firmar"
- [ ] UI mejorada

---

## 📝 Resumen

**Estado Actual:**
- ✅ Modelos completos (ColorSample + ColorApproval)
- ✅ CRUD de muestras funcional
- ✅ Aprobación por staff funcional
- ✅ Sistema de firma digital (pero solo en Change Orders)
- ❌ Firma de cliente para muestras: **NO EXISTE**

**Lo que necesitas:**
1. Vista pública para firma (similar a Change Order)
2. Link con token para cliente
3. Canvas digital + captura de nombre
4. Guardar firma + notificaciones

**Esfuerzo estimado:** 5-8 horas de desarrollo

---

**Documentado:** 3 de Diciembre, 2025
**Por:** GitHub Copilot
