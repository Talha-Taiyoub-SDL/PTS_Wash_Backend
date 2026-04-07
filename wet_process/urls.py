from django.urls import path,include
from rest_framework_nested.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("machines",views.MachineViewSet,basename="machine")
router.register("batches", views.BatchViewSet, basename="batch")
router.register("batch-sources", views.BatchQcViewSet, basename="batch-source")
router.register("first-wash-processes", views.ProcessFirstWashViewSet, basename="first-wash-process")
# router.register("first-wash-hydro-processes",views.ProcessFirstWashHydroViewSet, basename="first-wash-hydro-process")
# router.register("first-wash-dryer-processes",views.ProcessFirstWashDryerViewSet, basename="first-wash-dryer-process")
router.register("rejections", views.RejectionViewSet, basename="rejection")
# router.register("wash-logs", views.WashLogViewSet, basename="wash-log")

urlpatterns = [
    path("",include(router.urls))
]