from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.api_views import TodoViewSet

router = DefaultRouter()
router.register("view", TodoViewSet, basename="todo")

app_name = "todo"

urlpatterns = [
    path("viewsets/", include(router.urls)),
]
