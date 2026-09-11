from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class DocumentacaoAPITestCase(APITestCase):
    """
    Testes de integração para os endpoints de documentação OpenAPI (drf-spectacular).
    """

    def test_schema_endpoint_retorna_200(self):
        """Deve retornar o schema OpenAPI em formato YAML/JSON com status 200 sem necessidade de autenticação."""
        url = reverse('schema')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verifica se o conteúdo do schema inclui o título da API
        self.assertIn('Fluxo Tarefas API', response.content.decode('utf-8'))

    def test_swagger_ui_retorna_200(self):
        """Deve retornar a página HTML do Swagger UI com status 200."""
        url = reverse('swagger-ui')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('swagger-ui', response.content.decode('utf-8').lower())

    def test_redoc_retorna_200(self):
        """Deve retornar a página HTML do ReDoc com status 200."""
        url = reverse('redoc')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('redoc', response.content.decode('utf-8').lower())
