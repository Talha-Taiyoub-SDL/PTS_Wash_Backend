from django.db import transaction, IntegrityError
from django.db.models import Sum
from django.utils import timezone
from common.models import GarmentUnit
from .choices import BatchInputType, RejectionReason
from common.choices import GarmentUnitStatus
from common.utils import get_user_name
from .models import (
    Machine,
    Batch,
    BatchSource,
    BatchSourcePiece,
    Rejection,
    ProcessFirstWash,
    ProcessFirstWashHydro,
    ProcessFirstWashDryer,
)
from rest_framework import serializers


class SimpleBatchSerializer(serializers.ModelSerializer):
    rejection_count = serializers.SerializerMethodField(
        method_name="get_rejection_count", read_only=True
    )
    total_quantity = serializers.SerializerMethodField(
        method_name="get_total_quantity", read_only=True
    )

    class Meta:
        model = Batch
        fields = [
            "id",
            "buyer",
            "color",
            "shade",
            "stage",
            "type",
            "rejection_count",
            "total_quantity",
        ]

    def get_rejection_count(self, instance: Batch):
        return instance.rejections.count()

    def get_total_quantity(self, instance: Batch):
        return instance.sources.aggregate(total=Sum("quantity"))["total"] or 0


class BatchQcSerializer(serializers.ModelSerializer):
    batch = SimpleBatchSerializer(read_only=True)

    class Meta:
        model = BatchSource
        fields = ["source", "batch", "quantity", "rewash_quantity"]
        read_only_fields = ["source", "quantity"]

    def update(self, instance: BatchSource, validated_data):
        instance.rewash_quantity = validated_data["rewash_quantity"]
        instance.save(update_fields=["rewash_quantity"])
        return instance


class BatchSourceInputSerializer(serializers.Serializer):
    # When the input type is aggregate, then mpo, style, so, and quantity is needed.
    mpo = serializers.CharField(required=False)
    style = serializers.CharField(required=False)
    so = serializers.CharField(required=False)
    quantity = serializers.IntegerField(required=False)

    # When the input type is pieces, then only garment_unit is needed
    garment_unit = serializers.PrimaryKeyRelatedField(
        queryset=GarmentUnit.objects.all(), required=False
    )


class BatchSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchSource
        fields = [
            "id",
            "mpo",
            "style",
            "so",
            "quantity",
            "rewash_quantity",
            "rejection_quantity",
        ]
        read_only_fields = ["batch"]


class BatchSerializer(serializers.ModelSerializer):
    sources = BatchSourceSerializer(many=True, read_only=True)

    input_type = serializers.ChoiceField(
        choices=BatchInputType.choices, write_only=True
    )
    input_sources = BatchSourceInputSerializer(many=True, write_only=True)

    class Meta:
        model = Batch
        fields = [
            "id",
            "buyer",
            "color",
            "shade",
            "stage",
            "type",
            "status",
            "total_quantity",
            "total_rewash_quantity",
            "total_rejection_quantity",
            "created_at",
            "operator",
            "sources",
            "input_type",
            "input_sources",
        ]
        read_only_fields = ["id", "operator"]

    def create(self, validated_data):
        input_type = validated_data.pop("input_type")
        input_sources = validated_data.pop("input_sources", [])

        if not input_sources:
            raise serializers.ValidationError(
                {"input_sources": "At least one source is required to create a batch."}
            )

        with transaction.atomic():
            batch = Batch.objects.create(
                **validated_data, operator=get_user_name(self.context["request"])
            )

            if input_type == BatchInputType.AGGREGATE:
                batch_sources = [
                    BatchSource(
                        batch=batch,
                        mpo=source["mpo"],
                        style=source["style"],
                        so=source["so"],
                        quantity=source["quantity"],
                    )
                    for source in input_sources
                ]

                BatchSource.objects.bulk_create(batch_sources)

            # When input type is pieces
            else:
                grouped_sources = []
                group_map = {}

                for source in input_sources:
                    garment_unit = source["garment_unit"]

                    key = (garment_unit.mpo, garment_unit.style, garment_unit.so)

                    if key not in group_map:
                        group_map[key] = {
                            "mpo": garment_unit.mpo,
                            "style": garment_unit.style,
                            "so": garment_unit.so,
                            "garment_units": [],
                        }

                        grouped_sources.append(group_map[key])

                    group_map[key]["garment_units"].append(garment_unit)

                for grouped_source in grouped_sources:
                    batch_source = BatchSource.objects.create(
                        batch=batch,
                        mpo=grouped_source["mpo"],
                        style=grouped_source["style"],
                        so=grouped_source["so"],
                        quantity=len(grouped_source["garment_units"]),
                    )

                    for garment_unit in grouped_source["garment_units"]:
                        BatchSourcePiece.objects.create(
                            batch_source=batch_source, garment_unit=garment_unit
                        )

            total = batch.sources.aggregate(total=Sum("quantity"))["total"]
            batch.total_quantity = total
            batch.save(update_fields=["total_quantity"])

            return batch


# Below is the line
class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = ["machine_number", "SAP", "added_at"]


class ProcessFirstWashSerializer(serializers.ModelSerializer):
    batch = SimpleBatchSerializer(read_only=True)
    machine = MachineSerializer(read_only=True)

    class Meta:
        model = ProcessFirstWash
        fields = [
            "id",
            "batch",
            "machine",
            "standard_time",
            "loading_start",
            "loading_started_by",
            "loading_finish",
            "loading_finished_by",
            "process_finish",
            "process_finished_by",
            "unload_finish",
            "unload_finished_by",
        ]


class CreateProcessFirstWashSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessFirstWash
        fields = ["batch", "machine", "standard_time"]

    def create(self, validated_data):
        first_wash = ProcessFirstWash.objects.create(
            **validated_data, loading_started_by=get_user_name(self.context["request"])
        )
        return first_wash


class UpdateProcessFirstWashSerializer(serializers.ModelSerializer):
    state = serializers.CharField(max_length=100, write_only=True)

    class Meta:
        model = ProcessFirstWash
        fields = ["state"]

    def update(self, instance: ProcessFirstWash, validated_data):
        # Map of timestamp fields to the user field who completed them
        timestamp_to_user_field = {
            "loading_finish": "loading_finished_by",
            "process_finish": "process_finished_by",
            "unload_finish": "unload_finished_by",
        }

        state_field = validated_data.get("state")
        if state_field not in timestamp_to_user_field:
            raise serializers.ValidationError("You have to provide a validated state")

        # Check if the state has already been completed
        if getattr(instance, state_field) is not None:
            raise serializers.ValidationError("You've already completed this state")

        # Get the corresponding "finished by" field
        finished_by_field = timestamp_to_user_field[state_field]

        # Update timestamp and user who finished it
        setattr(instance, state_field, timezone.now())
        setattr(instance, finished_by_field, get_user_name(self.context["request"]))
        instance.save(update_fields=[state_field, finished_by_field])

        return instance


class ProcessFirstWashHydroSerializer(serializers.ModelSerializer):
    batch = SimpleBatchSerializer(read_only=True)

    class Meta:
        model = ProcessFirstWashHydro
        fields = [
            "id",
            "batch",
            "machine",
            "standard_time",
            "hydro_in",
            "hydro_in_by",
            "hydro_out",
            "hydro_out_by",
        ]


class CreateProcessFirstWashHydroSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessFirstWashHydro
        fields = ["batch", "machine", "standard_time"]

    def create(self, validated_data):
        # Check if Process First Wash is done or not
        try:
            ProcessFirstWash.objects.get(batch=validated_data["batch"])
        except ProcessFirstWash.DoesNotExist:
            raise serializers.ValidationError(
                "You've to complete first wash cycle first"
            )

        first_wash_hydro = ProcessFirstWashHydro.objects.create(
            **validated_data, hydro_in_by=get_user_name(self.context["request"])
        )
        return first_wash_hydro


class UpdateProcessFirstWashHydroSerializer(serializers.ModelSerializer):
    state = serializers.CharField(max_length=100, write_only=True)

    class Meta:
        model = ProcessFirstWashHydro
        fields = ["state"]

    def update(self, instance: ProcessFirstWashHydro, validated_data):
        state = validated_data["state"]

        if state != "hydro_out":
            raise serializers.ValidationError("You have to provide validated state")

        if getattr(instance, state) is not None:
            raise serializers.ValidationError("You've already completed this state")

        instance.hydro_out = timezone.now()
        instance.hydro_out_by = get_user_name(self.context["request"])
        instance.save(update_fields=["hydro_out", "hydro_out_by"])

        return instance


class ProcessFirstWashDryerSerializer(serializers.ModelSerializer):
    # We will not take input for this field from the frontend.
    dryer_in_by = serializers.CharField(max_length=100, read_only=True)

    class Meta:
        model = ProcessFirstWashDryer
        fields = [
            "id",
            "batch",
            "machine",
            "standard_time",
            "type",
            "dryer_in",
            "dryer_in_by",
            "dryer_out",
            "dryer_out_by",
        ]

    # Replace the batch ID with its nested serialized data in responses,
    # while still allowing it to be written as a primary key during create.
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["batch"] = SimpleBatchSerializer(instance.batch).data
        return representation

    def create(self, validated_data):
        # Check if Hydro is done or not
        try:
            ProcessFirstWashHydro.objects.get(batch=validated_data["batch"])
        except ProcessFirstWashHydro.DoesNotExist:
            raise serializers.ValidationError("You've to complete Hydro first")

        # Without completing tumble, you can't do oven or conve
        # if validated_data["type"] == "oven" or "tumble":
        #     try:
        #         ProcessFirstWashDryer.objects.get(batch=validated_data["batch"])
        #     except ProcessFirstWashDryer.DoesNotExist:
        #         raise serializers.ValidationError("You've to complete Conveyor first")

        first_wash_dryer = ProcessFirstWashDryer.objects.create(
            **validated_data, dryer_in_by=get_user_name(self.context["request"])
        )
        return first_wash_dryer


class UpdateProcessFirstWashDryerSerializer(serializers.ModelSerializer):
    state = serializers.CharField(max_length=100, write_only=True)

    class Meta:
        model = ProcessFirstWashDryer
        fields = ["state"]

    def update(self, instance: ProcessFirstWashDryer, validated_data):
        state = validated_data["state"]

        if state != "dryer_out":
            raise serializers.ValidationError("You have to provide validated state")

        if getattr(instance, state) is not None:
            raise serializers.ValidationError("You've already completed this state")

        instance.dryer_out = timezone.now()
        instance.dryer_out_by = get_user_name(self.context["request"])
        instance.save(update_fields=["dryer_out", "dryer_out_by"])

        return instance


class RewashSourceSerializer(serializers.Serializer):
    batch_source = serializers.PrimaryKeyRelatedField(
        queryset=BatchSource.objects.all()
    )
    rewash_quantity = serializers.IntegerField(min_value=1)


class BatchRewashSerializer(serializers.Serializer):
    sources = RewashSourceSerializer(many=True)

    # def validate(self, data):
    #     batch = self.context["batch"]

    #     source_ids = [
    #         source["batch_source_id"]
    #         for source in data["sources"]
    #     ]

    #     batch_sources = BatchSource.objects.filter(
    #         id__in=source_ids,
    #         batch=batch
    #     )

    #     batch_source_map = {
    #         source.id: source
    #         for source in batch_sources
    #     }

    #     for source_data in data["sources"]:
    #         batch_source = batch_source_map.get(
    #             source_data["batch_source_id"]
    #         )

    #         if not batch_source:
    #             raise serializers.ValidationError({
    #                 "sources": "Invalid batch source."
    #             })

    #         if source_data["rewash_quantity"] > batch_source.quantity:
    #             raise serializers.ValidationError({
    #                 "rewash_quantity":
    #                 f"Rewash quantity cannot exceed quantity for source {batch_source.id}"
    #             })

    #     data["batch_source_map"] = batch_source_map

    #     return data

    def save(self):
        batch = self.context["batch"]

        sources = self.validated_data["sources"]
        # batch_source_map = self.validated_data["batch_source_map"]

        # for source_data in sources:
        #     batch_source = batch_source_map[
        #         source_data["batch_source_id"]
        #     ]

        #     batch_source.rewash_quantity = source_data["rewash_quantity"]

        # BatchSource.objects.bulk_update(
        #     batch_source_map.values(),
        #     ["rewash_quantity"]
        # )

        for source in sources:
            batch_source = source["batch_source"]
            batch_source.rewash_quantity = source["rewash_quantity"]
            batch_source.save(update_fields=["rewash_quantity"])

        batch.total_rewash_quantity = sum(
            batch.sources.values_list("rewash_quantity", flat=True)
        )

        batch.save(update_fields=["total_rewash_quantity"])

        return batch


class RejectionSourceSerializer(serializers.Serializer):
    garment_unit = serializers.PrimaryKeyRelatedField(
        queryset=GarmentUnit.objects.all()
    )
    rejection_reason = serializers.ChoiceField(choices=RejectionReason.choices)


class RejectionSerializer(serializers.Serializer):
    sources = RejectionSourceSerializer(many=True)

    def save(self, **kwargs):
        batch = self.context["batch"]
        sources = self.validated_data["sources"]

        with transaction.atomic():
            for source in sources:
                garment_unit = source["garment_unit"]
                rejection_reason = source["rejection_reason"]

                try:
                    batch_source = batch.sources.get(
                        mpo=garment_unit.mpo,
                        style=garment_unit.style,
                        so=garment_unit.so,
                    )
                except BatchSource.DoesNotExist:
                    raise serializers.ValidationError(
                        {
                            "garment_unit": f"Garment {garment_unit.individual_barcode} is not part of this batch"
                        }
                    )

                try:
                    Rejection.objects.create(
                        batch_source=batch_source,
                        garment_unit=garment_unit,
                        rejection_reason=rejection_reason,
                        operator=get_user_name(self.context["request"]),
                    )

                except IntegrityError:
                    raise serializers.ValidationError(
                        {
                            "garment_unit": f"Garment {garment_unit.individual_barcode} is already rejected"
                        }
                    )

                garment_unit.status = GarmentUnitStatus.REJECTED
                garment_unit.save(update_fields=["status"])

                batch_source.rejection_quantity += 1
                batch_source.save(update_fields=["rejection_quantity"])

            batch.total_rejection_quantity = sum(
                batch.sources.values_list("rejection_quantity", flat=True)
            )

            batch.save(update_fields=["total_rejection_quantity"])

        return batch
