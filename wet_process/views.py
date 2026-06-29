from django.shortcuts import get_object_or_404
from .models import Machine, Batch, WashProcess, HydroProcess, DryerProcess
from .serializers import (
    BatchReceiveSerializer,
    MachineSerializer,
    BatchSerializer,
    RejectionSerializer,
    BatchRewashSerializer,
    UpdateBatchSerializer,
    WashProcessSerializer,
    CreateWashProcessSerializer,
    UpdateWashProcessSerializer,
    HydroProcessSerializer,
    CreateHydroProcessSerializer,
    UpdateHydroProcessSerializer,
    DryerProcessSerializer,
    CreateDryerProcessSerializer,
    UpdateDryerProcessSerializer,
)
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import APIView
# Create your views here.


class MachineViewSet(ModelViewSet):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer


class WashProcessViewSet(ModelViewSet):
    def get_queryset(self):
        queryset = WashProcess.objects.all()
        batch = self.request.query_params.get("batch")
        if batch:
            queryset = queryset.filter(batch=batch)

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateWashProcessSerializer
        elif self.request.method == "PATCH":
            return UpdateWashProcessSerializer
        else:
            return WashProcessSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        serializer = WashProcessSerializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        serializer = WashProcessSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HydroProcessViewSet(ModelViewSet):
    def get_queryset(self):
        queryset = HydroProcess.objects.all()
        batch = self.request.query_params.get("batch")
        if batch:
            queryset = queryset.filter(batch=batch)

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateHydroProcessSerializer
        elif self.request.method == "PATCH":
            return UpdateHydroProcessSerializer
        else:
            return HydroProcessSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        serializer = HydroProcessSerializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        serializer = HydroProcessSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DryerProcessViewSet(ModelViewSet):
    def get_queryset(self):
        queryset = DryerProcess.objects.all()
        batch = self.request.query_params.get("batch")
        type = self.request.query_params.get("type")

        if batch:
            queryset = queryset.filter(batch=batch)

        if type:
            queryset = queryset.filter(type=type)

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateDryerProcessSerializer
        elif self.request.method == "PATCH":
            return UpdateDryerProcessSerializer
        else:
            return DryerProcessSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        serializer = DryerProcessSerializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        serializer = DryerProcessSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BatchViewSet(ModelViewSet):
    http_method_names = ["get", "post", "patch"]
    queryset = Batch.objects.all()

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return UpdateBatchSerializer

        return BatchSerializer


# Write documentation about the logic of showing remaining rewash quantity per mpo, style, and so.
# BatchSource er moddhe giye proti batch source traverse kore dekhte hobe:
# (batch.stage = "first_wash" & batch.type="normal_wash" eder rewash_quantity (per mpo)) - (batch.stage = "first_wash" & batch.type = "rewash" er quantity per mpo)


class BatchRewashView(APIView):
    def patch(self, request, pk):
        batch = get_object_or_404(Batch, pk=pk)

        serializer = BatchRewashSerializer(data=request.data, context={"batch": batch})

        serializer.is_valid(raise_exception=True)
        batch = serializer.save()
        serializer = BatchSerializer(batch)

        return Response(serializer.data, status=status.HTTP_200_OK)


class BatchReceiveView(APIView):
    def patch(self, request, pk):
        batch = get_object_or_404(Batch, pk=pk)

        serializer = BatchReceiveSerializer(
            data=request.data, context={"batch": batch, "request": request}
        )

        serializer.is_valid(raise_exception=True)
        batch = serializer.save()
        serializer = BatchSerializer(batch)

        return Response(serializer.data, status=status.HTTP_200_OK)


class RejectionView(APIView):
    def post(self, request, pk):
        batch = get_object_or_404(Batch, pk=pk)

        serializer = RejectionSerializer(
            data=request.data, context={"batch": batch, "request": request}
        )
        serializer.is_valid(raise_exception=True)
        batch = serializer.save()
        serializer = BatchSerializer(batch)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
