from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from production.models import Batch,ReceivedBundle
from production.serializers import get_user_name
from .models import Machine, Batch, BatchSource, InternalBatch
from rest_framework import serializers

class SimpleBatchSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Batch
        fields = ["id", "buyer", "color", "shade", "stage", "type"]

class BatchQcSerializer(serializers.ModelSerializer):
    source = serializers.SerializerMethodField(method_name="get_source",read_only=True)
    batch = SimpleBatchSerializer(read_only=True)
    
    class Meta:
        model = BatchSource
        fields = ["source","batch","quantity","rewash_quantity"]
        read_only_fields = ["source", "quantity"]
    
    def get_source(self, instance:BatchSource):
        return {
            "id": instance.id,
            "mpo": instance.source_object.mpo,
            "style": instance.source_object.style,
            "so": instance.source_object.so   
        }
    
    def update(self, instance:BatchSource, validated_data):
        instance.rewash_quantity = validated_data["rewash_quantity"]
        instance.save(update_fields=["rewash_quantity"])
        return instance
        
class BatchSourceInputSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["internal","bundle"])
    id = serializers.IntegerField(required=False)
    
    mpo = serializers.CharField(required=False)
    style = serializers.CharField(required=False)
    so = serializers.CharField(required=False)
    
    quantity = serializers.IntegerField()
    
class BatchSourceSerializer(serializers.ModelSerializer):
    source = serializers.SerializerMethodField(method_name="get_source", read_only=True)
    
    class Meta:
        model = BatchSource
        fields = ["id","source","quantity"]
        read_only_fields = ["batch"]
    
    def get_source(self, instance:BatchSource):
        return {
            "mpo": instance.source_object.mpo,
            "style": instance.source_object.style,
            "so": instance.source_object.so   
        }
 
class BatchSerializer(serializers.ModelSerializer):
    sources = BatchSourceSerializer(many=True, read_only=True)
    sources_input = BatchSourceInputSerializer(many=True, write_only=True)
    
    class Meta:
        model = Batch
        fields = ["id", "buyer", "color", "shade", "stage", "type", "created_at", "created_by", "sources", "sources_input"]
        read_only_fields = ["created_by"]
        
    def create(self, validated_data):
        sources_data = validated_data.pop("sources_input", [])
        if not sources_data:
            raise serializers.ValidationError({
                "sources_input": "At least one source is required to create a batch."
            })
        
        with transaction.atomic():
            batch = Batch.objects.create(**validated_data, created_by=get_user_name(self.context["request"]))
            
            for source in sources_data:
                source_type = source["type"]
                quantity = source["quantity"]

                if source_type == "bundle":
                    try:
                        bundle = ReceivedBundle.objects.get(id=source["id"])
                    except ReceivedBundle.DoesNotExist:
                        raise serializers.ValidationError({
                            "sources_input": f"Bundle with id {source['id']} does not exist."
                        }) 
                    content_type = ContentType.objects.get_for_model(ReceivedBundle)

                    BatchSource.objects.create(
                        batch=batch,
                        content_type=content_type,
                        object_id=bundle.id,
                        quantity=quantity
                    )

                elif source_type == "internal":
                    internal, created = InternalBatch.objects.get_or_create(
                        mpo=source["mpo"],
                        style=source["style"],
                        so=source["so"]
                    )
                    content_type = ContentType.objects.get_for_model(InternalBatch)

                    BatchSource.objects.create(
                        batch=batch,
                        content_type=content_type,
                        object_id=internal.id,
                        quantity=quantity
                    )

            return batch    
        
        
# Below is the line 
class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = ["machine_number","SAP","added_at"]
         
# class ProcessFirstWashSerializer(serializers.ModelSerializer):
#     batch = SimpleBatchSerializer(read_only=True)
#     machine = MachineSerializer(read_only=True)
    
#     class Meta:
#         model = ProcessFirstWash
#         fields = ["id","batch","machine","loading_start","loading_started_by","loading_finish","loading_finished_by","process_finish","process_finished_by","unload_finish","unload_finished_by"]

# class CreateProcessFirstWashSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ProcessFirstWash   
#         fields = ["batch","machine"]
        
#     def create(self, validated_data):
#         first_wash = ProcessFirstWash.objects.create(**validated_data,loading_started_by = get_user_name(self.context["request"]))
#         return first_wash
    
# class UpdateProcessFirstWashSerializer(serializers.ModelSerializer):
#     state = serializers.CharField(max_length=100, write_only=True)
    
#     class Meta:
#         model = ProcessFirstWash
#         fields = ["state"]
        
#     def update(self, instance: ProcessFirstWash, validated_data):
#         # Map of timestamp fields to the user field who completed them
#         timestamp_to_user_field = {
#             "loading_finish": "loading_finished_by",
#             "process_finish": "process_finished_by",
#             "unload_finish": "unload_finished_by"
#         }

#         state_field = validated_data.get("state")
#         if state_field not in timestamp_to_user_field:
#             raise serializers.ValidationError("You have to provide a validated state")

#         # Check if the state has already been completed
#         if getattr(instance, state_field) is not None:
#             raise serializers.ValidationError("You've already completed this state")

#         # Get the corresponding "finished by" field
#         finished_by_field = timestamp_to_user_field[state_field]

#         # Update timestamp and user who finished it
#         setattr(instance, state_field, timezone.now())
#         setattr(instance, finished_by_field, get_user_name(self.context["request"]))
#         instance.save(update_fields=[state_field, finished_by_field])

#         return instance
        
# class ProcessFirstWashHydroSerializer(serializers.ModelSerializer):
#     batch = SimpleBatchSerializer(read_only=True)
    
#     class Meta:
#         model = ProcessFirstWashHydro
#         fields = ["id","batch","machine","hydro_in","hydro_in_by","hydro_out","hydro_out_by"]
        
# class CreateProcessFirstWashHydroSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ProcessFirstWashHydro
#         fields = ["batch","machine"]       
    
#     def create(self, validated_data):
#         first_wash_hydro = ProcessFirstWashHydro.objects.create(**validated_data,hydro_in_by=get_user_name(self.context["request"]))            
#         return first_wash_hydro                               

# class UpdateProcessFirstWashHydroSerializer(serializers.ModelSerializer):
#     state = serializers.CharField(max_length=100)
#     class Meta:
#         model = ProcessFirstWashHydro
#         fields = ["state"]    
    
#     def update(self, instance:ProcessFirstWashHydro, validated_data):
#         state = validated_data["state"]
        
#         if state != "hydro_out":
#             raise serializers.ValidationError("You have to provide validated state")
        
#         if getattr(instance,state) is not None:
#             raise serializers.ValidationError("You've already completed this state")
    
#         instance.hydro_out = timezone.now()
#         instance.hydro_out_by = get_user_name(self.context["request"])
#         instance.save(update_fields=["hydro_out","hydro_out_by"])
        
#         return instance
    
# class ProcessFirstWashDryerSerializer(serializers.ModelSerializer):
#     # We will not take input for this field from the frontend.
#     dryer_in_by = serializers.CharField(max_length=100, read_only=True)
    
#     class Meta:
#         model = ProcessFirstWashDryer
#         fields = ["id","batch","machine","type","dryer_in","dryer_in_by","dryer_out","dryer_out_by"]
        
#     # Replace the batch ID with its nested serialized data in responses,
#     # while still allowing it to be written as a primary key during create.
#     def to_representation(self, instance):
#         representation = super().to_representation(instance)
#         representation["batch"] = SimpleBatchSerializer(
#             instance.batch
#         ).data
#         return representation
    
#     def create(self, validated_data):
#         first_wash_dryer = ProcessFirstWashDryer.objects.create(**validated_data, dryer_in_by = get_user_name(self.context["request"]))
#         return first_wash_dryer        
   
# class UpdateProcessFirstWashDryerSerializer(serializers.ModelSerializer):
#     state = serializers.CharField(max_length=100)
    
#     class Meta:
#         model= ProcessFirstWashDryer
#         fields = ["state"]
        
#     def update(self, instance:ProcessFirstWashDryer, validated_data):
#         state = validated_data["state"]
        
#         if state != "dryer_out":
#             raise serializers.ValidationError("You have to provide validated state")
        
#         if getattr(instance,state) is not None:
#             raise serializers.ValidationError("You've already completed this state")
    
#         instance.dryer_out = timezone.now()
#         instance.dryer_out_by = get_user_name(self.context["request"])
#         instance.save(update_fields=["dryer_out","dryer_out_by"])
        
#         return instance
                        
# class RejectionSerializer(serializers.ModelSerializer):
#     content_type = serializers.CharField(max_length=100)
#     class Meta:
#         model = Rejection
#         fields = ["id","individual_barcode","reason","stage","rejected_at","rejected_by","content_type","object_id"]
#         read_only_fields = ["rejected_by", "source_batch"]
    
#     def to_representation(self, instance:Rejection):
#         representation= super().to_representation(instance)
#         representation["content_type"] = instance.content_type.model
#         return representation
        
#     def create(self, validated_data):
#         content_type = ContentType.objects.get(model=validated_data.pop("content_type", None))
        
#         rejection = Rejection.objects.create(**validated_data, rejected_by=get_user_name(self.context["request"]),content_type=content_type)
        
#         #update the rejection quantity in the wash log
#         rejection.source_batch.logs.update(rejections=F("rejections") + 1)
#         return rejection

# class WashLogSerializer(serializers.ModelSerializer):
#     batch_details = serializers.SerializerMethodField(method_name="get_batch_details", read_only=True)
#     class Meta:
#         model = WashLog
#         fields = ["id", "content_type", "object_id", "batch_details", "total_quantity", "rejections", "rewash_quantity", "remaining_rewash_quantity", "status"]  
    
#     def get_batch_details(self,instance:WashLog):
#         batch = instance.source_batch
#         return {
#             "buyer": batch.buyer,
#             "color": batch.color,
#             "shade": batch.shade
#         }
    
#     def to_representation(self, instance:WashLog):
#         representation = super().to_representation(instance)
#         representation["content_type"] = instance.content_type.model
#         return representation  
    
# class UpdateWashLogSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = WashLog
#         fields = ["rewash_quantity"]
#         read_only_fields = ["content_type","object_id","total_quantity"]
        
#     def update(self, instance:WashLog, validated_data):
#         new_rewash_quantity = validated_data["rewash_quantity"]
#         increased_amount = new_rewash_quantity - instance.rewash_quantity

#         WashLog.objects.filter(id=instance.id).update(
#             remaining_rewash_quantity=F("remaining_rewash_quantity") + increased_amount,
#             rewash_quantity=new_rewash_quantity
#         )

#         instance.refresh_from_db()
#         return instance
        
            
                                                            