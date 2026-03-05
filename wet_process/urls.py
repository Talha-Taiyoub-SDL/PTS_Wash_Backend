from django.urls import path,include
from rest_framework_nested.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("machines",views.MachineViewSet,basename="machine")
router.register("first-wash-batches", views.BatchForFirstWashViewSet, basename="first-wash-batch")
router.register("first-wash-processes", views.ProcessFirstWashViewSet, basename="first-wash-process")
router.register("first-wash-hydro-processes",views.ProcessFirstWashHydroViewSet, basename="first-wash-hydro-process")
router.register("first-wash-dryer-processes",views.ProcessFirstWashDryerViewSet, basename="first-wash-dryer-process")

urlpatterns = [
    path("",include(router.urls))
]