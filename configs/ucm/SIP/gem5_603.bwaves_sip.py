import m5
from m5.objects import *
import os

# --- Configuracion del Sistema ---
system = System()
system.clk_domain = SrcClockDomain(clock='3.2GHz', voltage_domain=VoltageDomain())
system.mem_mode = 'atomic' # Obligatorio para AtomicSimpleCPU
system.mem_ranges = [AddrRange('16GB')]
system.membus = SystemXBar()

# --- CPU para Profiling ---
# Usamos AtomicSimpleCPU porque es el unico que genera BBVs de forma eficiente
system.cpu = AtomicSimpleCPU()

# --- CONFIGURACION SIMPOINT (CRITICO) ---
# El intervalo estandar en la literatura es de 100 millones de instrucciones
interval = 100000000 
system.cpu.addSimPointProbe(interval)
# Conexiones basicas (sin caches para ir mas rapido en esta fase)
system.cpu.icache_port = system.membus.cpu_side_ports
system.cpu.dcache_port = system.membus.cpu_side_ports

system.cpu.createInterruptController()
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR4_2400_8x8() #device_size='16GB')
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# --- Configuracion del Proceso (SPEC2017) ---
#executable = '/scratch/rrodriguez/SPEC2017/603.bwaves_s/speed_bwaves_base.x86-64'
#process = Process(executable=executable, cwd=os.path.dirname(executable))
#process.input = os.path.dirname(executable) + "/bwaves_1.in"
base_path = "/scratch/rrodriguez/SPEC2017/603.bwaves_s/"
executable = base_path + "speed_bwaves_base.x86-64" # Ajustar nombre exacto del binario

process = Process()
process.executable = executable
# bwaves_s suele recibir un argumento que indica el prefijo del archivo de entrada
process.cmd = [executable, "bwaves_1"] 
# Redirigimos el archivo de entrada (.in) al stdin del proceso
process.input = base_path + "bwaves_1.in" 

system.cpu.workload = process
system.cpu.createThreads()
system.workload = SEWorkload.init_compatible(executable)

root = Root(full_system=False, system=system)
m5.instantiate()

print("Iniciando generacion de BBV... Esto puede tardar segun el benchmark.")
exit_event = m5.simulate()
print(f"Finalizado: {exit_event.getCause()}")
