#import pdb
#pdb.set_trace()
# -*- coding: utf-8 -*-

import m5
from m5.objects import *

# --- Configuracion del Sistema ---
system = System()

# Configuracion del reloj y voltaje
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = '3GHz'
system.clk_domain.voltage_domain = VoltageDomain()

# Configuracion de la memoria principal
system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('2GB')]
system.membus = SystemXBar()

# --- Configuracion de la CPU (X86 Out-of-Order) ---
system.cpu = X86O3CPU()

# --- Jerarquia de Caches ---

# L1 Instrucciones (16KB, LRU)
system.cpu.icache = Cache(size='16kB',
                         assoc=4,
                         tag_latency=2,
                         data_latency=2,
                         response_latency=2,
                         mshrs=4,
                         tgts_per_mshr=20,
                         replacement_policy=LRURP())

# L1 Datos (64KB, LRU)
system.cpu.dcache = Cache(size='64kB',
                         assoc=4,
                         tag_latency=2,
                         data_latency=2,
                         response_latency=2,
                         mshrs=4,
                         tgts_per_mshr=20,
                         replacement_policy=LRURP())

# L2 Cache (1MB, LRU)
system.l2cache = Cache(size='1MB',
                      assoc=8,
                      tag_latency=20,
                      data_latency=20,
                      response_latency=20,
                      mshrs=20,
                      tgts_per_mshr=12,
                      replacement_policy=LRURP())

# Conexiones de la jerarquia
system.cpu.icache.cpu_side = system.cpu.icache_port
system.cpu.dcache.cpu_side = system.cpu.dcache_port

system.l2bus = L2XBar()
system.cpu.icache.mem_side = system.l2bus.cpu_side_ports
system.cpu.dcache.mem_side = system.l2bus.cpu_side_ports

system.l2cache.cpu_side = system.l2bus.mem_side_ports
system.l2cache.mem_side = system.membus.cpu_side_ports

# Conexiones de interrupciones y memoria
system.cpu.createInterruptController()
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# --- Configuracion del Benchmark SPEC 2017: 623.xalancbmk_s ---
# Ruta base proporcionada
base_path = '/home/jiahui/repos/cpu2017/cpu2017/benchspec/CPU/623.xalancbmk_s/exe/'

process = Process()
# Buscamos el ejecutable dentro de la carpeta (el nombre exacto depende de tu compilación)
process.executable = base_path + 'xalancbmk_s_base.x86-64'

# Argumentos para el dataset 'train' de xalancbmk:
# El benchmark requiere: -v entrada.xml hoja_estilo.xsl
process.cmd = [process.executable, '-v', 'allbooks.xml', 'xalanc.xsl']

# Directorio de trabajo para que encuentre los archivos .xml y .xsl
process.cwd = base_path

system.cpu.workload = process
system.cpu.createThreads()

# --- Ejecucion ---
root = Root(full_system = False, system = system)
m5.instantiate()

print("Iniciando simulacion de 623.xalancbmk_s (L2 con política MRU)...")
exit_event = m5.simulate()

print(f"Simulacion terminada en el tick {m5.curTick()} debido a {exit_event.getCause()}")

