import mysql.connector
import csv
from datetime import datetime

# 1. Configuración de la conexión a la base de datos
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="DanceConnect2026!",
        database="danceconnect_db"
    )
    cursor = db.cursor()
    print("-> Conexión a MySQL establecida correctamente.\n")
except mysql.connector.Error as e:
    print(f"Error crítico al conectar a MySQL: {e}")
    exit(1)

# 2. Cargar la tabla de Usuarios
print("Step 1: Cargando registros en la tabla 'usuarios'...")
usuarios_cargados = 0
usuarios_errores = 0

# Usamos 'utf-8-sig' por si el archivo viene de Excel con BOM
with open('usuarios.csv', 'r', encoding='utf-8-sig', errors='replace') as f:
    reader = csv.DictReader(f)
    for row in reader:
        sql = """INSERT INTO usuarios (id, email, name, username, picture, role, bio) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        try:
            cursor.execute(sql, (
                row['id'].strip(), 
                row['email'].strip(), 
                row['name'].strip(), 
                row['username'].strip(), 
                row['picture'].strip(), 
                row['role'].strip(), 
                row['bio'].strip()
            ))
            usuarios_cargados += 1
        except mysql.connector.Error as err:
            # Si el usuario ya existe o hay duplicados, te avisa pero no rompe el flujo
            print(f"   [Aviso] No se pudo cargar usuario {row.get('username')}: {err.msg}")
            usuarios_errores += 1

print(f"-> Fin usuarios. Éxito: {usuarios_cargados} | Saltados/Errores: {usuarios_errores}\n")


# 3. Cargar la tabla de Clases
print("Step 2: Cargando registros en la tabla 'clases'...")
clases_cargadas = 0
clases_errores = 0

with open('clases.csv', 'r', encoding='utf-8-sig', errors='replace') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Asegurar que la duración sea un entero puro
        try:
            duracion_final = int(float(row['duration'].strip()))
        except (ValueError, TypeError):
            duracion_final = 0
        
        # Formatear la fecha dinámicamente para MySQL
        fecha_str = row['publishDate'].strip()
        fecha_mysql = None
        
        # Intentar procesar formatos de fecha comunes (con o sin segundos)
        for formato in ('%m/%d/%Y %H:%M', '%m/%d/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S'):
            try:
                fecha_obj = datetime.strptime(fecha_str, formato)
                fecha_mysql = fecha_obj.strftime('%Y-%m-%d %H:%M:%S')
                break
            except ValueError:
                continue
        
        # Si el formato es irreconocible, asignamos la hora actual del sistema
        if not fecha_mysql:
            fecha_mysql = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        sql = """INSERT INTO clases 
                 (id, publisherId, name, description, style, difficulty, thumbnailUrl, videoUrl, duration, publishDate) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        try:
            cursor.execute(sql, (
                row['id'].strip(), 
                row['publisherId'].strip(), 
                row['name'].strip(), 
                row['description'].strip(), 
                row['style'].strip(), 
                row['difficulty'].strip(), 
                row['thumbnailUrl'].strip(), 
                row['videoUrl'].strip(), 
                duracion_final, 
                fecha_mysql
            ))
            clases_cargadas += 1
        except mysql.connector.Error as err:
            print(f"   [Aviso] No se pudo cargar clase ID {row.get('id')}: {err.msg}")
            clases_errores += 1

print(f"-> Fin clases. Éxito: {clases_cargadas} | Saltadas/Errores: {clases_errores}\n")

# 4. Confirmar y guardar todos los cambios en la Base de Datos
db.commit()
print("=== ¡PROCESO DE CARGA MASIVA TERMINADO ===")
print(f"Total registros guardados con éxito -> Usuarios: {usuarios_cargados}, Clases: {clases_cargadas}")

cursor.close()
db.close()
