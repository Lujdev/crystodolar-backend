#!/usr/bin/env python3
"""
Script simple para probar dependencias de producción
"""

import subprocess
import sys
import os

def test_simple():
    """Prueba simple de dependencias"""
    print("🧪 Probando dependencias de producción...")
    print()
    
    # Verificar que requirements.txt existe
    if not os.path.exists("requirements.txt"):
        print("❌ No se encontró requirements.txt")
        return False
    
    # Crear entorno virtual
    print("1️⃣ Creando entorno virtual...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "test_env"], check=True, capture_output=True)
        print("✅ Entorno virtual creado")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creando entorno virtual: {e}")
        return False
    
    # Instalar dependencias
    print("2️⃣ Instalando dependencias...")
    try:
        # Usar python -m pip para evitar problemas de permisos
        python_exe = os.path.join("test_env", "Scripts", "python.exe")
        
        # Actualizar pip
        result = subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ pip actualizado")
        else:
            print(f"⚠️ pip no se pudo actualizar: {result.stderr}")
        
        # Instalar dependencias
        result = subprocess.run([python_exe, "-m", "pip", "install", "-r", "requirements.txt"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencias instaladas correctamente")
            success = True
        else:
            print(f"❌ Error instalando dependencias:")
            print(result.stderr)
            success = False
            
    except Exception as e:
        print(f"❌ Error durante la instalación: {e}")
        success = False
    
    # Limpiar
    print("3️⃣ Limpiando...")
    try:
        import shutil
        shutil.rmtree("test_env", ignore_errors=True)
        print("✅ Entorno temporal eliminado")
    except:
        print("⚠️ No se pudo eliminar test_env (elimínalo manualmente)")
    
    print()
    if success:
        print("🎉 ¡Dependencias funcionando correctamente!")
        print("✅ Tu requirements.txt está listo para Railway")
    else:
        print("❌ Hay problemas con las dependencias")
        print("💡 Revisa el error anterior")
    
    return success

if __name__ == "__main__":
    test_simple()
