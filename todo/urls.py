from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.api_views import (
    TodoViewSet,
    TodoListAPI,
    TodoCreateAPI,
    TodoRetrieveAPI,
    TodoUpdateAPI,
    TodoDeleteAPI,
)

router = DefaultRouter()
router.register("view", TodoViewSet, basename="todo")

app_name = "todo"

urlpatterns = [
    # ✅ APIView 기반 (tests_crud.py가 치는 주소)
    path("api/list/", TodoListAPI.as_view(), name="todo_api_list"),
    path("api/create/", TodoCreateAPI.as_view(), name="todo_api_create"),
    path("api/retrieve/<int:pk>/", TodoRetrieveAPI.as_view(), name="todo_api_retrieve"),
    path("api/update/<int:pk>/", TodoUpdateAPI.as_view(), name="todo_api_update"),
    path("api/delete/<int:pk>/", TodoDeleteAPI.as_view(), name="todo_api_delete"),
    # ✅ ViewSet 기반 (testsviewset*가 치는 주소)
    path("viewsets/", include(router.urls)),
]
