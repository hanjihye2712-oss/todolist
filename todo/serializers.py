from rest_framework.serializers import ModelSerializer
from .models import Todo


# API 요청 데이터를 모델 객체로 변환하는 변환기
class TodoSerializer(ModelSerializer):
    class Meta:
        model = Todo
        fields = "__all__"
