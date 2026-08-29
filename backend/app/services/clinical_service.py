from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from app.schemas.clinical_schema import DashboardMetricsResponse, AppointmentDetail

class ClinicalService:

    @staticmethod
    def fetch_historia_clinica(db: Session, dni: str) -> List[dict]:
        query = text("""
            SELECT fecha_registro, glucosa, categoria, detalle_reserva 
            FROM citas 
            WHERE patient_id = :dni 
            ORDER BY fecha_registro DESC
        """)
        result = db.execute(query, {"dni": dni}).fetchall()
        return [
            {
                "fecha_registro": row.fecha_registro,
                "glucosa": row.glucosa,
                "categoria": row.categoria,
                "detalle_reserva": row.detalle_reserva
            } for row in result
        ]

    @staticmethod
    def get_dashboard_metrics(
        db: Session,
        rol: str,
        username: str,
        patient_id: Optional[str] = None,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None
    ) -> DashboardMetricsResponse:
        
        # 1. Consulta para Estadísticas
        query_stats = "SELECT categoria, count(*) FROM citas WHERE 1=1"
        params: Dict[str, Any] = {}

        # Filtros por rol y paciente
        if rol.lower() == "paciente":
            query_stats += " AND patient_id = :pid"
            params["pid"] = username
        elif patient_id and patient_id.strip():
            query_stats += " AND patient_id = :pid"
            params["pid"] = patient_id.strip()

        # Filtros por rango de fechas
        if fecha_inicio and fecha_inicio.strip():
            query_stats += " AND fecha_cita >= :f_inicio"
            params["f_inicio"] = fecha_inicio.strip()
        if fecha_fin and fecha_fin.strip():
            query_stats += " AND fecha_cita <= :f_fin"
            params["f_fin"] = fecha_fin.strip()

        query_stats_exec = query_stats + " GROUP BY categoria"
        results_stats = db.execute(text(query_stats_exec), params).fetchall()
        
        stats = {r[0]: r[1] for r in results_stats} if results_stats else {}

        # 2. Consulta para Detalle
        query_detalle = """
            SELECT 
                patient_id AS DNI, 
                paciente AS NOMBRE_DEL_PACIENTE, 
                CAST(glucosa AS VARCHAR) || ' mg/dL' AS GLUCOSA, 
                categoria AS CATEGORIA, 
                COALESCE(detalle_reserva, '') AS DETALLE_DE_LA_RESERVA 
            FROM citas 
            WHERE 1=1
        """
        
        # Reutilizar filtros aplicados
        if rol.lower() == "paciente":
            query_detalle += " AND patient_id = :pid"
        elif patient_id and patient_id.strip():
            query_detalle += " AND patient_id = :pid"
            
        if fecha_inicio and fecha_inicio.strip():
            query_detalle += " AND fecha_cita >= :f_inicio"
        if fecha_fin and fecha_fin.strip():
            query_detalle += " AND fecha_cita <= :f_fin"

        query_detalle += " ORDER BY fecha_registro DESC"
        
        results_detalle = db.execute(text(query_detalle), params).fetchall()
        
        detalle_list = [
            AppointmentDetail(
                DNI=str(row[0]),
                NOMBRE_DEL_PACIENTE=str(row[1]),
                GLUCOSA=str(row[2]),
                CATEGORIA=str(row[3]),
                DETALLE_DE_LA_RESERVA=str(row[4])
            )
            for row in results_detalle
        ]

        return DashboardMetricsResponse(
            stats=stats,
            total=sum(stats.values()),
            emergencias=stats.get("EMERGENCIA", 0),
            citas=stats.get("AGENDAR CITA", 0),
            urgencias=stats.get("URGENCIAS", 0),
            detalle=detalle_list
        )