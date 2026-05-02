from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from api.servicios.papeleta_sitio.papeleta_telegram_service import TelegramWebhookService


class TelegramWebhookView(APIView):
    """
    Endpoint público para recibir notificaciones (Webhooks) directamente desde los servidores de Telegram.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        TelegramWebhookService.procesar_actualizacion(request.data)

        return Response({"status": "ok"}, status=status.HTTP_200_OK)