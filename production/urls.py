from django.urls import path,include
from rest_framework_nested.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("stage-names", views.StageNameViewSet, basename="stage-name")
router.register("plannings", views.PlannigViewSet, basename="planning")
router.register("received-bundles", views.ReceivedBundleViewSet, basename="received-bundles")
router.register("batches", views.BatchViewSet, basename="batch")
router.register("batch-stages", views.BatchStageViewSet, basename="batch-stage")
router.register("batch-stage-history", views.BatchStageHistoryViewSet, basename="batch-stage-history")
router.register("rejections",views.RejectionViewSet, basename="rejection")
router.register("qc-stage-summaries",views.BatchQcStageSummaryViewSet,basename="qc-stage-summary")

urlpatterns = [
    path("",include(router.urls))
]

