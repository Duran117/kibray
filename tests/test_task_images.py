"""
Tests para TaskImage Versionado (Q11.8)
Módulo 11 - FASE 2
"""

import pytest
from io import BytesIO
from PIL import Image as PILImage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from core.models import Project, Task, TaskImage


@pytest.fixture
def user():
    return User.objects.create_user(username="imguser", password="testpass123")


@pytest.fixture
def project():
    from datetime import date

    return Project.objects.create(name="Image Test Project", start_date=date.today())


@pytest.fixture
def sample_image():
    """Crear una imagen de prueba en memoria"""
    img = PILImage.new("RGB", (100, 100), color="red")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(name="test_image.jpg", content=buffer.read(), content_type="image/jpeg")


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.module_11
class TestTaskImageVersioning:
    """Tests para versionado de imágenes en tareas (Q11.8)"""

    def test_add_first_image(self, project, user, sample_image):
        """Agregar primera imagen a una tarea"""
        task = Task.objects.create(project=project, title="Task with image", created_by=user)

        task_image = task.add_image(image_file=sample_image, uploaded_by=user, caption="Primera versión")

        assert task_image.version == 1
        assert task_image.is_current is True
        assert task.images.count() == 1

    def test_add_second_image_increments_version(self, project, user):
        """Agregar segunda imagen incrementa version y marca anterior como no-current"""
        task = Task.objects.create(project=project, title="Task", created_by=user)

        # Primera imagen
        img1_buffer = BytesIO()
        PILImage.new("RGB", (100, 100), color="red").save(img1_buffer, format="JPEG")
        img1_buffer.seek(0)
        img1 = SimpleUploadedFile("img1.jpg", img1_buffer.read(), content_type="image/jpeg")

        first_img = task.add_image(image_file=img1, uploaded_by=user, caption="V1")

        # Segunda imagen
        img2_buffer = BytesIO()
        PILImage.new("RGB", (100, 100), color="blue").save(img2_buffer, format="JPEG")
        img2_buffer.seek(0)
        img2 = SimpleUploadedFile("img2.jpg", img2_buffer.read(), content_type="image/jpeg")

        second_img = task.add_image(image_file=img2, uploaded_by=user, caption="V2")

        # Verificar versiones
        first_img.refresh_from_db()
        assert first_img.version == 1
        assert first_img.is_current is False  # Ya no es current

        assert second_img.version == 2
        assert second_img.is_current is True

        assert task.images.count() == 2

    def test_multiple_images_versioning(self, project, user):
        """Agregar múltiples imágenes mantiene el versionado correcto"""
        task = Task.objects.create(project=project, title="Multi-img task", created_by=user)

        for i in range(1, 6):  # 5 imágenes
            buffer = BytesIO()
            PILImage.new("RGB", (100, 100), color="green").save(buffer, format="JPEG")
            buffer.seek(0)
            img = SimpleUploadedFile(f"img{i}.jpg", buffer.read(), content_type="image/jpeg")
            task.add_image(image_file=img, uploaded_by=user, caption=f"Version {i}")

        # Verificar versiones
        images = task.images.all().order_by("version")
        assert images.count() == 5

        for i, img in enumerate(images, start=1):
            assert img.version == i

        # Solo la última debe ser current
        current_images = task.images.filter(is_current=True)
        assert current_images.count() == 1
        assert current_images.first().version == 5

    def test_get_current_image(self, project, user):
        """Obtener la imagen actual (versión más reciente)"""
        task = Task.objects.create(project=project, title="Task", created_by=user)

        # Agregar 3 imágenes
        for i in range(1, 4):
            buffer = BytesIO()
            PILImage.new("RGB", (100, 100), color="yellow").save(buffer, format="JPEG")
            buffer.seek(0)
            img = SimpleUploadedFile(f"img{i}.jpg", buffer.read(), content_type="image/jpeg")
            task.add_image(image_file=img, uploaded_by=user)

        current = task.images.filter(is_current=True).first()
        assert current is not None
        assert current.version == 3

    def test_get_all_versions_history(self, project, user):
        """Obtener histórico completo de versiones"""
        task = Task.objects.create(project=project, title="Task", created_by=user)

        versions = []
        for i in range(1, 4):
            buffer = BytesIO()
            PILImage.new("RGB", (100, 100), color="purple").save(buffer, format="JPEG")
            buffer.seek(0)
            img = SimpleUploadedFile(f"img{i}.jpg", buffer.read(), content_type="image/jpeg")
            versions.append(task.add_image(image_file=img, uploaded_by=user, caption=f"V{i}"))

        all_versions = task.images.all().order_by("version")
        assert all_versions.count() == 3

        for i, img in enumerate(all_versions, start=1):
            assert img.version == i

    def test_image_caption_and_metadata(self, project, user, sample_image):
        """Verificar que caption y metadata se guardan correctamente"""
        task = Task.objects.create(project=project, title="Task", created_by=user)

        task_image = task.add_image(
            image_file=sample_image, uploaded_by=user, caption="Imagen de referencia del touch-up"
        )

        assert task_image.caption == "Imagen de referencia del touch-up"
        assert task_image.uploaded_by == user
        assert task_image.uploaded_at is not None

    def test_task_with_multiple_images_touch_up(self, project, user):
        """Touch-up con varias imágenes (antes/después)"""
        task = Task.objects.create(project=project, title="Touch-up task", is_touchup=True, created_by=user)

        # Imagen "antes"
        before_buffer = BytesIO()
        PILImage.new("RGB", (200, 200), color="gray").save(before_buffer, format="JPEG")
        before_buffer.seek(0)
        before_img = SimpleUploadedFile("before.jpg", before_buffer.read(), content_type="image/jpeg")
        task.add_image(image_file=before_img, uploaded_by=user, caption="Antes de reparar")

        # Imagen "después"
        after_buffer = BytesIO()
        PILImage.new("RGB", (200, 200), color="white").save(after_buffer, format="JPEG")
        after_buffer.seek(0)
        after_img = SimpleUploadedFile("after.jpg", after_buffer.read(), content_type="image/jpeg")
        task.add_image(image_file=after_img, uploaded_by=user, caption="Después de reparar")

        assert task.images.count() == 2
        current = task.images.filter(is_current=True).first()
        assert current.caption == "Después de reparar"

    def test_image_queryset_ordering(self, project, user):
        """TaskImage se ordena por uploaded_at descendente por defecto"""
        task = Task.objects.create(project=project, title="Task", created_by=user)

        images = []
        for i in range(3):
            buffer = BytesIO()
            PILImage.new("RGB", (100, 100), color="orange").save(buffer, format="JPEG")
            buffer.seek(0)
            img = SimpleUploadedFile(f"img{i}.jpg", buffer.read(), content_type="image/jpeg")
            images.append(task.add_image(image_file=img, uploaded_by=user))

        # El queryset default debe retornar más recientes primero
        ordered = list(task.images.all())
        assert ordered[0].version > ordered[-1].version

    def test_task_with_no_images(self, project, user):
        """Tarea sin imágenes adjuntas"""
        task = Task.objects.create(project=project, title="No images", created_by=user)

        assert task.images.count() == 0
        current = task.images.filter(is_current=True).first()
        assert current is None

    def test_image_str_representation(self, project, user, sample_image):
        """Verificar __str__ de TaskImage"""
        task = Task.objects.create(project=project, title="Task", created_by=user)
        img = task.add_image(image_file=sample_image, uploaded_by=user)

        assert str(img) == f"{task.title} - v{img.version}"
