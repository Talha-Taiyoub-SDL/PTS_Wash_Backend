from django.urls import path, include
from rest_framework_nested.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("machines", views.MachineViewSet, basename="machine")
router.register("batches", views.BatchViewSet, basename="batch")
router.register("wash-processes", views.WashProcessViewSet, basename="wash-process")
router.register("hydro-processes", views.HydroProcessViewSet, basename="hydro-process")
router.register("dryer-processes", views.DryerProcessViewSet, basename="dryer-process")

urlpatterns = [
    path("", include(router.urls)),
    path("batches/<str:pk>/rewash/", views.BatchRewashView.as_view()),
    path("batches/<str:pk>/rejections/", views.RejectionView.as_view()),
]
