from django.shortcuts import render
from .models import BatchForFirstWash,ProcessFirstWash, Machine
from .serializers import BatchForFirstWashSerializer, ProcessFirstWashSerializer, CreateProcessFirstWashSerializer, MachineSerializer
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
# Create your views here.

class MachineViewSet(ModelViewSet):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer

class BatchForFirstWashViewSet(ModelViewSet):
    queryset = BatchForFirstWash.objects.all().prefetch_related("source_batches","source_bundles__bundle")
    serializer_class = BatchForFirstWashSerializer

class ProcessFirstWashViewSet(ModelViewSet):
    queryset = ProcessFirstWash.objects.all()
    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateProcessFirstWashSerializer
        return ProcessFirstWashSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        first_wash = serializer.save()
        serializer = ProcessFirstWashSerializer(first_wash)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

 
        
            