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


def obtener_nombre_perfil(user_id: Optional[str]) -> Optional[str]:
    if not user_id:
        return None
    resultado = supabase.table("perfiles").select("nombre").eq("id", user_id).execute()
    if resultado.data:
        return resultado.data[0]["nombre"]
    return None


def obtener_viaje_con_conductor(viaje_id: str) -> Optional[dict]:
    """El viaje completo (para el detalle que ve el rutero) + el nombre del conductor."""
    viaje = obtener_viaje(viaje_id)
    if not viaje:
        return None
    data = viaje.model_dump(mode="json")
    data["conductor_nombre"] = obtener_nombre_perfil(viaje.conductor_id)
    return data


def crear_solicitud(viaje_id: str, pasajero_id: str, distancia_pickup_km: float,
                     distancia_destino_km: float, precio_soles: float, km_recorridos: float) -> dict:
    fila = {
        "viaje_id": viaje_id,
        "pasajero_id": pasajero_id,
        "distancia_pickup_km": distancia_pickup_km,
        "distancia_destino_km": distancia_destino_km,
        "precio_soles": precio_soles,
        "km_recorridos": km_recorridos,
        "estado": "pendiente",
    }
    resultado = supabase.table("matches").insert(fila).execute()
    return resultado.data[0]


def listar_solicitudes_de_viaje(viaje_id: str) -> list:
    """Las personas que han pedido unirse a un viaje (para que el poolero las vea y acepte)."""
    resultado = supabase.table("matches").select("*").eq("viaje_id", viaje_id).execute()
    solicitudes = resultado.data
    for s in solicitudes:
        s["pasajero_nombre"] = obtener_nombre_perfil(s.get("pasajero_id"))
    return solicitudes


def aceptar_solicitud(solicitud_id: str) -> Optional[dict]:
    resultado = supabase.table("matches").select("*").eq("id", solicitud_id).execute()
    if not resultado.data:
        return None
    solicitud = resultado.data[0]

    supabase.table("matches").update({"estado": "confirmado"}).eq("id", solicitud_id).execute()

    viaje_resultado = supabase.table("viajes_poolero").select("cupos_disponibles").eq(
        "id", solicitud["viaje_id"]
    ).execute()
    if viaje_resultado.data:
        cupos_actuales = viaje_resultado.data[0]["cupos_disponibles"]
        nuevos_cupos = max(cupos_actuales - 1, 0)
        supabase.table("viajes_poolero").update({"cupos_disponibles": nuevos_cupos}).eq(
            "id", solicitud["viaje_id"]
        ).execute()

    return {"id": solicitud_id, "estado": "confirmado"}


def listar_viajes_de_conductor(conductor_id: str) -> list:
    """Los viajes que un poolero ha publicado, con el conteo de confirmados/pendientes de cada uno."""
    resultado = supabase.table("viajes_poolero").select("*").eq("conductor_id", conductor_id).execute()
    viajes = []
    for fila in resultado.data:
        matches_resultado = supabase.table("matches").select("estado").eq("viaje_id", fila["id"]).execute()
        confirmados = sum(1 for m in matches_resultado.data if m["estado"] == "confirmado")
        pendientes = sum(1 for m in matches_resultado.data if m["estado"] == "pendiente")
        fila["confirmados"] = confirmados
        fila["pendientes"] = pendientes
        viajes.append(fila)
    return viajes
