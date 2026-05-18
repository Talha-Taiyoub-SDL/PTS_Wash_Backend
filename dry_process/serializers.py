from django.db import transaction, IntegrityError
from .models import TrackingHistory
from .choices import Action, RejectionReason
from rest_framework import serializers
from common.utils import get_user_name
from production.models import Planning, PlanningRouteStep
from common.models import GarmentUnit


class TrackingHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingHistory
        fields = [
            "id",
            "garment_unit",
            "stage",
            "action",
            "rejection_reason",
            "scanned_at",
            "operator",
        ]
        validators = []

    # Remove rejection_reason from the response if the action is not "rejected"
    def to_representation(self, instance):
        data = super().to_representation(instance)

        if instance.action != Action.REJECTED:
            data.pop("rejection_reason", None)

        return data

    def validate(self, data):
        garment_unit = data.get("garment_unit")
        stage = data.get("stage")
        action = data.get("action")

        # Check already rejected
        if garment_unit.status == Action.REJECTED:
            raise serializers.ValidationError(
                {"garment_unit": "This garment is already rejected"}
            )

        # Check if this stage is already completed
        if TrackingHistory.objects.filter(
            garment_unit=garment_unit, stage=stage, action=action
        ).exists():
            raise serializers.ValidationError(
                {
                    "non_field_errors": "This action already exists for this garment at this stage."
                }
            )

        # If the action is "rejected", rejection_reason must be included, otherwise not
        rejection_reason = data.get("rejection_reason")

        if action == Action.REJECTED and not rejection_reason:
            raise serializers.ValidationError(
                {"rejection_reason": "This field is required when action is REJECTED."}
            )

        if action != Action.REJECTED and rejection_reason:
            raise serializers.ValidationError(
                {"rejection_reason": "Should be empty unless action is REJECTED."}
            )

        return data

    # Use this function to create history and update garment unit's status
    def create_history(self, stage, action, garment_unit):
        with transaction.atomic():
            history = TrackingHistory.objects.create(
                **self.validated_data, operator=get_user_name(self.context["request"])
            )

            # Update garment unit's status
            if action == Action.REJECTED:
                status = Action.REJECTED
            else:
                status = stage + "_" + action

            garment_unit.status = status
            garment_unit.save(update_fields=["status"])

            return history

    def create(self, validated_data):
        garment_unit = validated_data["garment_unit"]
        stage = validated_data["stage"]
        action = validated_data["action"]

        # Check if planning exist for the MPO the garment belongs to
        try:
            planning = Planning.objects.get(mpo=garment_unit.mpo)

            # Check if this is a valid stage.
            try:
                route_step = planning.route_steps.get(stage=stage)

            except PlanningRouteStep.DoesNotExist:
                raise serializers.ValidationError(
                    {
                        "stage": "This stage does not exist for the MPO this garment belongs to"
                    }
                )

        except Planning.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "garment_unit": "Planning does not exist for the MPO this garment belongs to"
                }
            )

        # Create History for the specified action
        if action == Action.IN:
            # Whent it's the first stage, the garment unit's status must have to be "received"
            if route_step.sequence == 1:
                if garment_unit.status == "received":
                    return self.create_history(
                        stage=stage, action=action, garment_unit=garment_unit
                    )
                else:
                    raise serializers.ValidationError(
                        {"stage": "Please complete the stages accordingly"}
                    )

            # If it's not the first stage, then previous stage's out action must have to be completed
            elif (
                garment_unit.status
                == planning.route_steps.get(sequence=(route_step.sequence - 1)).stage
                + "_"
                + Action.OUT
            ):
                return self.create_history(
                    stage=stage, action=action, garment_unit=garment_unit
                )

            else:
                raise serializers.ValidationError(
                    {"stage": "Please complete the stages accordingly"}
                )

        elif action == Action.OUT:
            if garment_unit.status == route_step.stage + "_" + Action.IN:
                return self.create_history(
                    stage=stage, action=action, garment_unit=garment_unit
                )
            else:
                raise serializers.ValidationError(
                    {"stage": "Please complete the stages accordingly"}
                )

        elif action == Action.REJECTED:
            if garment_unit.status == route_step.stage + "_" + Action.IN:
                return self.create_history(
                    stage=stage, action=action, garment_unit=garment_unit
                )
            else:
                raise serializers.ValidationError(
                    {"stage": "Please complete the stages accordingly"}
                )


class RejectionItemSerializer(serializers.Serializer):
    garment_unit = serializers.PrimaryKeyRelatedField(
        queryset=GarmentUnit.objects.exclude(status=Action.REJECTED)
    )
    rejection_reason = serializers.ChoiceField(choices=RejectionReason.choices)


class RejectionSerializer(serializers.Serializer):
    rejection_items = RejectionItemSerializer(many=True)
    stage = serializers.CharField(max_length=100)

    def create(self, validated_data):
        stage = validated_data["stage"]
        rejection_items = validated_data["rejection_items"]

        # grab all the rejected garment units' barcodes
        barcode_list = [
            rejection_item["garment_unit"].individual_barcode
            for rejection_item in rejection_items
        ]

        histories = [
            TrackingHistory(
                garment_unit=rejection_item["garment_unit"],
                stage=stage,
                action=Action.REJECTED,
                rejection_reason=rejection_item["rejection_reason"],
                operator=get_user_name(self.context["request"]),
            )
            for rejection_item in rejection_items
        ]

        try:
            with transaction.atomic():
                TrackingHistory.objects.bulk_create(histories)

                # Update the garment units status to rejected
                GarmentUnit.objects.filter(individual_barcode__in=barcode_list).update(
                    status=Action.REJECTED
                )

                return histories

        except IntegrityError:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        "One or more garments are already rejected for this stage."
                    ]
                }
            )
