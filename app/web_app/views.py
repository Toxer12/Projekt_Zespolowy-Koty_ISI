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
from rest_framework_simplejwt.authentication import JWTAuthentication # type: ignore
from rest_framework_simplejwt.tokens import RefreshToken # type: ignore
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken # type: ignore
from web_app.auth import CookieJWTAuthentication
import uuid


activation_tokens = {}

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        user.is_active = False
        user.save()

        token = str(uuid.uuid4())
        activation_tokens[token] = user.id

        activation_link = f"http://localhost:5173/activate/{token}/"

        send_mail(
            "Activate account",
            f"Hello {user.username}, here is your activation link: {activation_link}",
            "ISI_Koty@test.com",
            [user.email],
        )


class ActivateUser(APIView):
    def get(self, request, token):
        user_id = activation_tokens.get(token)
        if not user_id:
            return Response({"error": "Invalid token"}, status=400)

        user = User.objects.get(id=user_id)
        user.is_active = True
        user.save()
        del activation_tokens[token]

        return Response({"status": "activated"})

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

        link = f"http://localhost:5173/reset-password-confirm/{token}/"

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
    authentication_classes = [CookieJWTAuthentication]
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
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.delete()
        return Response(
            {"status": "account deleted"},
            status=status.HTTP_204_NO_CONTENT
        )

class LoginView(APIView):
    def post(self, request):
        user = authenticate(
            username=request.data.get("username"),
            password=request.data.get("password")
        )
        if not user:
            return Response({"detail": "Nieprawidłowe dane"}, status=401)

        refresh = RefreshToken.for_user(user)
        response = Response({"status": "ok"})
        response.set_cookie(
            key="access_token",
            value=str(refresh.access_token),
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=3600,
        )
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=7 * 24 * 3600,
        )
        return response

class LogoutView(APIView):
    def post(self, request):
        response = Response({"status": "ok"})
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response

class CookieTokenRefreshView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response({"error": "Brak refresh tokenu"}, status=401)

        try:
            refresh = RefreshToken(refresh_token)
            response = Response({"status": "ok"})
            response.set_cookie(
                key="access_token",
                value=str(refresh.access_token),
                httponly=True,
                secure=False,
                samesite="Lax",
                max_age=3600,
            )
            return response
        except (TokenError, InvalidToken):
            return Response({"error": "Nieprawidłowy refresh token"}, status=401)

class MeView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"username": request.user.username})