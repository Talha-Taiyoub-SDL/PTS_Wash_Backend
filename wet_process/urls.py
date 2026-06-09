from django.urls import path, include
from rest_framework_nested.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("machines", views.MachineViewSet, basename="machine")
router.register("batches", views.BatchViewSet, basename="batch")
router.register("wash-processes", views.WashProcessViewSet, basename="wash-process")
router.register(
    "first-wash-processes", views.ProcessFirstWashViewSet, basename="first-wash-process"
)
router.register(
    "second-wash-processes",
    views.ProcessSecondWashViewSet,
    basename="second-wash-process",
)
router.register(
    "first-wash-hydro-processes",
    views.ProcessFirstWashHydroViewSet,
    basename="first-wash-hydro-process",
)
router.register(
    "second-wash-hydro-processes",
    views.ProcessSecondWashHydroViewSet,
    basename="second-wash-hydro-process",
)
router.register(
    "first-wash-dryer-processes",
    views.ProcessFirstWashDryerViewSet,
    basename="first-wash-dryer-process",
)
router.register(
    "second-wash-dryer-processes",
    views.ProcessSecondWashDryerViewSet,
    basename="second-wash-dryer-process",
)

urlpatterns = [
    path("", include(router.urls)),
    path("batches/<str:pk>/rewash/", views.BatchRewashView.as_view()),
    path("batches/<str:pk>/rejections/", views.RejectionView.as_view()),
]
