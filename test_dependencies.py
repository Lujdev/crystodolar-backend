#!/usr/bin/env python3
"""
Script para probar la instalación de dependencias de producción
"""

import subprocess
import sys
import os

def test_dependencies():
    """Prueba la instalación de dependencias de producción"""
    print("🧪 Probando instalación de dependencias de producción...")
    print()
    
    # Crear entorno virtual temporal
    print("1️⃣ Creando entorno virtual temporal...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "temp_env"], check=True)
        print("✅ Entorno virtual creado")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creando entorno virtual: {e}")
        return False
    
    # Activar entorno virtual y instalar dependencias
    if os.name == 'nt':  # Windows
        activate_script = "temp_env\\Scripts\\activate"
        pip_path = "temp_env\\Scripts\\pip"
    else:  # Unix/Linux
        activate_script = "temp_env/bin/activate"
        pip_path = "temp_env/bin/pip"
    
    print("2️⃣ Instalando dependencias...")
    try:
        # Actualizar pip usando python -m pip (más seguro)
        subprocess.run([f"{temp_env}\\Scripts\\python.exe", "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)
        print("✅ pip actualizado")
        
        # Instalar dependencias de producción
        subprocess.run([f"{temp_env}\\Scripts\\python.exe", "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencias instaladas correctamente")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False
    
    # Limpiar
    print("3️⃣ Limpiando entorno temporal...")
    try:
        if os.name == 'nt':  # Windows
            import shutil
            shutil.rmtree("temp_env", ignore_errors=True)
        else:  # Unix/Linux
            subprocess.run(["rm", "-rf", "temp_env"], check=True)
        print("✅ Entorno temporal eliminado")
    except Exception as e:
        print(f"⚠️ No se pudo eliminar el entorno temporal: {e}")
        print("💡 Puedes eliminarlo manualmente con: rmdir /s /q temp_env")
    
    print()
    print("🎉 ¡Todas las dependencias se instalaron correctamente!")
    print("✅ Tu requirements.txt está listo para Railway")
    return True

if __name__ == "__main__":
    success = test_dependencies()
    sys.exit(0 if success else 1)
