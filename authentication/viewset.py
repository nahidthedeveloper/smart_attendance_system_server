from datetime import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Account, PasswordResetToken, OTP
from .utils import generate_otp
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import uuid

from authentication.serializers import EmptySerializer, LoginSerializer, ForgotPasswordSerializer, OTPSerializer, \
    PasswordResetSerializer


class AuthenticationViewSet(viewsets.ModelViewSet):
    serializer_class = []
    queryset = []

    def get_serializer_class(self):
        if self.action == 'login':
            return LoginSerializer
        elif self.action == 'forgot_password':
            return ForgotPasswordSerializer
        elif self.action == 'verify_otp':
            return OTPSerializer
        elif self.action == 'reset_password':
            return PasswordResetSerializer
        return EmptySerializer

    def list(self, request, *args, **kwargs):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'], url_path='login')
    def login(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = Account.objects.get(academic_id=serializer.validated_data['academic_id'])
            user.last_login = datetime.now()
            user.save()
            refresh = RefreshToken.for_user(user)

            return Response({
                'token': str(refresh.access_token),
                'role': user.role,
                'user': user.academic_id
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['POST'], url_path='forgot_password')
    def forgot_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            otp = generate_otp(user)
            username = "User"
            if user.name is not None:
                username = user.name

            # Send OTP via email
            subject = 'Your Password Reset OTP'
            message = (
                f'Hello {username},\n\nYour OTP for password reset is: {otp}\n\nOTP will expired after 5 minutes.\n\nIf '
                f'you did not request this, please ignore this email.')
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [user.email]
            send_mail(subject, message, email_from, recipient_list)

            return Response({'message': 'Check your email to get OTP'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='verify-otp')
    def verify_otp(self, request):
        serializer = OTPSerializer(data=request.data)
        if serializer.is_valid():
            otp_instance = serializer.validated_data['otp_instance']  # Access otp_instance
            user = otp_instance.user

            # Generate or update the PasswordResetToken
            token, created = PasswordResetToken.objects.get_or_create(user=user)
            if not created:
                token.token = uuid.uuid4()
                token.created_at = timezone.now()
                token.save()

            # Delete any old OTP instances for the user
            OTP.objects.filter(user=user).delete()

            return Response({
                "message": "OTP is valid. You can now reset your password.",
                "user_id": user.id,
                "token": str(token.token)
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='reset-password')
    def reset_password(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Delete the token after successful password reset
            reset_token = PasswordResetToken.objects.get(token=serializer.validated_data['token'])
            reset_token.delete()
            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
