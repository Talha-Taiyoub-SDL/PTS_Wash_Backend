from django.shortcuts import render
from .models import BatchForFirstWash
from .serializers import BatchForFirstWashSerializer
from rest_framework.viewsets import ModelViewSet
# Create your views here.

class BatchForFirstWashViewSet(ModelViewSet):
    queryset = BatchForFirstWash.objects.all().prefetch_related("source_batches")
    serializer_class = BatchForFirstWashSerializer
    