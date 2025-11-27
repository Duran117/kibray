from rest_framework import serializers

from signatures.models import Signature


class SignatureSerializer(serializers.ModelSerializer):
    signer = serializers.PrimaryKeyRelatedField(read_only=True)

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
        ]
        read_only_fields = ("id", "signed_at")
