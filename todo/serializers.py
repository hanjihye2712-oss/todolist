from rest_framework.serializers import ModelSerializer
from .models import Todo


class TodoSerializer(ModelSerializer):
    class Meta:
        model = Todo
        fields = [
            "id",
            "name",
            "description",
            "complete",
            "exp",
            "image",
            "created_at",
            "user",
        ]
        read_only_fields = ["user"]
