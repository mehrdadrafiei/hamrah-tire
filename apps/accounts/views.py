from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserCreateSerializer

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer