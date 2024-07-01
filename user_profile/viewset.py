from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from authentication.models import Account
from user_profile.serializers import ProfileSerializer, TeacherProfileSerializer, StudentProfileSerializer


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = ProfileSerializer  # Use ProfileSerializer for dynamic role-based serialization
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    def list(self, request, *args, **kwargs):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'], url_path='avatar')
    def avatar(self, request, *args, **kwargs):
        user = request.user
        if user.avatar:
            avatar_url = request.build_absolute_uri(user.avatar.url)
        else:
            avatar_url = None
        return Response({"avatar_url": avatar_url}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'], url_path='profile')
    def profile(self, request, *args, **kwargs):
        user = request.user
        serializer = ProfileSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
