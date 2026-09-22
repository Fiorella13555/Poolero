"""
Lógica de matching entre pooleros (conductores) y ruteros (pasajeros).

Regla de negocio (definida por Fiorella):
- El punto de RECOJO del pasajero debe caer DENTRO de la ruta del conductor
  o a un máximo de ~0.5 km de ella (radio configurable).
- El DESTINO del pasajero puede tener más margen: no hace falta que
  coincida con el destino del conductor, solo estar "razonablemente cerca".
- Precio = 1 sol por km recorrido + 20% de margen para la plataforma.
"""

from math import radians, sin, cos, sqrt, atan2
from typing import List
from .models import Coordenada, ViajePoolero, BusquedaRutero, ResultadoMatch

RADIO_TIERRA_KM = 6371.0

# --- Parámetros de negocio (fácil de ajustar) ---
RADIO_PICKUP_KM = 0.5       # tolerancia para el punto de recojo
RADIO_DESTINO_KM = 3.0      # tolerancia para el destino (más flexible)
PRECIO_POR_KM = 1.0         # 1 sol por km
MARGEN_PLATAFORMA = 0.20    # 20% de ganancia


def haversine_km(a: Coordenada, b: Coordenada) -> float:
    """Distancia en línea recta entre dos coordenadas, en km."""
    lat1, lon1, lat2, lon2 = map(radians, [a.lat, a.lng, b.lat, b.lng])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * RADIO_TIERRA_KM * atan2(sqrt(h), sqrt(1 - h))


def distancia_punto_a_ruta(punto: Coordenada, ruta: List[Coordenada]) -> float:
    """
    Distancia mínima entre un punto y una ruta (lista de coordenadas).
    Simplificado: mide contra cada punto de la ruta y se queda con el
    más cercano. Para una ruta con buena densidad de puntos (la que te
    da Google Directions / OSRM) esto es suficientemente preciso.
    Si luego quieres precisión de "punto a segmento de línea", se puede
    mejorar con shapely (ya está instalado).
    """
    if not ruta:
        raise ValueError("La ruta no puede estar vacía")
    return min(haversine_km(punto, p) for p in ruta)


def calcular_km_recorridos(ruta: List[Coordenada]) -> float:
    """Suma la distancia entre puntos consecutivos de la ruta."""
    total = 0.0
    for i in range(len(ruta) - 1):
        total += haversine_km(ruta[i], ruta[i + 1])
    return round(total, 2)


def calcular_precio(km_recorridos: float) -> float:
    base = km_recorridos * PRECIO_POR_KM
    return round(base * (1 + MARGEN_PLATAFORMA), 2)


def buscar_matches(
    busqueda: BusquedaRutero, viajes_disponibles: List[ViajePoolero]
) -> List[ResultadoMatch]:
    """
    Filtra los viajes de pooleros que hacen match con la búsqueda
    de un rutero, según las reglas de distancia y horario.
    """
    resultados = []

    for viaje in viajes_disponibles:
        if viaje.cupos_disponibles <= 0:
            continue

        # 1. Filtro de horario
        diferencia_min = abs(
            (viaje.hora_salida - busqueda.horario_deseado).total_seconds() / 60
        )
        if diferencia_min > busqueda.tolerancia_minutos:
            continue

        # 2. Filtro de pickup (estricto: dentro de la ruta o 0.5km)
        dist_pickup = distancia_punto_a_ruta(busqueda.origen, viaje.ruta)
        if dist_pickup > RADIO_PICKUP_KM:
            continue

        # 3. Filtro de destino (más flexible)
        dist_destino = distancia_punto_a_ruta(busqueda.destino, viaje.ruta)
        if dist_destino > RADIO_DESTINO_KM:
            continue

        km_recorridos = calcular_km_recorridos(viaje.ruta)
        precio = calcular_precio(km_recorridos)

        resultados.append(
            ResultadoMatch(
                viaje_id=viaje.id or "sin_id",
                conductor_id=viaje.conductor_id,
                distancia_pickup_km=round(dist_pickup, 2),
                distancia_destino_km=round(dist_destino, 2),
                precio_soles=precio,
                km_recorridos=km_recorridos,
            )
        )

    # Ordenamos los mejores matches primero (más cerca del pickup)
    resultados.sort(key=lambda r: r.distancia_pickup_km)
    return resultados