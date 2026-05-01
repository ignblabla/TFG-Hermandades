from rest_framework import generics
from rest_framework.permissions import AllowAny

from api.serializadores.hermano.hermano_serializer import UserSerializer

from django.contrib.auth import get_user_model

User = get_user_model()


class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]