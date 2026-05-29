import m5
from m5.objects import *

# --- 1. Configuracion del Sistema Base ---
system = System()
system.clk_domain = SrcClockDomain(clock='3.2GHz', voltage_domain=VoltageDomain())
system.mem_mode = 'timing'  # Iniciamos en atomic para el Fast-Forward
system.mem_ranges = [AddrRange('16GB')]
system.membus = SystemXBar()

# --- 2. Definicion de CPUs (Directamente como una lista para evitar conflictos) ---
# Indice 0: Fast-Forward (TimingSimple es mas rapido que O3 y evita el error)
# Indice 1: Detallada (X86O3CPU)
system.cpu = [TimingSimpleCPU(cpu_id=0), X86O3CPU(cpu_id=0)]

# --- 3. Jerarquia de Memoria y Caches ---

# Clase base para L1 (16KB iCache, 64KB dCache - LRU)
class L1ICache(Cache):
    size = '16kB'
    assoc = 4
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20
    replacement_policy = LRURP()

class L1DCache(Cache):
    size = '32kB'
    assoc = 8
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20
    replacement_policy = LRURP()

# Clase para L2 (1MB - BRRIP)
class L2Cache(Cache):
    size = '1MB'
    assoc = 32
    tag_latency = 20
    data_latency = 20
    response_latency = 20
    mshrs = 20
    tgts_per_mshr = 12
    replacement_policy = BRRIPRP()

# Bus compartido para conectar L1s a L2
system.l2bus = L2XBar()

def setup_cpu_caches(cpu):
    # Crear caches L1
    cpu.icache = L1ICache()
    cpu.dcache = L1DCache()
    
    # Conectar puertos de cache a la CPU
    cpu.icache.cpu_side = cpu.icache_port
    cpu.dcache.cpu_side = cpu.dcache_port
    
    # Conectar caches al bus L2
    cpu.icache.mem_side = system.l2bus.cpu_side_ports
    cpu.dcache.mem_side = system.l2bus.cpu_side_ports
    
    # Crear controlador de interrupciones
    cpu.createInterruptController()
    
    # CONEXION CRITICA: Puertos de interrupcion al membus (Resuelve el Panic)
    cpu.interrupts[0].pio = system.membus.mem_side_ports
    cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
    cpu.interrupts[0].int_responder = system.membus.mem_side_ports

# Configuramos ambas CPUs
for cpu in system.cpu:
    setup_cpu_caches(cpu)

system.l2cache = L2Cache()
system.l2cache.cpu_side = system.l2bus.mem_side_ports
system.l2cache.mem_side = system.membus.cpu_side_ports

system.system_port = system.membus.cpu_side_ports
system.mem_ctrl = MemCtrl(dram=DDR4_2400_8x8(range=system.mem_ranges[0]))
system.mem_ctrl.port = system.membus.mem_side_ports

# --- Configuracion del Benchmark 654.roms_s ---
# Ruta definida por el usuario
base_path = "/scratch/rrodriguez/SPEC2017/654.roms_s"
executable = f"{base_path}/sroms_base.x86-64"
process = Process()
# Buscamos el ejecutable (tipicamente roms_s_base.x86 o similar)
process.executable = executable

# Comando para dataset 'train' de 654.roms_s
# Nota: ROMS lee su configuracion de un archivo .in redirigido a la entrada estandar (stdin)
process.cmd = [process.executable]
process.cwd = base_path # Directorio de trabajo para que encuentre yee.dat

process.input = f"{base_path}/ocean_benchmark1.in"
process.output = "654.roms.stdout.txt" # Salida estandar del benchmark

system.workload = SEWorkload.init_compatible(executable)

# Asignamos el proceso a ambas CPUs de la lista
for cpu in system.cpu:
    cpu.workload = process
    cpu.createThreads()

# --- 5. Ejecucion ---
root = Root(full_system=False, system=system)
m5.instantiate()

# FASE 1: Salto Rapido (Fast-Forward)
# Usamos max_insts para detener la simulacion exactamente al llegar al objetivo
print(">>> Fase 1: Saltando 1 millon de instrucciones (Fast-Forward)...")
system.cpu[0].max_insts_any_thread = 10000 
exit_event = m5.simulate()
print("Sali de Fase 1 en el tick %d debido a %s" % (m5.curTick(), exit_event.getCause()))

# FASE 2: Cambio de CPU Manual Seguro
print(">>> Fase 2: Realizando cambio de CPU (Switching)...")
m5.drain() # Vacia buffers de memoria

# Intercambio de estado
system.cpu[1].takeOverFrom(system.cpu[0])

# Actualizacion de flags de actividad (Evita el hang)
system.cpu[0].switched_out = True
system.cpu[1].switched_out = False

m5.resume() # Reanuda el motor de eventos

# FASE 3: Calentamiento (Warmup)
print(">>> Fase 3: Calentando caches BRRIP (500k instrucciones)...")
system.cpu[1].max_insts_any_thread = 50000
exit_event = m5.simulate()

# FASE 4: Medicion ROI
print(">>> Fase 4: Medicion ROI (1 millon de instrucciones)...")
m5.stats.reset()
system.cpu[1].max_insts_any_thread = 10000
exit_event = m5.simulate()

print("Simulacion finalizada en tick %d por %s" % (m5.curTick(), exit_event.getCause()))