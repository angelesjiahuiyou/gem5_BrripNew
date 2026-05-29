#!/bin/bash

# Directorio a procesar (por defecto el actual, o puedes pasar uno como argumento)
TARGET_DIR=${1:-.}

echo "Procesando archivos .py en: $TARGET_DIR"

# Buscar archivos .py y ejecutar la sustitución
# -i realiza el cambio en el archivo
# 's/MRU/LRU/g' busca MRU y lo cambia por LRU globalmente
find "$TARGET_DIR" -maxdepth 1 -name "*.py" -type f -exec sed -i 's/SHIP/SHiP/g' {} +

echo "Proceso completado. Se han sustituido todas las ocurrencias de MRU por LRU." 
