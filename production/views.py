from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from django.shortcuts import get_object_or_404
from django.db.models import Value
from django.db.models.functions import Substr, Concat
from django.utils import timezone
from django.db import transaction
from django.db.models import F, OuterRef, Subquery, Prefetch
from rest_framework import status
from .models import Planning, ReceivedBundle, Batch, BatchBundle, BatchStage, BatchStageHistory, PlanningRouteStep, StageName, BatchQcStageSummary, Rejection
from . import serializers

def create_fabricated_data(fabricated_data,route):
    fabricated_data["sequence"] = route.sequence
    fabricated_data["production_status"] = "in"
    return fabricated_data

def check_stage(batch,stage):
    # Check if the stage is part of the planning or not
    try:
        route = batch.planning.route_steps.get(stage=stage)
        return route
    except PlanningRouteStep.DoesNotExist:
        raise ValidationError(
            f"{stage} stage is not defined in the planning route."
        )

# Create your views here.

class StageNameViewSet(ModelViewSet):
    http_method_names = ["get"]
    queryset = StageName.objects.all()
    serializer_class = serializers.StageNameSerializer

class PlannigViewSet(ModelViewSet):
    http_method_names = ["get","post","patch"]
    queryset = Planning.objects.all().prefetch_related("route_steps").order_by("-last_update")
    filter_backends = [SearchFilter]
    search_fields = ["mpo"]
    
    def get_serializer_class(self):
        if self.request.method =="PATCH":
            return serializers.UpdatePlanningSerializer
        else:
            return serializers.PlanningSerializer
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        planning = serializer.save()
        serializer = serializers.PlanningSerializer(planning)
        return Response(serializer.data)
       
class ReceivedBundleViewSet(ModelViewSet):
    http_method_names = ["get","post","delete"]
    queryset = ReceivedBundle.objects.all()
    serializer_class = serializers.ReceivedBundleSerializer 
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if instance.status == "allocated":
            raise ValidationError("You can't delete this bundle cause it's already allocated in a batch.")
        
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
      
    # Scan the bundle and get the received_bundle object
    @action(detail=False, methods=["get"], url_path="scan")
    def scan_bundle(self, request):
        mpo = request.query_params.get("mpo")
        marker = request.query_params.get("marker")
        bundle_no = request.query_params.get("bundle_no")
        if not mpo or not marker or not bundle_no:
            raise ValidationError(
                "mpo, marker, and bundle_no are required."
            )

        try:
            bundle_no = int(bundle_no)
        except (TypeError, ValueError):
            raise ValidationError(
                "bundle_no must be an integer."
            )
        
        try:
            bundle = ReceivedBundle.objects.get(
                mpo=mpo,
                marker=marker,
                bundle_no=bundle_no
            )
        except ReceivedBundle.DoesNotExist:
            raise ValidationError(
                "This bundle is not received or does not exist."
            )

        if bundle.status == ReceivedBundle.STATUS_ALLOCATED:
            raise ValidationError(
                "This bundle is already allocated in a batch."
            )

        serializer = self.get_serializer(bundle)
        return Response(serializer.data)
 
class BatchViewSet(ModelViewSet):
    http_method_names = ["get","post","delete"]
    queryset = Batch.objects.all().select_related("planning").prefetch_related("planning__route_steps","batch_bundles__received")
    serializer_class = serializers.BatchSerializer 
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        try:
            BatchStage.objects.get(batch=instance)
            raise ValidationError("You can't delete this batch cause this batch is already in processing stage")
        
        except BatchStage.DoesNotExist:
            with transaction.atomic():
                
                # reset received bundle statuses
                batch_bundles = instance.batch_bundles.select_related("received")

                for batch_bundle in batch_bundles:
                    received_bundle = batch_bundle.received
                    received_bundle.status = ReceivedBundle.STATUS_RECEIVED
                    received_bundle.save(update_fields=["status"])

                instance.delete()
            
            return Response(status=status.HTTP_204_NO_CONTENT)    

class BatchStageViewSet(ModelViewSet):
    http_method_names = ["get","post"]
    queryset = BatchStage.objects.all()
    serializer_class = serializers.BatchStageSerializer
    
    def create(self, request, *args, **kwargs):
        batch_id = request.data.get("batch")
        stage = request.data.get("current_stage")
        stage_status = request.data.get("current_status")
               
        if not batch_id and stage and stage_status:
            return Response({"detail": "Batch, current stage, and current_status are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if batch exists
        batch = get_object_or_404(Batch, id=batch_id)
        
        # Check if the stage exists in the route 
        route = check_stage(batch=batch, stage=stage)
        
        # Create fabricated_data
        fabricated_data = create_fabricated_data(fabricated_data = request.data.copy(), route=route)
        
        try:
            batch_stage = BatchStage.objects.get(batch=batch)
            
            # Update the existing batch stage
            serializer = self.get_serializer(batch_stage, data=fabricated_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        except BatchStage.DoesNotExist:
            
            # Create new if not exists
            serializer = self.get_serializer(data=fabricated_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class BatchStageHistoryViewSet(ModelViewSet):
    http_method_names = ["get"]
    serializer_class = serializers.BatchStageHistorySerializer    
    
    def get_queryset(self):
        queryset = BatchStageHistory.objects.all()
        batch = self.request.query_params.get("batch")
        
        if batch:
            try:
                batch = int(batch)
            except (TypeError, ValueError):
                raise ValidationError(
                    "batch must be an integer."
                )    
            queryset = BatchStageHistory.objects.filter(batch_id = batch)
        
        return queryset     
    
class BatchQcStageSummaryViewSet(ModelViewSet):
    http_method_names = ["get"]
    serializer_class = serializers.BatchQcStageSummarySerializer
    
    def get_queryset(self):
        queryset = BatchQcStageSummary.objects.all()

        batch = self.request.query_params.get("batch")
        stage = self.request.query_params.get("stage")

        # When batch is provided in the query params
        if batch is not None:
            try:
                batch = int(batch)
            except (TypeError, ValueError):
                raise ValidationError("batch must be an integer.")
            queryset = queryset.filter(batch_id=batch)

        # When stage is provided in the query params
        if stage:
            queryset = queryset.filter(stage=stage)

        return queryset
    
class RejectionViewSet(ModelViewSet):
    http_method_names = ["get","post","delete","patch"]

    def get_serializer_class(self):
        if self.request.method =="PATCH":
            return serializers.UpdateRejectionSerializer
        else:
            return serializers.RejectionSerializer
        
    def get_queryset(self):
        queryset = Rejection.objects.all() 
        batch = self.request.query_params.get("batch")

        if batch is not None:
            try:
                batch = int(batch)
            except (TypeError, ValueError):
                raise ValidationError("batch must be an integer.")
            queryset = queryset.filter(batch_id = batch)

        return queryset
    
    def destroy(self, request, *args, **kwargs):
        stage = request.query_params.get("stage")
        
        if not stage:
            raise ValidationError("You must define stage")

        instance = self.get_object()
        
        # Check the batch stage and status
        try:
            BatchStage.objects.get(batch=instance.batch, current_stage=stage, current_status="in")      
        except BatchStage.DoesNotExist:
            raise ValidationError(f"The batch must be in {stage} and the current status should be in")
        
        with transaction.atomic():
            summary = BatchQcStageSummary.objects.filter(
                batch=instance.batch,
                stage=stage
            ).first()

            if summary:
                if summary.rejection_count <= 1:
                    summary.delete()
                else:
                    summary.rejection_count = F("rejection_count") - 1
                    summary.last_update = timezone.now()
                    summary.save(update_fields=["rejection_count", "last_update"])

            instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def update(self, request, *args, **kwargs):
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)  
    


    
