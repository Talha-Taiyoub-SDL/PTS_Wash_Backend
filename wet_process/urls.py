from django.urls import path,include
from rest_framework_nested.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("first-wash-batches", views.BatchForFirstWashViewSet, basename="first-wash-batch")

urlpatterns = [
    path("",include(router.urls))
]