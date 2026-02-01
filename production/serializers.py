from .import models
from rest_framework import serializers
from django.db import transaction
from django.db.models import F
from django.utils import timezone


def get_user_name(request):
    return (
        request.user.username
        if request.user.is_authenticated
        else "system"
    )

class StageNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StageName
        fields = ["id","stage","last_update"]

class PlanningRouteStepSerializer(serializers.ModelSerializer):
    class Meta:
        model= models.PlanningRouteStep
        fields = ["id","sequence","stage"]

class UpdatePlanningSerializer(serializers.ModelSerializer):
    stages = serializers.ListField(
        child=serializers.CharField(),
        write_only=True
    )
    class Meta:
        model= models.Planning
        fields = ["stages"]
    
    def update(self, instance:models.Planning, validated_data):
        
        # If any of the batches of this mpo is already in the processing, we won't update the route plan  
        if models.BatchStage.objects.filter(batch__mpo=instance.mpo).exists():
            raise serializers.ValidationError("You can't update this route plan cause already one of the batches of this mpo is in processing already.")
        
        else:
            with transaction.atomic():
                
                # Update the planning
                instance.updated_by = get_user_name(self.context["request"])
                instance.last_update = timezone.now()
                instance.save()
                
                # Delete the existing routes for this planning
                instance.route_steps.all().delete()
                
                # Create new routes for this planning
                models.PlanningRouteStep.objects.bulk_create([
                        models.PlanningRouteStep(
                            planning=instance,
                            sequence = index+1,
                            stage = stage
                        )
                        for (index,stage) in enumerate(validated_data["stages"])
                    ])
                
            return instance
    
class PlanningSerializer(serializers.ModelSerializer):
    route_steps = PlanningRouteStepSerializer(many=True, read_only = True)
    
    # Stages will be be sent by the client
    stages = serializers.ListField(
        child=serializers.CharField(),
        write_only=True
    )
    class Meta:
        model= models.Planning
        fields = ["id","mpo","updated_by","last_update","route_steps","stages"]
        read_only_fields = ["updated_by"]
           
    def create(self, validated_data):
        with transaction.atomic():
            # Create Planning
            planning = models.Planning.objects.create(
                mpo=validated_data["mpo"],
                updated_by=get_user_name(self.context["request"])
            )
            
            # Create Route Steps for the created Planning
            models.PlanningRouteStep.objects.bulk_create([
                models.PlanningRouteStep(
                    planning=planning,
                    sequence = index+1,
                    stage = stage
                )
                for (index,stage) in enumerate(validated_data["stages"])
            ])
            
            return planning
        
class ReceivedBundleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ReceivedBundle
        fields = ["id","mpo","buyer","style","marker","bundle_no","bundle_barcode","size","shade","color","quantity","received_at","received_by","status"]
        read_only_fields = ("received_by", "status", "received_at")
                  
    def create(self, validated_data):
        validated_data ["received_by"] = get_user_name(self.context["request"])
        return super().create(validated_data)    
    
class BatchBundleSerializer(serializers.ModelSerializer):
    quantity = serializers.SerializerMethodField(method_name="get_quantity", read_only=True)
    bundle_no = serializers.SerializerMethodField(method_name="get_bundle_no", read_only= True)
    received = ReceivedBundleSerializer(read_only=True)##Fahad
    class Meta:
        model = models.BatchBundle
        # Mainly bundle_no and quantity will be showed in the frontend
        fields = ["id","batch_id","received_id","bundle_no","quantity","added_at","received"]
    
    def get_bundle_no(self, batch_bundle):
        return batch_bundle.received.bundle_no     
        
    def get_quantity(self, batch_bundle):
        return batch_bundle.received.quantity
       
class BatchSerializer(serializers.ModelSerializer):
    updated_at = serializers.SerializerMethodField(method_name="get_updated_at",read_only=True)
    planning = PlanningSerializer(read_only=True)
    batch_bundles = BatchBundleSerializer(many=True,read_only=True)
    total_quantity = serializers.SerializerMethodField(method_name="get_total_quantity",read_only=True)
    scanned_bundles = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    
    class Meta:
        model = models.Batch
        fields = ["id","mpo","size","color","batch_bundles","total_quantity","planning","updated_at","updated_by","scanned_bundles"]
        read_only_fields = ("mpo","size","color","updated_by")
    
    def get_updated_at(self, obj):
        # return obj.updated_at.strftime("%d-%m-%Y %I:%M%p")
        return obj.updated_at.strftime("%Y%m%d")
    
    def get_total_quantity(self, batch):
        total = 0 
        for bundle in batch.batch_bundles.all():
            total+= bundle.received.quantity
        
        return total 
    
    def create(self, validated_data):
        scanned_ids = validated_data.pop("scanned_bundles")
        
        # Empty bundle list is not allowed
        if not scanned_ids:
            raise serializers.ValidationError(
                "You must add at least one bundle to create a batch."
            )
            
        # Duplicate bundle IDs are not allowed
        if len(scanned_ids) != len(set(scanned_ids)):
            raise serializers.ValidationError(
                "Duplicate bundle IDs are not allowed."
            )    
            
        received_queryset = models.ReceivedBundle.objects.filter(id__in=scanned_ids)

        # Check if all the scanned bundles exist or not
        if received_queryset.count() != len(scanned_ids):
            raise serializers.ValidationError(
                "One or more bundles do not exist in the received section."
            )
        
        # Check if any of the bundles is allocated       
        if received_queryset.filter(
            status=models.ReceivedBundle.STATUS_ALLOCATED
        ).exists():
            raise serializers.ValidationError(
                "One or more bundles are already allocated."
            )

        # Same MPO, Size, and Color Validation
        first = received_queryset.first()

        if not received_queryset.filter(
            mpo=first.mpo,
            size=first.size,
            color=first.color,
        ).count() == received_queryset.count():
            raise serializers.ValidationError(
                "All bundles must have same MPO, size, and color."
            )
            
        # Fetch the planning id for this MPO
        try:
            planning = models.Planning.objects.get(mpo=first.mpo)
        except models.Planning.DoesNotExist:
            raise serializers.ValidationError(
                f"No planning found for MPO {first.mpo}"
            )
              
        with transaction.atomic():
            # Create Batch
            batch = models.Batch.objects.create(
                mpo=first.mpo,
                size=first.size,
                color=first.color,
                planning=planning,
                updated_by= get_user_name(self.context["request"]),
            )
            
            # Create Batch Bundles for the created batch
            models.BatchBundle.objects.bulk_create([
                models.BatchBundle(
                    batch=batch,
                    received=received_bundle
                )
                for received_bundle in received_queryset
            ]) 
            
            # Mark received bundles as allocated
            received_queryset.update(
                status=models.ReceivedBundle.STATUS_ALLOCATED
            )
            
            return batch   

class BatchStageHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BatchStageHistory
        fields = ["id","batch","stage","sequence","entered_at","closed_at","entered_by","closed_by"]

class BatchStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BatchStage
        fields = ["batch","current_stage","sequence","current_status","production_status"]
            
    def update(self, instance:models.BatchStage, validated_data):
        if instance.production_status == "closed":
                raise serializers.ValidationError("This batch is already out for production")
        
        # When the request is for Closed
        if validated_data["current_status"] == "closed":
            
            # Is the closing for the same stage
            if instance.sequence == validated_data["sequence"]:
                
                # If the same stage's status is In
                if instance.current_status == "in":
                    with transaction.atomic():   
                        try:
                            history = models.BatchStageHistory.objects.get(
                                sequence=instance.sequence,
                                batch=instance.batch
                            )
                        except models.BatchStageHistory.DoesNotExist:
                            raise serializers.ValidationError(
                                "It seems you didn't enter into this stage, so closing is not possible"
                            )
                        
                        # Update the stage    
                        for attr, value in validated_data.items():
                            setattr(instance, attr, value)
                        instance.save()
                        
                        # Update the stage history
                        history.closed_at = timezone.now()
                        history.closed_by = get_user_name(self.context["request"])
                        history.save()
    
                # When the stage is already closed    
                else:
                    raise serializers.ValidationError(f"{instance.current_stage} is already {instance.current_status}")
            
            # Is the closing is for the next stage
            elif instance.sequence < validated_data["sequence"]:
                raise serializers.ValidationError(f"You have to complete the previous stages first. Your current stage is {instance.current_stage} and current status is {instance.current_status}")
            
            # When the closing is for the previous stage
            else:    
                raise serializers.ValidationError(f"You have already completed this stage. Your current stage is {instance.current_stage} and current status is {instance.current_status}")
        
        # When the request is for In
        else:
            # Check if it's the next stage or not
            if instance.sequence < validated_data["sequence"]:
                
                # Check if it's actually the immediate next stage and if the previous stage is closed?
                if instance.sequence + 1 == validated_data["sequence"] and instance.current_status=="closed":
                    with transaction.atomic():
                        for attr, value in validated_data.items():
                            setattr(instance, attr, value)
                        instance.save()
                        
                        # Create history for this stage change
                        models.BatchStageHistory.objects.create(batch=instance.batch, stage=instance.current_stage, sequence=instance.sequence, entered_at=timezone.now(), entered_by=get_user_name(self.context["request"]))
                
                # When it's not the immediate next stage    
                else:
                    route = instance.batch.planning.route_steps.get(sequence = instance.sequence + 1)
                    raise serializers.ValidationError(f"Your current stage is {instance.current_stage} and the current staus is {instance.current_status}. You have to close the current stage to go to the next stage, and your next stage is {route.stage}")
                
            # Check if it's the same stage    
            elif instance.sequence == validated_data["sequence"]:
                    raise serializers.ValidationError(f"You're already in {instance.current_stage} and the status is {instance.current_status}")    
            
            # If it's the previous stage        
            else:
                raise serializers.ValidationError(f"You've already completed this stage, your current stage is {instance.current_stage} and the status is {instance.current_status}")
        
        return instance    
          
    def create(self, validated_data):
        sequence = validated_data["sequence"]
        current_status = validated_data ["current_status"]
        
        if sequence == 1 and current_status == "in":
            with transaction.atomic(): 
                batch_stage = models.BatchStage.objects.create(**validated_data)
                
                # Now create corresponding stage history
                models.BatchStageHistory.objects.create(batch=batch_stage.batch, stage=batch_stage.current_stage,sequence=batch_stage.sequence, entered_at = timezone.now(), entered_by = get_user_name(self.context["request"]))
                
            return batch_stage
            
        else:
            batch = validated_data["batch"]
            route = batch.planning.route_steps.get(sequence=1)
            raise serializers.ValidationError(f"Please follow the route plan. Your first stage is {route.stage} and first task should be in")
                
class BatchQcStageSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BatchQcStageSummary
        fields = ["id","batch","stage","rejection_count","last_update"]                
            
class RejectionSerializer(serializers.ModelSerializer):
    details = serializers.SerializerMethodField(method_name="get_details",read_only=True)
    
    class Meta:
        model = models.Rejection
        fields = ["id","individual_barcode","batch","stage","reason","rejected_at","rejected_by","details"]
        read_only_fields = ["batch","rejected_by"]
    
    def get_details(self,instance:models.Rejection):
        bundle_barcode = "8220" + instance.individual_barcode[0:12] + "001"

        try:
            bundle = models.ReceivedBundle.objects.get(bundle_barcode = bundle_barcode)
        except models.ReceivedBundle.DoesNotExist:
            raise serializers.ValidationError("Bundle of this specific garment doesn't exist. Something is wrong.")    
        
        return {
        "mpo": bundle.mpo,
        "marker": bundle.marker,
        "size": bundle.size,
        "shade": bundle.shade,
        "color": bundle.color,
        }
        
    def get_received_bundle(self,instance:models.Rejection):
        bundle_barcode = "8220" + instance.individual_barcode[0:12] + "001"
        bundle = models.ReceivedBundle.objects.get(bundle_barcode = bundle_barcode)
        return bundle
            
    def create(self, validated_data):
        individual_barcode = validated_data["individual_barcode"]
        if not isinstance(individual_barcode, str) or len(individual_barcode) < 12:
            raise serializers.ValidationError(
                "individual_barcode must be a string with at least 12 characters."
            )

        bundle_barcode = "8220" + individual_barcode[0:12] + "001"

        # Check if bundle of this specific garment is received yet or not
        try:
            bundle = models.ReceivedBundle.objects.get(bundle_barcode = bundle_barcode)
        except models.ReceivedBundle.DoesNotExist:
            raise serializers.ValidationError("Bundle of this individual garment is not in the received section yet")
               
        # Check if this bundle is assigned to a batch or not
        batch_bundle = getattr(bundle, "batch_bundle", None)
        if not batch_bundle:
            raise serializers.ValidationError("Bundle is not assigned to any batch.")

        batch = batch_bundle.batch

        # Check the batch stage and status
        try:
            models.BatchStage.objects.get(batch=batch, current_stage=validated_data["stage"], current_status="in")      
        except models.BatchStage.DoesNotExist:
            raise serializers.ValidationError(f"The batch must be in {validated_data['stage']} and the current status should be in")
        
        # Create Rejection and update BatchQcStageSummary
        with transaction.atomic():
            validated_data["batch"] = batch
            validated_data["rejected_by"] = get_user_name(
                self.context["request"]
            )

            rejection = models.Rejection.objects.create(**validated_data)

            summary, created = models.BatchQcStageSummary.objects.get_or_create(
                batch=rejection.batch,
                stage=rejection.stage,
                defaults={
                    "rejection_count": 1,
                    "last_update": timezone.now(),
                },
            )

            if not created:
                summary.rejection_count = F("rejection_count") + 1
                summary.last_update = timezone.now()
                summary.save(update_fields=["rejection_count", "last_update"])

        return rejection  
        
class UpdateRejectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Rejection
        fields = ["id","individual_barcode","batch","stage","reason","rejected_at","rejected_by"]
        read_only_fields = ["id","individual_barcode","batch","stage","rejected_at","rejected_by"]
    
    def update(self, instance, validated_data):
         instance.reason = validated_data["reason"]
         instance.rejected_at = timezone.now()
         instance.rejected_by = get_user_name(self.context["request"])
         instance.save(update_fields=["reason", "rejected_at", "rejected_by"])
         return instance