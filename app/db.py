"""
Conexión a Supabase.

IMPORTANTE: las credenciales NUNCA van escritas en el código.
Van en un archivo `.env` (que no se sube a git) con este formato:

    SUPABASE_URL=https://tuproyecto.supabase.co
    SUPABASE_KEY=tu_service_role_key_aqui

Usamos la `service_role` key (no la `anon`) porque el backend
necesita permisos completos para leer/escribir en todas las tablas.
Esa key es secreta — solo vive en el servidor, nunca en el frontend.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = "https://iarzynvjnkuolkfmqmnf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlhcnp5bnZqbmt1b2xrZm1xbW5mIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4OTk5NjA5MiwiZXhwIjoyMTA1NTcyMDkyfQ.xuxnHjaCHXprfZpaz68BGZI8bDjTkFrBe-9lcAbcnY8"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Faltan SUPABASE_URL y/o SUPABASE_KEY. "
        "Crea un archivo .env en la raíz del proyecto con esas variables "
        "(mira .env.example)."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)