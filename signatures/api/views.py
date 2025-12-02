import hashlib

from django.utils.translation import gettext_lazy as _, gettext
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from signatures.api.serializers import SignatureSerializer
from signatures.models import Signature


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow anyone to read; modifications restricted to owner (signer)."""

    def has_permission(self, request, view):
        if view.action in ("list", "retrieve", "verify"):
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in ("GET",):
            return True
        return request.user and obj.signer_id == request.user.id


class SignatureViewSet(viewsets.ModelViewSet):
    queryset = Signature.objects.all()
    serializer_class = SignatureSerializer
    permission_classes = [IsOwnerOrReadOnly]

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
            return Response({"error": gettext("Unsupported algorithm: %(alg)s") % {"alg": alg}}, status=400)
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = content or b""
        h.update(content_bytes)
        actual = h.hexdigest()
        expected = sig.content_hash
        return Response({"matches": actual == expected, "expected": expected, "actual": actual})
