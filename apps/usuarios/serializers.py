from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

Usuario = get_user_model()


class UsuarioCadastroSerializer(serializers.ModelSerializer):
    """Serializer para validação dos dados de entrada do cadastro de usuários."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Senha segura para acesso.'
    )

    class Meta:
        model = Usuario
        fields = ('username', 'email', 'password', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate_password(self, value):
        validate_password(value)
        return value


class UsuarioResponseSerializer(serializers.ModelSerializer):
    """Serializer para representação pública dos dados do usuário."""

    class Meta:
        model = Usuario
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'data_criacao',
            'data_atualizacao',
        )
        read_only_fields = fields


class LogoutSerializer(serializers.Serializer):
    """Serializer para validação do payload de logout."""

    refresh = serializers.CharField(
        required=True,
        help_text='Refresh token a ser invalidado.'
    )
