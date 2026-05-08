import unittest
from unittest.mock import MagicMock, patch
import pytest
from rest_framework.test import APIRequestFactory, force_authenticate
from django.db.models import Q

from api.vistas.comunicado.listado_comunicados_view import MisComunicadosListView


class TestMisComunicadosListView(unittest.TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view_class = MisComunicadosListView
        self.path = "/api/comunicados/mis-noticias/"

        self.mock_user = MagicMock(spec=['is_authenticated', 'areas_interes'])
        self.mock_user.is_authenticated = True



    @patch('api.vistas.comunicado.listado_comunicados_view.Comunicado')
    def test_get_queryset_autenticado_con_filtro_correcto(self, mock_comunicado):
        """
        Test: Construcción correcta del QuerySet filtrado
        
        Given: Un usuario autenticado con áreas de interés.
        When: Se invoca get_queryset.
        Then: Se consultan las áreas del usuario, se aplica el filtro Q (interés o hermanos),
            se aplica distinct, se ordena por fecha descendente y retorna el resultado.
        """
        request = self.factory.get(self.path)
        request.user = self.mock_user

        vista = self.view_class()
        vista.request = request

        mock_areas_usuario = [MagicMock(), MagicMock()]
        self.mock_user.areas_interes.all.return_value = mock_areas_usuario

        mock_qs_final = MagicMock(name="QuerySetFinal")

        mock_comunicado.objects.filter.return_value.distinct.return_value.order_by.return_value = mock_qs_final

        resultado = vista.get_queryset()

        self.mock_user.areas_interes.all.assert_called_once()

        mock_comunicado.objects.filter.assert_called_once()
        args, _ = mock_comunicado.objects.filter.call_args
        self.assertIsInstance(args[0], Q)

        mock_comunicado.objects.filter.return_value.distinct.return_value.order_by.assert_called_once_with('-fecha_emision')

        self.assertEqual(resultado, mock_qs_final)