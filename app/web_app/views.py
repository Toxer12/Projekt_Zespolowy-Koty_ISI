from django.shortcuts import render

# Create your views here.

from rest_framework import generics
from .serializers import RegisterSerializer
from django.shortcuts import get_object_or_404
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()

        token = Token.objects.create(user=user)

        activation_link = f"http://localhost:8000/api/activate/{token.key}/"

        send_mail(
            "Activate account",
            f"Click: {activation_link}",
            "noreply@test.com",
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
    def get(self, request):
        return Response({
            "detail": "Use POST with username and password"
        })

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.is_active:
            return Response(
                {"error": "Account not active"},
                status=status.HTTP_403_FORBIDDEN
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key
        })


import uuid

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
            "Reset password",
            link,
            "noreply@test.com",
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