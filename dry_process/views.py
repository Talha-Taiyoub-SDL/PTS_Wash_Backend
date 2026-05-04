from .models import TrackingHistory
from .serializers import TrackingHistorySerializer
from rest_framework.viewsets import ModelViewSet

# Create your views here.
class TrackingHistoryViewSet(ModelViewSet):
    queryset = TrackingHistory.objects.all()
    serializer_class = TrackingHistorySerializer
    