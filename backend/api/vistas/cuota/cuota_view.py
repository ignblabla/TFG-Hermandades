from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum, Q

from api.serializers import CuotaSerializer
from api.pagination import StandardResultsSetPagination
from api.models import Cuota

class MisCuotasListView(generics.ListAPIView):
    """
    Lista las cuotas exclusivas del hermano autenticado.
    Paginadas de 5 en 5 y ordenadas de más recientes a más antiguas.
    Incluye un resumen de los totales del hermano.
    """
    serializer_class = CuotaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Cuota.objects.filter(
            hermano=self.request.user
        ).order_by('-anio', '-fecha_emision')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        estados_deuda = [Cuota.EstadoCuota.PENDIENTE, Cuota.EstadoCuota.DEVUELTA]
        
        agregaciones = queryset.aggregate(
            total_cuotas=Count('id'),
            total_pagadas=Count('id', filter=Q(estado=Cuota.EstadoCuota.PAGADA)),
            total_pendientes=Count('id', filter=Q(estado__in=estados_deuda)),
            total_importe_pendiente=Sum('importe', filter=Q(estado__in=estados_deuda))
        )

        importe_pendiente = agregaciones['total_importe_pendiente'] or 0.00

        resumen = {
            "total_cuotas": agregaciones['total_cuotas'],
            "total_pagadas": agregaciones['total_pagadas'],
            "total_pendientes": agregaciones['total_pendientes'],
            "total_pendiente_euros": importe_pendiente,
        }

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)

            response.data['resumen'] = resumen
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "resumen": resumen,
            "results": serializer.data
        })