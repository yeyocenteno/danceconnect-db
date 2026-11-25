from app import app
from models import db, Usuario

def probar_conexion():
    with app.app_context():
        # 1. Intentamos crear un usuario de prueba
        test_user = Usuario(
            id="123456789",
            email="prueba@test.com",
            name="Usuario de Prueba",
            username="tester_uno"
        )
        
        try:
            db.session.add(test_user)
            db.session.commit()
            print("✅ ¡Éxito! Usuario insertado en MySQL (Maestro).")
            
            # 2. Verificamos que se pueda leer
            user = Usuario.query.get("123456789")
            if user:
                print(f"✅ ¡Lectura confirmada! Usuario encontrado: {user.email}")
            
            # 3. Limpiamos la prueba
            db.session.delete(user)
            db.session.commit()
            print("✅ Limpieza completada.")
            
        except Exception as e:
            print(f"❌ Error durante la prueba: {e}")
            db.session.rollback()

if __name__ == "__main__":
    probar_conexion()
