from rest_framework import serializers
from .models import Account, OTP, PasswordResetToken
from django.utils import timezone
from datetime import timedelta


class EmptySerializer(serializers.Serializer):
    pass


class AccountSerializer(serializers.Serializer):
    class Meta:
        model = Account
        fields = ['academic_id', 'email', 'role', 'name', 'avatar', 'department']


class LoginSerializer(serializers.Serializer):
    academic_id = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        academic_id = attrs.get('academic_id')
        password = attrs.get('password')

        try:
            user = Account.objects.get(academic_id=academic_id, is_active=True)
        except Account.DoesNotExist:
            raise serializers.ValidationError({'password': 'ID or password is incorrect'})

        if not user.check_password(password):
            raise serializers.ValidationError({'password': 'ID or password is incorrect'})

        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    academic_id = serializers.CharField()

    def validate(self, attrs):
        academic_id = attrs['academic_id'].strip()
        print(len(academic_id))

        if not academic_id.isdigit():
            raise serializers.ValidationError({"academic_id": "ID must contain only digits."})

        if not (11 <= len(academic_id) <= 16):
            raise serializers.ValidationError({"academic_id": "ID length must be between 11 and 16 digits."})

        try:
            user = Account.objects.get(academic_id=attrs['academic_id'])
            attrs['user'] = user  # Attach the user object to attrs
        except Account.DoesNotExist:
            raise serializers.ValidationError({"academic_id": "ID is incorrect."})

        return attrs


class OTPSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        otp_code = attrs.get('otp')
        try:
            otp_instance = OTP.objects.get(otp=otp_code)
        except OTP.DoesNotExist:
            raise serializers.ValidationError({"otp": "OTP is incorrect."})

        if otp_instance.created_at < timezone.now() - timedelta(minutes=5):
            raise serializers.ValidationError({"otp": "OTP has expired."})

        # If OTP is valid, attach the user and otp_instance to attrs
        attrs['user'] = otp_instance.user
        attrs['otp_instance'] = otp_instance  # Attach otp_instance to attrs

        return attrs


class PasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True)
    token = serializers.CharField(write_only=True, required=True)
    user_id = serializers.IntegerField(write_only=True, required=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError({"password": "Password must be at least 8 characters long."})
        return value

    def validate(self, attrs):
        token = attrs.get('token')
        user_id = attrs.get('user_id')

        # Validate token and user_id
        try:
            reset_token = PasswordResetToken.objects.get(token=token)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError({"token": "Invalid or expired token."})

        if str(reset_token.user.id) != str(user_id):
            raise serializers.ValidationError({"user_id": "User ID does not match token."})

        attrs['user'] = reset_token.user
        return attrs

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
