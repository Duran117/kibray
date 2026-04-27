import hashlib

from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from signatures.api.serializers import SignatureSerializer
from signatures.models import Signature


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Authenticated users can read; modifications restricted to owner (signer)."""

    def has_permission(self, request, view):
        # SECURITY: All actions require authentication
        if not request.user or not request.user.is_authenticated:
            return False
        if view.action in ("list", "retrieve", "verify", "for_object"):
            return True
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in ("GET",):
            return True
        return request.user and obj.signer_id == request.user.id


class SignatureViewSet(viewsets.ModelViewSet):
    queryset = Signature.objects.all()
    serializer_class = SignatureSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        """Optional Phase D4 filters on GFK target.

        ``?content_type=<id>``       — filter by ContentType primary key
        ``?content_type_label=app.model`` — filter by app_label.model string
        ``?object_id=<id>``          — filter by signed object's pk
        """
        qs = Signature.objects.all()
        params = self.request.query_params

        ct_id = params.get("content_type")
        if ct_id:
            try:
                qs = qs.filter(content_type_id=int(ct_id))
            except (TypeError, ValueError):
                qs = qs.none()

        label = params.get("content_type_label")
        if label and "." in label:
            app_label, model = label.split(".", 1)
            try:
                ct = ContentType.objects.get(app_label=app_label, model=model)
                qs = qs.filter(content_type=ct)
            except ContentType.DoesNotExist:
                qs = qs.none()

        obj_id = params.get("object_id")
        if obj_id:
            try:
                qs = qs.filter(object_id=int(obj_id))
            except (TypeError, ValueError):
                qs = qs.none()

        return qs

    def perform_create(self, serializer):
        serializer.save(signer=self.request.user)

    @action(detail=True, methods=["post"], url_path="verify")
    def verify(self, request, pk=None):
        """Verify provided content against stored hash.

        Payload: { content: string or bytes (base64/utf-8), hash_alg?: 'sha256' }
        Returns: { matches: bool, expected: hex, actual: hex }
        """
        sig = self.get_object()
        content = request.data.get("content", "")
        alg = (request.data.get("hash_alg") or sig.hash_alg).lower()
        try:
            h = hashlib.new(alg)
        except ValueError:
            return Response(
                {"error": gettext("Unsupported algorithm: %(alg)s") % {"alg": alg}}, status=400
            )
        content_bytes = content.encode("utf-8") if isinstance(content, str) else content or b""
        h.update(content_bytes)
        actual = h.hexdigest()
        expected = sig.content_hash
        return Response({"matches": actual == expected, "expected": expected, "actual": actual})

    @action(detail=False, methods=["get"], url_path="for-object")
    def for_object(self, request):
        """Phase D4 — list signatures attached to a specific document.

        Required query params:
        - ``content_type_label`` — e.g. ``core.estimate``
        - ``object_id``          — primary key of the signed document
        """
        label = request.query_params.get("content_type_label")
        obj_id = request.query_params.get("object_id")
        if not label or not obj_id:
            return Response(
                {"error": "content_type_label and object_id are required"},
                status=400,
            )
        if "." not in label:
            return Response({"error": "content_type_label must be 'app.model'"}, status=400)
        app_label, model = label.split(".", 1)
        try:
            ct = ContentType.objects.get(app_label=app_label, model=model)
        except ContentType.DoesNotExist:
            return Response({"error": f"unknown content type: {label}"}, status=404)
        try:
            obj_id_int = int(obj_id)
        except (TypeError, ValueError):
            return Response({"error": "object_id must be integer"}, status=400)

        qs = Signature.objects.filter(content_type=ct, object_id=obj_id_int).order_by("-signed_at")
        return Response(
            {
                "content_type_label": label,
                "object_id": obj_id_int,
                "count": qs.count(),
                "signatures": SignatureSerializer(qs, many=True).data,
            }
        )

