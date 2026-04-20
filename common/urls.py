from django.urls import path,include
from rest_framework_nested.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("master-plans",views.MasterPlanViewSet,basename="master-plan")

urlpatterns = [
    path("",include(router.urls))
]