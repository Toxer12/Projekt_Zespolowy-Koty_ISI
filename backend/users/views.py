from django.contrib.auth import get_user_model
from rest_framework import generics, authentication, permissions, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.urls import reverse

from users.serializers import UserSerializer, AuthTokenSerializer

from users.auth import CookieJWTAuthentication

class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        activation_link = f"http://localhost:8000/api/users/activate/{uid}/{token}/"
        try:
            send_mail(
                subject="Activate your account",
                message=f"Click to activate: {activation_link}",
                from_email="noreply@example.com",
                recipient_list=[user.email],
            )
        except Exception:
            pass

from django.shortcuts import redirect

class ActivateUserView(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = get_user_model().objects.get(pk=uid)
        except Exception:
            return redirect("http://localhost:5173/activation-error")
        if user.is_active:
            return redirect("http://localhost:5173/already-activated")
        if not default_token_generator.check_token(user, token):
            return redirect("http://localhost:5173/activation-error")
        user.is_active = True
        user.save()
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        response = redirect("http://localhost:5173/dashboard")

        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
            path='/',
            max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
        )

        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
            path='/',
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
        )

        return response

class LoginView(APIView):
    authentication_classes = (SessionAuthentication,)
    def post(self, request):
        serializer = AuthTokenSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        if not user.is_active:
            return Response({'error': 'Account not activated'}, status=403)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        response = Response({'message': 'Login successful'}, status=status.HTTP_200_OK)

        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
            path='/',
            max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
        )

        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
            path='/',
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
        )

        return response

class RefreshView(APIView):
    authentication_classes = (SessionAuthentication,)  # enforce CSRF

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response({'error': 'No refresh token'}, status=400)

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
        except TokenError:
            return Response({'error': 'Invalid token'}, status=401)

        response = Response({'message': 'Token refreshed'})

        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
            path='/',
            max_age=60 * 15,
        )

        return response

class LogoutView(APIView):
    authentication_classes = (SessionAuthentication,)
    def post(self, request):
        response = Response({'message': 'Logged out'})
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response

class MyView(APIView):
    authentication_classes = (CookieJWTAuthentication, SessionAuthentication)
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'email': request.user.email})