from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from .models import Machine, Batch, BatchSource, ProcessFirstWashDryer, Rejection, ProcessFirstWash, ProcessFirstWashHydro
from .serializers import CreateProcessFirstWashSerializer, MachineSerializer,  BatchSerializer, BatchQcSerializer, CreateRejectionSerializer, ProcessFirstWashDryerSerializer, ProcessFirstWashSerializer, RejectionSerializer, UpdateProcessFirstWashDryerSerializer, UpdateProcessFirstWashSerializer, ProcessFirstWashHydroSerializer, CreateProcessFirstWashHydroSerializer, UpdateProcessFirstWashHydroSerializer
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
# Create your views here.

class MachineViewSet(ModelViewSet):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer

class ProcessFirstWashViewSet(ModelViewSet):
    def get_queryset(self):
        queryset = ProcessFirstWash.objects.all()
        batch = self.request.query_params.get("batch")
        if batch:
            queryset = queryset.filter(batch=batch)
            
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateProcessFirstWashSerializer
        elif self.request.method == "PATCH":
            return UpdateProcessFirstWashSerializer
        else:
            return ProcessFirstWashSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        first_wash = serializer.save()
        serializer = ProcessFirstWashSerializer(first_wash)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        serializer = ProcessFirstWashSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK) 
            
class ProcessFirstWashHydroViewSet(ModelViewSet):
    def get_queryset(self):
        queryset = ProcessFirstWashHydro.objects.all()
        batch = self.request.query_params.get("batch")
        if batch:
            queryset = queryset.filter(batch=batch)
            
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateProcessFirstWashHydroSerializer
        elif self.request.method == "PATCH":
            return UpdateProcessFirstWashHydroSerializer
        else:
            return ProcessFirstWashHydroSerializer
        
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        first_wash_hydro = serializer.save()
        serializer = ProcessFirstWashHydroSerializer(first_wash_hydro)
        return Response(serializer.data, status=status.HTTP_201_CREATED)    
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        serializer = ProcessFirstWashHydroSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)    
          
class ProcessFirstWashDryerViewSet(ModelViewSet):
    def get_queryset(self):
        queryset = ProcessFirstWashDryer.objects.all()
        batch = self.request.query_params.get("batch")
        type = self.request.query_params.get("type")
        
        if batch:
            queryset = queryset.filter(batch=batch)
        
        if type:
            queryset = queryset.filter(type=type)
            
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return UpdateProcessFirstWashDryerSerializer
        else:
            return ProcessFirstWashDryerSerializer
        
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        serializer = ProcessFirstWashDryerSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
              
class RejectionViewSet(ModelViewSet):
    def get_queryset(self):
        queryset = Rejection.objects.all()
        batch = self.request.query_params.get("batch", None)
        queryset = queryset.filter(batch=batch)
        
    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateRejectionSerializer
        else:
            return RejectionSerializer 
        
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rejections = serializer.save()
        serializer = RejectionSerializer(rejections, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
            
                  
    serializer_class = RejectionSerializer            
    
# class WashLogViewSet(ModelViewSet):
#     def get_queryset(self):
#         queryset = WashLog.objects.all()
#         content_type = self.request.query_params.get("content_type")
#         object_id = self.request.query_params.get("object_id")
        
#         if content_type:
#             content_type = ContentType.objects.get(model=content_type)
#             queryset = queryset.filter(content_type=content_type.id)
        
#         if object_id:
#             queryset = queryset.filter(object_id=object_id)
            
#         return queryset
    
#     def get_serializer_class(self):
#         if self.request.method == "PATCH":
#             return UpdateWashLogSerializer
#         else:
#             return WashLogSerializer
    
#     # To provide the list of batches, consisting those new rewash batches can be created    
#     @action(detail=False, methods=["get"], url_path="rewashing")
#     def rewashing(self, request):
#         queryset = self.get_queryset().filter(remaining_rewash_quantity__gt=0)
#         serializer = WashLogSerializer(queryset, many=True)
#         return Response(serializer.data)
        
#     def update(self, request, *args, **kwargs):
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         wash_log = serializer.save()
#         serializer = WashLogSerializer(wash_log)
#         return Response(serializer.data)      
    
class BatchViewSet(ModelViewSet):
    http_method_names = ["get", "post"]
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer 

class BatchQcViewSet(ModelViewSet):
    http_method_names = ["get","patch"]
    def get_queryset(self):
        queryset = BatchSource.objects.all().select_related("batch")
        batch = self.request.query_params.get("batch", None)
        stage = self.request.query_params.get("stage", None)
        type = self.request.query_params.get("type", None)
        
        if batch:
            queryset = queryset.filter(batch=batch)   
        if stage:
            queryset = queryset.filter(batch__stage=stage)  
        if type: 
            queryset = queryset.filter(batch__type=type)           
        return queryset
        
    serializer_class = BatchQcSerializer    
    
# Write documentation about the logic of showing remaining rewash quantity per mpo, style, and so. 
# BatchSource er moddhe giye proti batch source traverse kore dekhte hobe:
# (batch.stage = "first_wash" & batch.type="normal_wash" eder rewash_quantity (per mpo)) - (batch.stage = "first_wash" & batch.type = "rewash" er quantity per mpo)
     