"""
Modelos de datos de la app (Poolero/Rutero).
Por ahora usamos Pydantic para validar la forma de los datos.
Cuando conectes una base de datos real (Supabase/Postgres), estos
mismos modelos te sirven de base para las tablas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Coordenada(BaseModel):
    lat: float
    lng: float


class Usuario(BaseModel):
    id: str
    nombre: str
    rol_default: Optional[str] = None  # "poolero" o "rutero"
    calificacion_promedio: float = 5.0
    gustos: List[str] = []
    musica_preferida: Optional[str] = None


class ViajePoolero(BaseModel):
    """Un viaje que publica un conductor (poolero)."""
    id: Optional[str] = None
    conductor_id: str
    hora_salida: datetime
    origen: Coordenada
    destino: Coordenada
    # La ruta completa como lista de puntos (la sacas de una API de rutas
    # tipo OSRM o Google Directions cuando conectes el mapa real).
    ruta: List[Coordenada]
    cupos_disponibles: int
    preferencias: Optional[str] = None
    musica: Optional[str] = None
    gustos: List[str] = []


class BusquedaRutero(BaseModel):
    """Lo que pide un pasajero (rutero) al buscar viaje."""
    pasajero_id: str
    origen: Coordenada
    destino: Coordenada
    horario_deseado: datetime
    # Cuánta tolerancia de horario acepta, en minutos
    tolerancia_minutos: int = 20


class ResultadoMatch(BaseModel):
    viaje_id: str
    conductor_id: str
    distancia_pickup_km: float
    distancia_destino_km: float
    precio_soles: float
    km_recorridos: float


class SolicitudCreate(BaseModel):
    """Lo que manda el rutero al querer unirse a un viaje ya encontrado en /buscar."""
    pasajero_id: str
    distancia_pickup_km: float
    distancia_destino_km: float
    precio_soles: float
    km_recorridos: float
