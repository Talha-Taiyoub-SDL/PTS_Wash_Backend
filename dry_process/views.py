from .models import TrackingHistory, Planning
from .serializers import (
    TrackingHistorySerializer,
    RejectionSerializer,
    PlanningSerializer,
    UpdatePlanningSerializer,
)
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend


# Create your views here.
class PlannigViewSet(ModelViewSet):
    http_method_names = ["get", "post", "patch"]
    queryset = (
        Planning.objects.all().prefetch_related("route_steps").order_by("-last_update")
    )
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["mpo", "color"]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return UpdatePlanningSerializer
        else:
            return PlanningSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        planning = serializer.save()
        serializer = PlanningSerializer(planning)
        return Response(serializer.data)


class TrackingHistoryViewSet(ModelViewSet):
    queryset = TrackingHistory.objects.all()
    serializer_class = TrackingHistorySerializer


class RejectionViewSet(ModelViewSet):
    queryset = TrackingHistory.objects.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return RejectionSerializer
        return TrackingHistorySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        histories = serializer.save()
        serializer = TrackingHistorySerializer(histories, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
