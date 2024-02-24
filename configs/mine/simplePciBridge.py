import sys
from pathlib import Path

import m5

# import all of the SimObjects
from m5.objects import *

sys.path.append(str(Path(__file__).resolve().parents[1]))
from common import ObjectList

# create the system we are going to simulate
system = ArmSystem()

# Set the clock frequency of the system (and all of its children)
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = "1GHz"
system.clk_domain.voltage_domain = VoltageDomain()

# Set up the system
system.mem_mode = "timing"  # Use timing accesses
system.mem_ranges = [AddrRange("8192MB")]  # Create an address range

# Create a simple CPU
# You can use ISA-specific CPU models for different workloads:
# `RiscvTimingSimpleCPU`, `ArmTimingSimpleCPU`.
system.cpu = ArmTimingSimpleCPU()
# system.cpu = X86TimingSimpleCPU()

# Create a memory bus, a system crossbar, in this case
system.membus = SystemXBar()

# Hook the CPU ports up to the membus
system.cpu.icache_port = system.membus.cpu_side_ports
system.cpu.dcache_port = system.membus.cpu_side_ports

# create the interrupt controller for the CPU and connect to the membus
system.cpu.createInterruptController()

# For X86 only we make sure the interrupts care connect to memory.
# Note: these are directly connected to the memory bus and are not cached.
# For other ISA you should remove the following three lines.

# system.cpu.interrupts[0].pio = system.membus.mem_side_ports
# system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
# system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

# Create a DDR3 memory controller and connect it to the membus
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# Connect the system up to the membus
system.system_port = system.membus.cpu_side_ports


# create the PciBridge
# system.PciBridge = PciBridge()
# system.PciBridge.sendUpPort
# system.PciBridge.receiveUpPort
# system.PciBridge.sendDownPort1
# system.PciBridge.receiveDownPort1
# system.PciBridge.sendDownPort2
# system.PciBridge.receiveDownPort2
# system.PciBridge.sendDownPort3
# system.PciBridge.receiveDownPort3
# system.PciBridge.sendUpPort = system.membus.cpu_side_ports
# system.PciBridge.receiveUpPort = system.membus.mem_side_ports


# use the version2 Pcibridge
system.pcie1 = PCIELink(lanes=2, speed=5, mps=5, max_queue_size=10)
system.pcie2 = PCIELink(lanes=2, speed=5, mps=5, max_queue_size=10)
system.pcie3 = PCIELink(lanes=2, speed=5, mps=5, max_queue_size=10)
system.pcie4 = PCIELink(lanes=2, speed=5, mps=5, max_queue_size=10)
system.pcie5 = PCIELink(lanes=2, speed=5, mps=5, max_queue_size=10)
system.pcie6 = PCIELink(lanes=2, speed=5, mps=5, max_queue_size=10)

machine_type = "VExpress_GEM5_V1"
platform_class = ObjectList.platform_list.get(machine_type)

system.realview = platform_class()
system.realview.voltage_domain = VoltageDomain()
system.realview.vnc = VncInput()
system.realview.device = SerialDevice()
# system.realview.bootmem =
# system._bootmem = system.realview.bootmem
system.RootComplex = RootComplex()
system.switch = PCIESwitch()
system.RootComplex.host = system.realview.pci_host
system.switch.host = system.realview.pci_host


# GenericArmPciHost
system.RootComplex.response = system.membus.mem_side_ports
system.RootComplex.request_dma = system.membus.cpu_side_ports

system.RootComplex.response_dma1 = system.pcie1.upstreamRequest
system.RootComplex.response_dma2 = system.pcie2.upstreamRequest
system.RootComplex.response_dma3 = system.pcie3.upstreamRequest
system.RootComplex.request1 = system.pcie1.upstreamResponse
system.RootComplex.request2 = system.pcie2.upstreamResponse
system.RootComplex.request3 = system.pcie3.upstreamResponse


system.pcie1.downstreamRequest = system.switch.response
system.pcie1.downstreamResponse = system.switch.request_dma

system.pcie4.upstreamRequest = system.switch.response_dma1
system.pcie4.upstreamResponse = system.switch.request1
system.pcie5.upstreamRequest = system.switch.response_dma2
system.pcie5.upstreamResponse = system.switch.request2
system.pcie6.upstreamRequest = system.switch.response_dma3
system.pcie6.upstreamResponse = system.switch.request3


# system.pcie4.downstreamRequest  = system.switch.response_dma1
# system.pcie4.downstreamResponse = system.switch.request1
# system.pcie5.downstreamRequest  = system.switch.response_dma2
# system.pcie5.downstreamResponse = system.switch.request2
# system.pcie6.downstreamRequest  = system.switch.response_dma3
# system.pcie6.downstreamResponse = system.switch.request3

system.realview.cxlmemdevice1 = CxlMemory(
    pci_bus=3, pci_dev=0, pci_func=0, InterruptLine=2, InterruptPin=1
)
system.realview.cxlmemdevice1.pio = system.pcie3.downstreamRequest
system.realview.cxlmemdevice1.dma = system.pcie3.downstreamResponse
system.realview.cxlmemdevice1.host = system.realview.pci_host

system.realview.cxlmemdevice2 = CxlMemory(
    pci_bus=4, pci_dev=0, pci_func=0, InterruptLine=2, InterruptPin=1
)
system.realview.cxlmemdevice2.pio = system.pcie4.downstreamRequest
system.realview.cxlmemdevice2.dma = system.pcie4.downstreamResponse
system.realview.cxlmemdevice2.host = system.realview.pci_host

# Attach any PCI devices this platform supports
system.realview.attachPciDevices()

# try to add Cxl Memory to the system
# system.RootComplex.device1= CxlMemory()
# Here we set the X86 "hello world" binary. With other ISAs you must specify
# workloads compiled to those ISAs. Other "hello world" binaries for other ISAs
# can be found in "tests/test-progs/hello".
binary = "tests/test-progs/hello/bin/arm/linux/hello"

system.workload = SEWorkload.init_compatible(binary)

# Create a process for a simple "Hello World" application
process = Process()
# Set the command
# cmd is a list which begins with the executable (like argv)
process.cmd = [binary]
# Set the cpu to use the process as its workload and create thread contexts
system.cpu.workload = process
system.cpu.createThreads()

# set up the root SimObject and start the simulation
root = Root(full_system=False, system=system)
# instantiate all of the objects we've created above
m5.instantiate()

print("Beginning simulation!")
exit_event = m5.simulate()
print("Exiting @ tick %i because %s" % (m5.curTick(), exit_event.getCause()))
