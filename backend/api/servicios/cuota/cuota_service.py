from django.db.models import QuerySet

from api.models import Cuota, Hermano


class CuotaService:
    @staticmethod
    def obtener_cuotas_pendientes_hermano(hermano: Hermano) -> QuerySet[Cuota]:
        """
        Retorna de manera eficiente las cuotas que representan una deuda 
        (Pendientes o Devueltas) para un hermano específico.
        """
        estados_deuda = [
            Cuota.EstadoCuota.PENDIENTE, 
            Cuota.EstadoCuota.DEVUELTA
        ]
        
        return Cuota.objects.filter(
            hermano=hermano,
            estado__in=estados_deuda
        ).order_by('anio', 'fecha_emision')



    @staticmethod
    def contar_cuotas_pendientes_hermano(hermano) -> int:
        """
        Retorna únicamente el número total de cuotas impagadas o devueltas
        del hermano, ejecutando un COUNT en la base de datos.
        """
        return CuotaService.obtener_cuotas_pendientes_hermano(hermano).count()