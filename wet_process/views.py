from django.shortcuts import get_object_or_404
from .models import (
    Machine,
    Batch,
    BatchSource,
    ProcessFirstWashDryer,
    ProcessFirstWash,
    ProcessFirstWashHydro,
)
from .serializers import (
    CreateProcessFirstWashSerializer,
    MachineSerializer,
    BatchSerializer,
    BatchQcSerializer,
    ProcessFirstWashDryerSerializer,
    ProcessFirstWashSerializer,
    RejectionSerializer,
    UpdateProcessFirstWashDryerSerializer,
    UpdateProcessFirstWashSerializer,
    ProcessFirstWashHydroSerializer,
    CreateProcessFirstWashHydroSerializer,
    UpdateProcessFirstWashHydroSerializer,
    BatchRewashSerializer,
)
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import APIView
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


class BatchViewSet(ModelViewSet):
    http_method_names = ["get", "post"]
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer


class BatchQcViewSet(ModelViewSet):
    http_method_names = ["get", "patch"]

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


class BatchRewashView(APIView):
    def patch(self, request, pk):
        batch = get_object_or_404(Batch, pk=pk)

        serializer = BatchRewashSerializer(data=request.data, context={"batch": batch})

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
