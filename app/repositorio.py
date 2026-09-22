"""
Funciones que hablan con Supabase (guardar y leer datos reales).
Separadas de main.py para que los endpoints queden limpios y
si el día de mañana cambias de base de datos, solo tocas este archivo.
"""

from typing import List, Optional
from datetime import datetime

from .db import supabase
from .models import Coordenada, ViajePoolero, BusquedaRutero


def _ruta_a_json(ruta: List[Coordenada]) -> list:
    return [{"lat": p.lat, "lng": p.lng} for p in ruta]


def _json_a_ruta(data: list) -> List[Coordenada]:
    return [Coordenada(lat=p["lat"], lng=p["lng"]) for p in data]


def guardar_viaje(viaje: ViajePoolero) -> ViajePoolero:
    fila = {
        "conductor_id": viaje.conductor_id,
        "hora_salida": viaje.hora_salida.isoformat(),
        "origen_lat": viaje.origen.lat,
        "origen_lng": viaje.origen.lng,
        "destino_lat": viaje.destino.lat,
        "destino_lng": viaje.destino.lng,
        "ruta": _ruta_a_json(viaje.ruta),
        "cupos_disponibles": viaje.cupos_disponibles,
        "preferencias": viaje.preferencias,
        "musica": viaje.musica,
        "gustos": viaje.gustos,
    }
    resultado = supabase.table("viajes_poolero").insert(fila).execute()
    fila_creada = resultado.data[0]
    viaje.id = fila_creada["id"]
    return viaje


def listar_viajes_activos() -> List[ViajePoolero]:
    resultado = (
        supabase.table("viajes_poolero")
        .select("*")
        .eq("estado", "activo")
        .execute()
    )
    viajes = []
    for fila in resultado.data:
        viajes.append(
            ViajePoolero(
                id=fila["id"],
                conductor_id=fila["conductor_id"],
                hora_salida=datetime.fromisoformat(fila["hora_salida"]),
                origen=Coordenada(lat=fila["origen_lat"], lng=fila["origen_lng"]),
                destino=Coordenada(lat=fila["destino_lat"], lng=fila["destino_lng"]),
                ruta=_json_a_ruta(fila["ruta"]),
                cupos_disponibles=fila["cupos_disponibles"],
                preferencias=fila.get("preferencias"),
                musica=fila.get("musica"),
                gustos=fila.get("gustos") or [],
            )
        )
    return viajes


def obtener_viaje(viaje_id: str) -> Optional[ViajePoolero]:
    resultado = (
        supabase.table("viajes_poolero").select("*").eq("id", viaje_id).execute()
    )
    if not resultado.data:
        return None
    fila = resultado.data[0]
    return ViajePoolero(
        id=fila["id"],
        conductor_id=fila["conductor_id"],
        hora_salida=datetime.fromisoformat(fila["hora_salida"]),
        origen=Coordenada(lat=fila["origen_lat"], lng=fila["origen_lng"]),
        destino=Coordenada(lat=fila["destino_lat"], lng=fila["destino_lng"]),
        ruta=_json_a_ruta(fila["ruta"]),
        cupos_disponibles=fila["cupos_disponibles"],
        preferencias=fila.get("preferencias"),
        musica=fila.get("musica"),
        gustos=fila.get("gustos") or [],
    )


def guardar_match(resultado_match) -> dict:
    fila = {
        "viaje_id": resultado_match.viaje_id,
        "distancia_pickup_km": resultado_match.distancia_pickup_km,
        "distancia_destino_km": resultado_match.distancia_destino_km,
        "precio_soles": resultado_match.precio_soles,
        "km_recorridos": resultado_match.km_recorridos,
    }
    resultado = supabase.table("matches").insert(fila).execute()
    return resultado.data[0]