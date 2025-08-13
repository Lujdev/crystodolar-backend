#!/usr/bin/env python3
"""
Script para generar una SECRET_KEY segura para producción
"""

import secrets
import string

def generate_secret_key(length=64):
    """Genera una clave secreta segura"""
    # Caracteres seguros para la clave
    characters = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    
    # Generar clave aleatoria
    secret_key = ''.join(secrets.choice(characters) for _ in range(length))
    
    return secret_key

if __name__ == "__main__":
    print("🔐 Generando SECRET_KEY segura para producción...")
    print()
    
    # Generar clave de 64 caracteres
    secret_key = generate_secret_key(64)
    
    print("✅ SECRET_KEY generada:")
    print(f"SECRET_KEY={secret_key}")
    print()
    
    print("📋 Copia esta línea y agrégalas a las variables de entorno en Railway:")
    print(f"SECRET_KEY={secret_key}")
    print()
    
    print("⚠️  IMPORTANTE:")
    print("- Guarda esta clave en un lugar seguro")
    print("- Nunca la compartas o subas a Git")
    print("- Usa una clave diferente para cada entorno")
