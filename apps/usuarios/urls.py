from django.urls import path
from usuarios.views import (
    CadastroView,
    LoginView,
    LogoutView,
    RefreshTokenView,
    UsuarioMeView,
)

urlpatterns = [
    path('cadastro/', CadastroView.as_view(), name='usuario-cadastro'),
    path('login/', LoginView.as_view(), name='usuario-login'),
    path('refresh/', RefreshTokenView.as_view(), name='usuario-refresh'),
    path('logout/', LogoutView.as_view(), name='usuario-logout'),
    path('me/', UsuarioMeView.as_view(), name='usuario-me'),
]
