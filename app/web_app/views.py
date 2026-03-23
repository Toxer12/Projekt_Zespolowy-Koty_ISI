from django.shortcuts import render

# Create your views here.

from rest_framework import generics
from .serializers import RegisterSerializer
from .serializers import ChangePasswordSerializer
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.auth import login
from rest_framework import status
import uuid


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()

        token = Token.objects.create(user=user)

        activation_link = f"http://localhost:8000/api/activate/{token.key}/"

        send_mail(
            "Activate account",
            f'Hello {user.username}, here is your activation link: {activation_link}',
            "ISI_Koty@test.com",
            [user.email],
        )


class ActivateUser(APIView):
    def get(self, request, token):
        token = get_object_or_404(Token, key=token)
        user = token.user
        user.is_active = True
        user.save()
        return Response({"status": "activated"})


class LoginView(APIView):
    def post(self, request):
        user = authenticate(
            username=request.data["username"],
            password=request.data["password"],
        )

        if user is None:
            return Response({"error": "Invalid credentials"}, status=400)

        login(request, user)

        return Response({"status": "logged in"})


reset_tokens = {}

class PasswordResetRequest(APIView):
    def get(self, request):
        return Response({
            "detail": "Use POST with email"
        })

    def post(self, request):
        email = request.data.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"status": "sent"})

        token = str(uuid.uuid4())
        reset_tokens[token] = user.id

        link = f"http://localhost:8000/api/reset/{token}/"

        send_mail(
            "Here is your password reset lin:",
            link,
            "ISI_Koty@test.com",
            [email],
        )

        return Response({"status": "sent"})


class PasswordResetConfirm(APIView):
    def get(self, request, token):
        return Response({
            "detail": "Use POST with new password"
        })

    def post(self, request, token):
        user_id = reset_tokens.get(token)

        if not user_id:
            return Response({"error": "Invalid token"}, status=400)

        user = User.objects.get(id=user_id)

        user.password = make_password(request.data["password"])
        user.save()

        return Response({"status": "password changed"})

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        if not user.check_password(serializer.validated_data["old_password"]):
            return Response({"error": "Wrong password"}, status=400)

        user.password = make_password(serializer.validated_data["new_password"])
        user.save()

        return Response({"status": "password changed"})

class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.delete()
        return Response(
            {"status": "account deleted"},
            status=status.HTTP_204_NO_CONTENT
        )