from .models import TrackingHistory
from .serializers import TrackingHistorySerializer, RejectionSerializer
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.response import Response
from rest_framework import status, mixins

# Create your views here.
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
            
    