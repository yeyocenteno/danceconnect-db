import json
import os
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
import uuid # Importar UUID

# Clave de cifrado (16, 24 o 32 bytes)
KEY = b'TuClaveSecreta16'  # Cambia esto a algo más seguro

def pad(data):
    """Rellena para que sea múltiplo de 16 bytes"""
    return data + ' ' * (16 - len(data) % 16)

def cifrar(texto):
    texto = pad(texto)
    cipher = AES.new(KEY, AES.MODE_ECB)
    encrypted = cipher.encrypt(texto.encode('utf-8'))
    return base64.b64encode(encrypted).decode('utf-8')

def descifrar(texto_cifrado):
    encrypted = base64.b64decode(texto_cifrado)
    cipher = AES.new(KEY, AES.MODE_ECB)
    decrypted = cipher.decrypt(encrypted).decode('utf-8')
    return decrypted.strip()
    
#////////////////////
# En utils.py, modifica leer_json:

def leer_json(ruta_completa):
    if not os.path.exists(ruta_completa):
        return []
    
    try:
        with open(ruta_completa, 'r') as f:
            content = f.read()
            if not content:
                return []
            
            # --- CORRECCIÓN AQUÍ ---
            try:
                # Intenta descifrar primero
                decrypted_content = descifrar(content)
                return json.loads(decrypted_content)
            except:
                # Si falla (porque el archivo estaba en texto plano o corrupto), intenta cargar directo
                return json.loads(content)
            # -----------------------
            
    except Exception as e:
        print(f"Error leyendo {ruta_completa}: {e}")
        return []


def guardar_json(path, data):
    texto = json.dumps(data)
    data_cifrada = cifrar(texto)
    with open(path, 'w') as f:
        f.write(data_cifrada)

# Función para generar el ID que usaremos en 'clases'
def generar_uuid():
    """Genera un ID único global (UUID v4) para las nuevas clases."""
    return str(uuid.uuid4())
