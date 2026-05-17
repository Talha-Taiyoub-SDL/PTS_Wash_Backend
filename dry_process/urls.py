from django.urls import path,include
from rest_framework_nested.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("tracking-histories", views.TrackingHistoryViewSet, basename="tracking-history")
router.register("rejections", views.RejectionViewSet, basename="rejection")

urlpatterns = [
    path("",include(router.urls))
]