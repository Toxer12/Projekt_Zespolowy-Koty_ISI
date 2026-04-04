from django.urls import path

from users.views import LoginView, RefreshView, LogoutView, RegisterView, ActivateUserView, MyView, ChangePasswordView

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('refresh/', RefreshView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('register/', RegisterView.as_view()),
    path(
        'activate/<uidb64>/<token>/',
        ActivateUserView.as_view(),
        name='user-activate'
    ),
    path('my/', MyView.as_view()),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]