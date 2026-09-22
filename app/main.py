"""
API principal de Poolero/Rutero — ahora con persistencia real en Supabase.

Cómo correrlo localmente:
    1. Copia .env.example como .env y completa tus credenciales de Supabase
    2. pip install -r requirements.txt
    3. uvicorn app.main:app --reload

Luego abres http://localhost:8000/docs para probar cada endpoint.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from .models import ViajePoolero, BusquedaRutero, ResultadoMatch, SolicitudCreate
from .matching import buscar_matches, calcular_km_recorridos, calcular_precio
from . import repositorio

app = FastAPI(title="Poolero/Rutero API")

# Permite que el frontend (que vive en otro dominio) le hable a esta API.
# En producción real conviene restringir allow_origins a tu dominio exacto,
# pero mientras pruebas, "*" (cualquier origen) es lo más simple.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/viajes", response_model=ViajePoolero)
def publicar_viaje(viaje: ViajePoolero):
    """El poolero (conductor) publica un viaje nuevo. Se guarda en Supabase."""
    return repositorio.guardar_viaje(viaje)


@app.get("/viajes", response_model=List[ViajePoolero])
def listar_viajes():
    """Lista los viajes activos guardados en Supabase."""
    return repositorio.listar_viajes_activos()


@app.post("/buscar", response_model=List[ResultadoMatch])
def buscar_viaje(busqueda: BusquedaRutero):
    """El rutero (pasajero) busca viajes que le hagan match, contra los viajes reales en Supabase."""
    disponibles = repositorio.listar_viajes_activos()
    resultados = buscar_matches(busqueda, disponibles)
    # Guardamos cada match encontrado, para tener historial
    for r in resultados:
        repositorio.guardar_match(r)
    return resultados


@app.get("/viajes/{viaje_id}/precio")
def precio_estimado(viaje_id: str):
    """Calcula el precio estimado de un viaje ya publicado en Supabase."""
    viaje = repositorio.obtener_viaje(viaje_id)
    if not viaje:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    km = calcular_km_recorridos(viaje.ruta)
    return {"viaje_id": viaje_id, "km_recorridos": km, "precio_soles": calcular_precio(km)}


@app.get("/")
def home():
    return {"mensaje": "API de Poolero/Rutero funcionando 🚗 (con Supabase conectado)"}


@app.get("/viajes/mios")
def mis_viajes(conductor_id: str):
    """Los viajes que ha publicado un poolero, con cuántos aceptaron/piden unirse."""
    return repositorio.listar_viajes_de_conductor(conductor_id)


@app.get("/viajes/{viaje_id}/detalle")
def detalle_de_viaje(viaje_id: str):
    """El detalle completo de un viaje (para que el rutero lo vea al hacer click), con el nombre del conductor."""
    data = repositorio.obtener_viaje_con_conductor(viaje_id)
    if not data:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    return data


@app.post("/viajes/{viaje_id}/solicitar")
def solicitar_viaje(viaje_id: str, solicitud: SolicitudCreate):
    """El rutero pide unirse a un viaje que le hizo match."""
    return repositorio.crear_solicitud(
        viaje_id,
        solicitud.pasajero_id,
        solicitud.distancia_pickup_km,
        solicitud.distancia_destino_km,
        solicitud.precio_soles,
        solicitud.km_recorridos,
    )


@app.get("/viajes/{viaje_id}/solicitudes")
def solicitudes_de_viaje(viaje_id: str):
    """Quiénes han pedido unirse a este viaje (para que el poolero decida)."""
    return repositorio.listar_solicitudes_de_viaje(viaje_id)


@app.post("/solicitudes/{solicitud_id}/aceptar")
def aceptar_solicitud(solicitud_id: str):
    """El poolero acepta a un pasajero: confirma la solicitud y descuenta un cupo."""
    resultado = repositorio.aceptar_solicitud(solicitud_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return resultado
