#!/bin/bash

# Directorio a procesar (por defecto el actual, o puedes pasar uno como argumento)
TARGET_DIR=${1:-.}

echo "Procesando archivos .py en: $TARGET_DIR"

# Buscar archivos .py y ejecutar la sustitución
# -i realiza el cambio en el archivo
# 's/MRU/LRU/g' busca MRU y lo cambia por LRU globalmente
find "$TARGET_DIR" -maxdepth 1 -name "*.py" -type f -exec sed -i 's/DDR3_1600_8x8/DDR4_2400_8x8/g' {} +
find "$TARGET_DIR" -maxdepth 1 -name "*.py" -type f -exec sed -i 's/8GB/16GB/g' {} +

echo "Proceso completado. Se han sustituido todas las ocurrencias de DDR3_1600_8x8 por DDR4_2400_8x8." 
