from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from .models import MasterPlan, GarmentUnit
from .serializers import CreateMasterPlanSerializer, MasterPlanSerializer, GarmentUnitSerializer

class MasterPlanViewSet(ModelViewSet):    
    def get_queryset(self):
        queryset = MasterPlan.objects.all()
        
        buyer = self.request.query_params.get("buyer")
        if buyer:
            queryset = queryset.filter(buyer=buyer)
            
        style = self.request.query_params.get("style")
        if style:
            queryset = queryset.filter(style=style)
            
        color = self.request.query_params.get("color")
        if color:
            queryset = queryset.filter(color=color)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateMasterPlanSerializer
        return MasterPlanSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        master_plan = serializer.save()
        serializer = MasterPlanSerializer(master_plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
class GarmentUnitViewSet(ModelViewSet):
    queryset = GarmentUnit.objects.all()
    serializer_class = GarmentUnitSerializer
    