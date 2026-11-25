import os
from dotenv import load_dotenv

# Esto carga el archivo .env
load_dotenv()

id_val = os.getenv("SPOTIFY_CLIENT_ID")
secret_val = os.getenv("SPOTIFY_CLIENT_SECRET")

print(f"DEBUG: SPOTIFY_CLIENT_ID encontrado: {id_val}")
print(f"DEBUG: SPOTIFY_CLIENT_SECRET encontrado: {secret_val}")
