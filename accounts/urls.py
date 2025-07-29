from django.urls import path
from .views import (
  SignInView,
  SignOutView,
  SignUpView,
  UserView,
)

urlpatterns = [
  path('signin', SignInView.as_view(), name='signin'),
  path('signup', SignUpView.as_view(), name='signup'),
  path('signout', SignOutView.as_view(), name='logout'),
  path('user', UserView.as_view(), name='user'),
]
