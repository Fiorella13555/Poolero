"""
API principal de Poolero/Rutero — ahora con persistencia real en Supabase.

Cómo correrlo localmente:
    1. Copia .env.example como .env y completa tus credenciales de Supabase
    2. pip install -r requirements.txt
    3. uvicorn app.main:app --reload

Luego abres http://localhost:8000/docs para probar cada endpoint.
"""

from fastapi import FastAPI, HTTPException
from typing import List

from .models import ViajePoolero, BusquedaRutero, ResultadoMatch
from .matching import buscar_matches, calcular_km_recorridos, calcular_precio
from . import repositorio

app = FastAPI(title="Poolero/Rutero API")


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
