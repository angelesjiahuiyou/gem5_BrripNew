import m5
from m5.objects import *

# --- Configuracion del Sistema ---
system = System()

# Configuracion del reloj y voltaje
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = '3.2GHz'
system.clk_domain.voltage_domain = VoltageDomain()

# Configuracion de la memoria principal
system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('16GB')] # ROMS requiere bastante memoria
system.membus = SystemXBar()

# --- Configuracion del Procesador (X86 O3) ---
system.cpu = X86O3CPU()

# --- Configuracion de Caches ---

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
system.cpu.dcache = Cache(size='32kB',
                         assoc=8,
                         tag_latency=2,
                         data_latency=2,
                         response_latency=2,
                         mshrs=4,
                         tgts_per_mshr=20,
                         replacement_policy=LRURP())

# L2 Cache (1MB, SHiP)
system.l2cache = Cache(size='1MB',
                      assoc=32,
                      tag_latency=20,
                      data_latency=20,
                      response_latency=20,
                      mshrs=20,
                      tgts_per_mshr=12,
                      replacement_policy=SHiPRP())

# Conexiones de la jerarquia de memoria
system.cpu.icache.cpu_side = system.cpu.icache_port
system.cpu.dcache.cpu_side = system.cpu.dcache_port

system.l2bus = L2XBar()
system.cpu.icache.mem_side = system.l2bus.cpu_side_ports
system.cpu.dcache.mem_side = system.l2bus.cpu_side_ports

system.l2cache.cpu_side = system.l2bus.mem_side_ports
system.l2cache.mem_side = system.membus.cpu_side_ports

# Conexiones de interrupciones y memoria principal
system.cpu.createInterruptController()
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR4_2400_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# --- 4. Configuracion del Benchmark: 644.nab_s (Train) ---
# Ruta indicada por el usuario
base_path = "/scratch/rrodriguez/SPEC2017/644.nab_s"
executable = f"{base_path}/nab_s_base.x86-64"
process = Process()
# Buscamos el ejecutable (ajustar el nombre exacto del binario si varia)
process.executable = executable

# Comandos y argumentos para el dataset 'train' de 644.nab_s
# Segun SPEC2017: nab_s [input_file] [seed] [steps]
process.cmd = [process.executable, 'gcn4dna', '1850041461', '300']
process.cwd = base_path # Directorio de trabajo para que encuentre los archivos

system.cpu.workload = process
system.cpu.createThreads()

system.workload = SEWorkload.init_compatible(executable)

# --- Logica de Warmup y Medicion ---

# Definimos los limites de instrucciones
warmup_insts = 2000000000
measurement_insts = 1000000000
total_insts = warmup_insts + measurement_insts

#Configuramos el primer limite (Warmup)
system.cpu.max_insts_any_thread = warmup_insts

root = Root(full_system = False, system = system)
m5.instantiate()

print(f"Iniciando Warmup: {warmup_insts} instrucciones...")
exit_event = m5.simulate()

# Configuramos el primer limite (Warmup)
#system.cpu.max_insts_any_thread = warmup_insts

# Al llegar al limite de warmup, reseteamos estadisticas y cambiamos el limite
if exit_event.getCause() == "a thread reached the max instruction count":
    print("Warmup finalizado. Reseteando estadisticas y comenzando medicion...")
    m5.stats.dump()
#    m5.stats.reset()
    
    # Configuramos el limite para la medicion detallada
    #system.cpu.max_insts_any_thread = measurement_insts
    system.cpu.scheduleInstStop(0, measurement_insts, "Escritura de estadisticas tras medicion") 
    
    print(f"Iniciando Medicion: {measurement_insts} instrucciones...")
    exit_event = m5.simulate()
else:
    print(f"Simulacion interrumpida prematuramente: {exit_event.getCause()}")

# Volcado final de estadisticas
print(f"Simulacion finalizada en el tick {m5.curTick()} debido a {exit_event.getCause()}")
m5.stats.dump()