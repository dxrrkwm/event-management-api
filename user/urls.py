from django.urls import path

from user.views import CreateTokenView, LogoutView, UserCreateView

urlpatterns = [
    path("register/", UserCreateView.as_view(), name="create"),
    path("login/", CreateTokenView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]

app_name = "user"
