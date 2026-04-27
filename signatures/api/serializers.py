from rest_framework import serializers

from signatures.models import Signature


class SignatureSerializer(serializers.ModelSerializer):
    signer = serializers.PrimaryKeyRelatedField(read_only=True)
    # Phase D4 — convenience: expose the model label of the GFK target so
    # consumers don't need a second round-trip to ContentType.
    content_type_label = serializers.SerializerMethodField()

    class Meta:
        model = Signature
        fields = [
            "id",
            "signer",
            "title",
            "signed_at",
            "hash_alg",
            "content_hash",
            "note",
            "file",
            "content_type",
            "content_type_label",
            "object_id",
        ]
        read_only_fields = ("id", "signed_at", "content_type_label")

    def get_content_type_label(self, obj) -> str | None:
        ct = obj.content_type
        if ct is None:
            return None
        return f"{ct.app_label}.{ct.model}"
