from django.contrib.auth import get_user_model, authenticate, password_validation
from rest_framework import serializers
from django.utils.translation import gettext as _
from django.contrib.auth.hashers import check_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password', 'name')  # was 'username'
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'write_only': True},
        }
    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        user.is_active = False
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        user = self.context['request'].user

        if not check_password(data['old_password'], user.password):
            raise serializers.ValidationError({"old_password": "Stare hasło jest nieprawidłowe."})

        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Nowe hasła nie są takie same."})

        password_validation.validate_password(data['new_password'], user)

        return data

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = User.objects.filter(email=email).first()
        if user and user.check_password(password):
            attrs['user'] = user
            return attrs

        raise serializers.ValidationError("Invalid credentials")
        if not user:
            raise serializers.ValidationError(
                _('Unable to authenticate with provided credentials'),
                code='authentication'
            )

        attrs['user'] = user
        return attrs
    

from rest_framework import serializers

class ChangeNameSerializer(serializers.Serializer):
    new_name = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        user = self.context['request'].user

        if not user.check_password(data['password']):
            raise serializers.ValidationError({
                "password": "Nieprawidłowe hasło."
            })

        return data

    def update(self, instance, validated_data):
        instance.username = validated_data['new_name']
        instance.save()
        return instance
    
class ChangeEmailSerializer(serializers.Serializer):
    new_email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        user = self.context['request'].user

        # check password
        if not user.check_password(data['password']):
            raise serializers.ValidationError({
                "password": "Nieprawidłowe hasło."
            })

        # check uniqueness
        if User.objects.filter(email=data['new_email']).exists():
            raise serializers.ValidationError({
                "new_email": "Ten email jest już zajęty."
            })

        return data

    def update(self, instance, validated_data):
        instance.email = validated_data['new_email']
        instance.save()
        return instance
