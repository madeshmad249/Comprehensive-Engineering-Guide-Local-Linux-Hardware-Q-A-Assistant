"""Realistic Linux hardware command fixtures for testing and simulated execution."""

MOCK_DMIDECODE_MEMORY = """# dmidecode 3.5
Getting SMBIOS data from sysfs.
SMBIOS 3.3.0 present.

Handle 0x000E, DMI type 16, 23 bytes
Physical Memory Array
	Location: System Board
	Use: System Memory
	Error Correction Type: None
	Maximum Capacity: 64 GB
	Error Information Handle: Not Provided
	Number Of Devices: 2

Handle 0x000F, DMI type 17, 92 bytes
Memory Device
	Array Handle: 0x000E
	Error Information Handle: Not Provided
	Total Width: 64 bits
	Data Width: 64 bits
	Size: 16 GB
	Form Factor: SODIMM
	Set: None
	Locator: ChannelA-DIMM0
	Bank Locator: BANK 0
	Type: DDR4
	Type Detail: Synchronous Unbuffered (Unregistered)
	Speed: 3200 MT/s
	Manufacturer: Micron Technology
	Serial Number: 28B712A4
	Asset Tag: 9876543210
	Part Number: 16ATF2G64HZ-3G2E2
	Rank: 2
	Configured Memory Speed: 3200 MT/s
	Minimum Voltage: 1.2 V
	Maximum Voltage: 1.2 V
	Configured Voltage: 1.2 V

Handle 0x0010, DMI type 17, 92 bytes
Memory Device
	Array Handle: 0x000E
	Error Information Handle: Not Provided
	Total Width: Unknown
	Data Width: Unknown
	Size: No Module Installed
	Form Factor: SODIMM
	Set: None
	Locator: ChannelB-DIMM0
	Bank Locator: BANK 1
	Type: Unknown
	Type Detail: None
	Speed: Unknown
	Manufacturer: Not Specified
	Serial Number: Not Specified
	Asset Tag: Not Specified
	Part Number: Not Specified
	Rank: Unknown
	Configured Memory Speed: Unknown
	Minimum Voltage: Unknown
	Maximum Voltage: Unknown
	Configured Voltage: Unknown
"""

MOCK_LSCPU = """Architecture:             x86_64
  CPU op-mode(s):         32-bit, 64-bit
  Address sizes:          48 bits physical, 48 bits virtual
  Byte Order:             Little Endian
CPU(s):                   16
  On-line CPU(s) list:    0-15
Vendor ID:                AuthenticAMD
  Model name:             AMD Ryzen 7 PRO 5850U with Radeon Graphics
    CPU family:           25
    Model:                80
    Thread(s) per core:   2
    Core(s) per socket:   8
    Socket(s):            1
    Stepping:             0
    Frequency boost:      enabled
    CPU(s) scaling MHz:   67%
    CPU max MHz:          4400.0000
    CPU min MHz:          1400.0000
    BogoMIPS:             3793.12
    Flags:                fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ht syscall nx mmxext fxsr_opt pdpe1gb rdtscp lm constant_tsc rep_good nopl nonstop_tsc cpuid extd_apicid aperfmperf rapl pni pclmulqdq monitor ssse3 fma cx16 sse4_1 sse4_2 movbe popcnt aes xsave avx f16c rdrand lahf_lm cmp_legacy svm extapic cr8_legacy abm sse4a misalignsse 3dnowprefetch osvw ibs skinit wdt tce topoext perfctr_core perfctr_nb bpext perfctr_llc mwaitx cpb cat_l3 cdp_l3 hw_pstate ssbd mba ibrs ibpb stibp vmmcall fsgsbase bmi1 avx2 smep bmi2 erms invpcid cqm rdt_a rdseed adx smap clflushopt clwb sha_ni xsaveopt xsavec xgetbv1 xsaves cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local clzero irperf xsaveerptr rdpru wbnoinvd cppc arat npt lbrv svm_lock nrip_save tsc_scale vmcb_clean flushbyasid decodeassists pausefilter pfthreshold v_vmsave_vmload vgif v_spec_ctrl umip pku ospke vaes vpclmulqdq rdpid overflow_recov succor smca fsrm
Virtualization features:  
  Virtualization:         AMD-V
Caches (sum of all):      
  L1d:                    256 KiB (8 instances)
  L1i:                    256 KiB (8 instances)
  L2:                     4 MiB (8 instances)
  L3:                     16 MiB (1 instance)
NUMA:                     
  NUMA node(s):           1
  NUMA node0 CPU(s):      0-15
Vulnerabilities:          
  Itlb multihit:          Not affected
  L1tf:                   Not affected
  Mds:                    Not affected
  Meltdown:               Not affected
  Spec store bypass:      Mitigation; Speculative Store Bypass disabled via prctl
  Spectre v1:             Mitigation; usercopy/swapgs barriers and __user pointer sanitization
  Spectre v2:             Mitigation; Retpolines, IBPB conditional, IBRS_FW, STIBP always-on, RSB filling, PBRSB-eIBRS Not affected
  Srbds:                  Not affected
  Tsx async abort:        Not affected
"""

MOCK_LSBLK_JSON = """{
   "blockdevices": [
      {
         "name": "nvme0n1",
         "size": "512110190592",
         "type": "disk",
         "mountpoint": null,
         "model": "SAMSUNG MZVL2512HCJQ-00BL7",
         "rota": false,
         "tran": "nvme",
         "children": [
            {
               "name": "nvme0n1p1",
               "size": "1073741824",
               "type": "part",
               "mountpoint": "/boot/efi",
               "model": null,
               "rota": false,
               "tran": null
            },
            {
               "name": "nvme0n1p2",
               "size": "2147483648",
               "type": "part",
               "mountpoint": "/boot",
               "model": null,
               "rota": false,
               "tran": null
            },
            {
               "name": "nvme0n1p3",
               "size": "508888965120",
               "type": "part",
               "mountpoint": "/",
               "model": null,
               "rota": false,
               "tran": null
            }
         ]
      }
   ]
}"""

MOCK_FREE_BYTES = """               total        used        free      shared  buff/cache   available
Mem:     16155930624  4210450432  6124568576   528482304  5820911616 11417001984
Swap:     8589934592           0  8589934592
"""

MOCK_PROC_MEMINFO = """MemTotal:       15777276 kB
MemFree:         5981024 kB
MemAvailable:   11149416 kB
Buffers:          412892 kB
Cached:          5269784 kB
SwapCached:            0 kB
Active:          5629104 kB
Inactive:        3128904 kB
SwapTotal:       8388608 kB
SwapFree:        8388608 kB
Dirty:               144 kB
Writeback:             0 kB
AnonPages:       3075332 kB
Mapped:          1249820 kB
Shmem:            516096 kB
KReclaimable:     351240 kB
Slab:             684200 kB
SReclaimable:     351240 kB
SUnreclaim:       332960 kB
KernelStack:       24576 kB
PageTables:        54320 kB
"""

MOCK_LSPCI = """Slot:	00:00.0
Class:	Host bridge [0600]
Vendor:	Advanced Micro Devices, Inc. [AMD]
Device:	Renoir/Cezanne Root Complex [1022:1630]
SVendor:	Lenovo
SDevice:	ThinkPad T14 Gen 2a

Slot:	00:02.1
Class:	PCI bridge [0604]
Vendor:	Advanced Micro Devices, Inc. [AMD]
Device:	Renoir/Cezanne PCIe GPP Bridge [1022:1634]

Slot:	00:08.1
Class:	PCI bridge [0604]
Vendor:	Advanced Micro Devices, Inc. [AMD]
Device:	Renoir Internal PCIe GPP Bridge to Bus [1022:1635]

Slot:	04:00.0
Class:	VGA compatible controller [0300]
Vendor:	Advanced Micro Devices, Inc. [AMD/ATI]
Device:	Cezanne [Radeon Vega Series / Radeon Vega Mobile Series] [1002:1638]
SVendor:	Lenovo
SDevice:	ThinkPad T14 Gen 2a
Rev:	c1

Slot:	04:00.1
Class:	Audio device [0403]
Vendor:	Advanced Micro Devices, Inc. [AMD/ATI]
Device:	Renoir Radeon High Definition Audio Controller [1002:1637]
SVendor:	Lenovo
SDevice:	ThinkPad T14 Gen 2a

Slot:	03:00.0
Class:	Non-Volatile memory controller [0108]
Vendor:	Samsung Electronics Co Ltd
Device:	NVMe SSD Controller PM9A1/980PRO [144d:a80a]
SVendor:	Samsung Electronics Co Ltd
SDevice:	ThinkPad T14 Gen 2a
"""

MOCK_DMIDECODE_SYSTEM = """# dmidecode 3.5
Getting SMBIOS data from sysfs.
SMBIOS 3.3.0 present.

Handle 0x0001, DMI type 1, 27 bytes
System Information
	Manufacturer: LENOVO
	Product Name: 20W0005HUS
	Version: ThinkPad T14 Gen 2
	Serial Number: PF39X123
	UUID: 39a4892c-6338-11ec-90d6-0242ac120003
	Wake-up Type: Power Switch
	SKU Number: LENOVO_MT_20W0_BU_Think_FM_ThinkPad T14 Gen 2
	Family: ThinkPad T14 Gen 2

Handle 0x0002, DMI type 2, 15 bytes
Base Board Information
	Manufacturer: LENOVO
	Product Name: 20W0005HUS
	Version: SDK0J40697 WIN
	Serial Number: 1S20W0005HUSPF39X123
	Asset Tag: Not Available
	Feature Flags:
		Board is a hosting board
		Board is replaceable
	Location In Chassis: Default string
	Chassis Handle: 0x0003
	Type: Motherboard
"""

MOCK_SYS_DMI_ID = {
    "sys_vendor": "LENOVO\n",
    "product_name": "20W0005HUS\n",
    "product_version": "ThinkPad T14 Gen 2\n",
    "bios_version": "N34ET52W (1.52 )\n",
    "bios_date": "08/15/2023\n",
    "chassis_type": "10\n"  # 10 is Notebook
}

MOCK_OS_RELEASE = """NAME="Ubuntu"
VERSION="24.04 LTS (Noble Numbat)"
ID=ubuntu
ID_LIKE=debian
PRETTY_NAME="Ubuntu 24.04 LTS"
VERSION_ID="24.04"
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=noble
"""
