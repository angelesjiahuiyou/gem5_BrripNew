#!/bin/bash

# Configuraci<C3><B3>n de rutas
GEM5_BIN="/scratch/rrodriguez/gem5-custom/build/X86/gem5.opt"
SCRIPT_PY="/scratch/rrodriguez/gem5-custom/configs/ucm"
OUT_DIR_BASE="./results/run"

# Lista de configuraciones (ejemplo: variando el tamaño de cache L1)
CONFIGS=("gem5_600.perl_mru" "gem5_607.cactuBSSN_mru" "gem5_631.deepsjeng_mru" "gem5_648.exchange2_mru" "gem5_602.gcc_mru" "gem5_619.lbm_mru" "gem5_638.imagick_mru" "gem5_649.fotonik3d_mru" "gem5_603.bwaves_mru" "gemm5_620.omnetpp_mru" "gem5_641.leela_mru" "gem5_654.roms_mru" "gem5_605.mcf_mru" "gem5_623.xalancbmk_mru" "gem5_644.nab_mru" "gem5_657.xz_mru")

echo "Iniciando instancias de gem5..."

for i in {0..11}
do
    CURRENT_OUT="${OUT_DIR_BASE}_${CONFIGS[$i]}"

    # Crear directorio de salida único para cada instancia
    mkdir -p $CURRENT_OUT

    # Ejecución de gem5
    # --outdir: define donde se guardan stats.txt y config.ini
    #syntax ./build/X86/gem5.opt --stats-file=600.perl.mru.txt simular_perl_mru.py
    $GEM5_BIN --outdir=$CURRENT_OUT $SCRIPT_PY/${CONFIGS[$i]}.py \
        --debug-flags=SyscallVerbose \
        --stats-file==${CONFIGS[$i]}.txt \
        > "$CURRENT_OUT/run_log.txt" 2>&1 &

    # Guardar el PID del proceso lanzado
    PIDS[$i]=$!
    echo "Instancia [$i] lanzada (PID: ${PIDS[$i]}), salida en: $CURRENT_OUT"
done

echo "Todas las instancias están en ejecución."
echo "PIDs: ${PIDS[@]}"

# Esperar a que todos los procesos terminen
wait
echo "Todas las simulaciones han finalizado correctamente."