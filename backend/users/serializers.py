from django.contrib.auth import get_user_model, authenticate, password_validation
from rest_framework import serializers
from django.utils.translation import gettext as _
from django.contrib.auth.hashers import check_password

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object"""
    class Meta:
        model = get_user_model()
        fields = ('email', 'password', 'username')  # <-- remove 'name', use 'username'
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 5},
            'email': {'write_only': True},
        }

    def create(self, validated_data):
        # Create user with email, username, password
        user = get_user_model().objects.create_user(**validated_data)
        user.is_active = False  # keep new users inactive until activation
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user

User = get_user_model()

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        user = self.context['request'].user

        if not check_password(data['old_password'], user.password):
            raise serializers.ValidationError({"old_password": "Old password is incorrect."})

        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New passwords do not match."})

        password_validation.validate_password(data['new_password'], user)

        return data

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance

class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user authentication object"""

    email = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs: dict) -> dict:
        """Validate and authenticate the user"""

        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )

        if not user:
            msg = _('Unable to authenticate with provided credentials')

            raise serializers.ValidationError(msg, code='authentication')

        attrs['user'] = user

        return attrs