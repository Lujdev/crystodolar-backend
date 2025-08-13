#!/usr/bin/env python3
"""
Script de inicio para Railway
Maneja correctamente la variable de entorno PORT
"""

import os
import uvicorn
from simple_server_railway import app

if __name__ == "__main__":
    # Obtener puerto de Railway o usar 8000 por defecto
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Iniciando CrystoDolar Backend en puerto {port}")
    print(f"🌐 Host: 0.0.0.0")
    print(f"🔧 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    # Iniciar servidor
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
