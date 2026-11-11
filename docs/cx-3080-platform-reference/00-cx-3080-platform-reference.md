# CX-3080 Platform Reference

## About this article

This is a base reference for Riverbed CX-3080 appliances reused in a home lab. It covers what the hardware is, what every BIOS and BMC setting does, the baseline every unit gets, and how to harden and tune a unit before an OS goes on.

**Where the facts come from.** One reference unit was examined end to end over three days. The sources were photos, two full BIOS walks over serial, a Linux hardware inventory taken from a root shell, the BMC web interface and the console logs. Other units of the same model are assumed identical until their own inventory says otherwise.

**How facts are labelled.**

- **Measured:** read directly off the reference unit.
- **From the CX-780:** learned on the smaller Riverbed unit, from a Netgate forum thread, and not re-tested here.
- **Unconfirmed:** a reasoned guess that hasn't been tested.

**Conventions.**

- Menu paths are written `Menu → Submenu → Option`.
- *Factory* means the value found on the reference unit as received; *Baseline* means the value every unit should be set to.
- Placeholders in angle brackets stand for your own values: `<BMC_IP>`, `<BMC_USER>`, `<UNIT_SERIAL>`, `<MGMT_SUBNET>` (the management subnet) and `<NETMASK>` (its netmask). Per-unit values live in the unit register (Appendix A).
- PCI addresses are written in the short bus:device.function form that `lspci -s` accepts, which drops the device number's leading zero.
- No password appears in any of these documents.

**Related documents.** Where this article says "the ipmitool guide", it means a companion guide to running ipmitool against this box: power, console, sensors, event log and BMC administration. ipmitool's own manual page covers the same commands.

**Where to start.**

| You want to… | Go to |
| --- | --- |
| Bring a new unit to baseline | Baseline bring-up procedure |
| Know what a BIOS option does | BIOS setup reference (three parts) |
| Manage a unit remotely | BMC reference, then the ipmitool guide |
| Lock a unit down or tune it | Security hardening; Efficiency and performance |
| Prepare an OS install | OS notes |
| Get a unit ready for its OS install, item by item | Appendix D: Pre-OS-install run sheet |
| Fix something that went wrong | Known issues, quirks and open items |

## Platform identity

The CX-3080 is a 1U x86 network appliance. It's built by Delta Networks (DNI) around an 8-core Xeon D-1553N, with 12 network ports and an AMI BMC. Riverbed sold the same hardware under two product lines, so the name on the case and the name in the firmware differ.

| Where you look | What it says |
| --- | --- |
| Front label | SteelHead CX-3080 Series |
| Firmware (DMI/FRU) product name | Riverbed SteelConnect EX-3080 |
| SKU / part number | SDEX-03080-B010, product version 03 |
| Motherboard | DNI SNRACK-1553N, board part 5508015887, silkscreen rev A1 |
| Riverbed codename | "Snook" (chassis part "Snook Rackmount", FRU file `Snook_r_fru_v01.bin`) |
| BIOS | AMI Aptio V core 5.14, project 0ACJZ 0.11, version x0.45V |
| BMC | ASPEED AST2520 running AMI MegaRAC SP-X 0.53.1108131520 |
| Factory OS | SteelConnect EX: Versa Networks FlexVNF on Ubuntu 14.04, kernel 4.4.0-151 |
| Manufactured | Board FRU date (read it with `ipmitool fru print 0`) |

**SteelHead vs SteelConnect.** SteelHead CX is Riverbed's WAN-optimisation line; SteelConnect EX is its SD-WAN line, built on Versa Networks software. The reference unit is labelled SteelHead but was built and shipped as a SteelConnect EX. For home-lab use the difference doesn't matter: the hardware, BIOS and BMC are what count, and the factory OS gets replaced.

**Family.** The smaller CX-780 uses the same idea: an x86 board, bypass relays, the same BIOS vendor and the Latch-Relay Mode option. A Netgate forum thread on the CX-780 is the source of the relay behaviour in this article. A community report on a CX-580 is the source of the one known NVMe quirk (see Known issues).

**Age and use.** The reference unit's drives show 15,953 power-on hours (about 22 months) and the BMC reports 641 days powered. Expect other units to be similar: lightly used ex-enterprise stock.

## Hardware specification

Everything below was measured on the reference unit unless marked otherwise.

### Processor

| Item | Value |
| --- | --- |
| Model | Intel Xeon D-1553N (Broadwell-DE, network SKU) |
| Cores / threads | 8 / 16 (Hyper-Threading must be enabled in BIOS; factory had it off) |
| Clocks | 2.3 GHz base (ratio 0x17), 0.8 GHz minimum (ratio 0x08), 2.7 GHz max turbo |
| Cache | L1 512 KB, L2 2 MB, L3 12 MB |
| TDP | 65 W |
| CPUID / stepping | 0x50665 (family 6, model 86, stepping 5) |
| Microcode | 0x0E00000C in BIOS; 0x0E000012 loaded by Ubuntu at boot; 0x0E000014 or later in current intel-microcode packages |
| Notable features | VT-x, VT-d, AES-NI, AVX2, RDRAND, TSX, cache allocation/monitoring, TXT-capable (off) |
| Known CPU flaws | Meltdown, Spectre v1/v2, SSB, L1TF, MDS (kernel mitigations apply; MDS leaks across SMT threads) |
| Built into the SoC | 4 × 10GbE (X552), QuickAssist (QAT), 8-channel CBDMA, SATA/USB/LPC/SMBus controller, Intel ME running Server Platform Services 3.0.3 (build 59) |

### Memory

| Item | Value |
| --- | --- |
| Slots | 2 DDR4 DIMM slots: DIMM\_A1 (channel 0) and DIMM\_B1 (channel 1) |
| Fitted (reference unit) | 8 GB single-rank x8 in A1 (part WD4RE9008G26MSC-RVB) + 16 GB single-rank x4 in B1 (part SH5722G4RIV26P1-SC); both report Samsung |
| Speed | Modules rated 2666, run at 2400 (the CPU's maximum) |
| Type | Registered ECC (setup allows UDIMMs and RDIMMs); multi-bit ECC, patrol scrub every 24 h, demand scrub on |
| Maximum | Firmware reports 64 GB (2 × 32 GB). Intel rates the CPU for 128 GB, but that needs four slots |

The mixed 8 GB + 16 GB fit works, but only 16 GB of it can interleave across both channels. A matched pair is the better fit for a production unit.

**Fitting a matched pair.**

- **What to buy:** two identical DDR4 registered ECC DIMMs (RDIMMs), 2400 MT/s or faster, the same size and rank. 2 × 16 GB gives 32 GB, fully interleaved. 2 × 32 GB is the firmware's stated maximum and hasn't been tested. Don't mix RDIMMs with unbuffered UDIMMs.
- **How:** power off, switch off at the rear rocker and unplug AC. Fit one DIMM in DIMM\_A1 and one in DIMM\_B1, pressing down until both latches close fully.
- **Check:** watch for the healthy power-on signature, then read Total Memory on setup's Main tab. Fans that keep cycling with no console output mean a DIMM isn't seated (Known issues).

### Storage

All storage hangs off the SoC's six-port SATA controller in AHCI mode. There's no RAID controller.

| SATA port | Where | Reference unit fit | Notes |
| --- | --- | --- | --- |
| P0 | Rear hot-swap 2.5" bay | Seagate Exos 7E2000 1 TB, ST1000NX0423, 7,200 rpm | 15,953 h, about 20 GB written, no errors |
| P1 | Rear hot-swap 2.5" bay | Same model | Held the Versa root filesystem; about 75 TB written, no errors |
| P2 | On-board M.2 | Intel D3-S4510 240 GB (SSDSCKKB240G8), SATA | Data-centre SSD with power-loss protection; about 1 TB written |
| P3 | On-board M.2 | Same model | Effectively unused |
| P4 | On-board module | Virtium StorFly 30 GB (VSFBM4CC030G-15A) | Industrial SSD, no partitions on the reference unit |
| P5 | Not populated | none |  |

The BIOS lists both M.2 slots as `PCH M2 Slot 1/2 = SATA3`, which suggests they could be switched to PCIe for NVMe. That's unconfirmed (see Known issues).

### Network

| Ports | Controller | Details |
| --- | --- | --- |
| 1–4 (PRI, AUX, LAN0\_0, WAN0\_0) | Intel I350 quad-port #1 (PCI 07:0.0–3) | 8086:1521, NVM 1.63, PCIe Gen2 x4, 8 SR-IOV VFs per port |
| 5–8 (LAN0\_1, WAN0\_1, 7, 8) | Intel I350 quad-port #2 (PCI 09:0.0–3) | Same as above |
| 9–12 (SFP+) | Xeon D built-in X552 10GbE (PCI 03:0.0/1, 05:0.0/1) | 8086:15ac, NVM 0x800008f7/f8, two Inphi CS4227 PHYs, 64 SR-IOV VFs per port |

- All MACs sit in Riverbed's OUI 00:0E:B6.
- Wake-on-LAN works on ports 1 and 5 only (the first port of each I350).
- The BMC shares port 1 by default and can be moved to port 2 (see BMC reference).
- Every port has its own IOMMU group, so any single port can be passed through to a VM.

### PCIe layout

| CPU root port | Width / speed | What's attached |
| --- | --- | --- |
| 00:1.0 (IIO port 1, bifurcation x8) | Gen3 x8 | Expansion slot (x16 physical), empty |
| 00:2.0 | Internal | QAT co-processor (02:0.0) |
| 00:2.2 / 00:2.3 | Internal | X552 10GbE pairs (03:0.x, 05:0.x) |
| 00:3.0 (IIO port 3A, bifurcation x4x4x4x4) | Gen2 x4 link (Gen3 capable) | I350 #1 |
| 00:3.1 (port 3B) | Gen2 x4 link | I350 #2 |
| 00:3.2 / 00:3.3 (ports 3C/3D) | Gen3 x4, no link | Enabled, nothing attached; destination unknown |

No PCH PCIe root ports are active and there's no VGA device. That's why the BMC offers serial-over-LAN but no graphical remote screen.

### Other devices

| Item | Value |
| --- | --- |
| QuickAssist (QAT) | 8086:6f54 at 02:0.0, 16 SR-IOV VFs; no driver in mainline Linux or FreeBSD 14 (see OS notes) |
| TPM | STMicro TPM 2.0, firmware 73.4, TIS interface, SHA-1 and SHA-256 banks; exposed as /dev/tpm0 |
| BMC | ASPEED AST2520 with 1 GB DDR4; IPMI 2.0 over KCS and USB; serial-over-LAN; virtual USB CD and hard disk |
| Serial | ttyS0 at 0x3F8 (the front RJ45 console); a second UART, ttyS1 at 0x2F8, purpose unknown |
| USB | Front USB-A and USB-C; xHCI + EHCI controllers |
| Power supplies | 2 × Delta DPS-550AB-22 P (rev S3F), 550 W, 12 V only, hot-swap, 1+1 redundant, readable over PMBus (input watts, temperature, fan) |
| Cooling | Fan module with 2 × Delta FFB0412SHN-A 40 mm fans, plus a fan in each PSU; front-to-back airflow |
| Bypass relays | 12 × Hongfa HFD4/3-S (non-latching) and 2 × HFD4/3-LS1 (single-coil latching) on ports 3–6 |

### Measured power and thermals

| State | Wall power | Notes |
| --- | --- | --- |
| Standby (host off, BMC on) | 12 W | One PSU connected |
| Idle at a root shell, all ports up | 48 W | HT on, C-states on, one PSU |

At idle the inlet read 22 °C, the outlet 34 °C, the CPU 38 °C, both DIMMs 26 °C and the PCH 34 °C. The fans ran at about 3,400 rpm. Loaded figures haven't been measured yet.

## Physical layout

### Front panel (left to right)

| Element | Notes |
| --- | --- |
| Power button | Ring glows amber in standby and blue when running (as observed) |
| SYS LEDs 1–4 | Meaning not yet identified |
| RESET pinhole | Hard reset, same as `ipmitool chassis power reset` |
| USB-C | Host USB |
| CONSOLE (RJ45) | Serial console, 8N1, no flow control. Works with a standard USB-to-RJ45 console cable (FTDI-based). Factory speed 9600; 115200 after the baseline |
| USB-A (under the console jack) | Host USB 3.0; boots installers |
| Ports 1–4 | PRI, AUX, LAN0\_0, WAN0\_0 (I350 #1) |
| Ports 5–8 | LAN0\_1, WAN0\_1, then two unlabelled ports (I350 #2) |
| SFP+ 9–12 | Two stacked pairs: 9 above 10, 11 above 12 (X552) |
| Expansion bay (blanked) | Behind it is the Gen3 x8 slot (x16 physical) |

Green board LEDs are visible through the grille to the left of the console jack.

**Port groups to remember.**

- PRI (port 1) carries the BMC's shared network connection by default.
- LAN0\_0/WAN0\_0 (ports 3/4) and LAN0\_1/WAN0\_1 (ports 5/6) are the two bypass pairs. They're dead whenever the box is off or in standby (see Bypass relays).
- Ports 7, 8 and 9–12 have no relays.

### Rear panel

| Element | Notes |
| --- | --- |
| Two 2.5" hot-swap drive bays | SATA P0 and P1 |
| Rocker switch (with a white dot) | Main power switch. It is not the identify LED |
| Two PSU bays | Delta DPS-550AB-22 P, hot-swap, 1+1. Either PSU alone runs the box |

### Inside the case

- **CPU** under a passive heatsink, cooled by the front-to-back airflow from the fan module.
- **Fan module:** two Delta FFB0412SHN-A 40 mm fans in one removable carrier.
- **DIMM slots:** two, beside the CPU. A badly seated DIMM causes a no-video, fan-cycling POST loop (see Known issues).
- **M.2 sockets:** three in a row.
  - Two 2280 sockets hold the Intel 240 GB SSDs (SATA P2 and P3).
  - The third holds the 30 GB Virtium M.2 2242 module (SATA P4). Its board also has a 2280 mounting point.
- **CMOS battery:** a coin cell beside the M.2 area. Pulling it for 5 minutes was tried during bring-up. It changed the fan pattern on the next boot but didn't help reach setup: the real problem was the console speed.
- **Bypass relay bank:** 14 relays beside ports 3–6.
- **SFP cages and two Inphi CS4227 PHYs** behind ports 9–12.
- **BMC:** ASPEED AST2520 with its own 1 GB DDR4 chip.
- **PCIe slot:** behind the front expansion bay.
- **BIOS flash:** soldered to the board, not socketed. DMI claims "BIOS ROM is socketed", but that's a template default.
- **TPM:** present and working, but its location on the board hasn't been identified.

### Headers and jumpers

| Designator | Form | What it is | Rule |
| --- | --- | --- | --- |
| J23 | 1×3, jumper fitted | Unknown, probably a clear/recovery option | Leave the jumper where it is |
| J21 | 1×8 | Unknown (possibly debug UART or GPIO) | Don't connect anything |
| J22 | 1×3 | Unknown | Don't connect anything |
| CON2 | 1×3, no jumper | Unknown | Leave open |
| 2×4 header above the PCIe slot | 2×4 | Possibly an SPI programming header for the BIOS flash (unconfirmed) | Only of interest for recovering a bricked BIOS |
| SWB1 | Push button | Unknown | Don't press without a reason |

### Rack mounting

The unit is 1U. It takes the supplied slide rails or front ears. Airflow is front to back, so the front (port side) faces the cold aisle.

### Healthy power-on signature

Apply power and press the power button, then watch for these timings. Any deviation is your first clue that something's wrong.

| Time | What happens |
| --- | --- |
| 0 s | Fans spin up loud; ports 3–6 show flashing amber (relays in bypass) |
| \~17 s | Fans drop to quiet |
| \~21 s | Amber on ports 3–6 goes out: the relays have switched to normal |
| \~37 s | A single beep, then progress codes and the setup prompt on the console |

## Bypass relays and Latch-Relay Mode

Ports 3–6 sit behind relays that Riverbed used for "fail-to-wire" bypass. With **Latch-Relay Mode = 1** (the factory and baseline value), the relays switch to normal operation during POST and the ports then behave as ordinary NICs. While the box is off or in standby, ports 3–6 pass no traffic.

### Hardware

- 14 relays next to ports 3–6:
  - 12 Hongfa HFD4/3-S: 3 V, non-latching, two-pole changeover signal relays.
  - 2 Hongfa HFD4/3-LS1: single-coil latching. These hold their position with no power, which is presumably what sets the unpowered state.
- **Pairs:** LAN0\_0 ↔ WAN0\_0 (ports 3/4) and LAN0\_1 ↔ WAN0\_1 (ports 5/6).
- **Indicator:** the amber LEDs on ports 3–6 flash while the relays are in bypass. They go out when the relays switch to normal, about 21 s after power-on, with an audible click.

### Control

The relays are controlled only by the BIOS/BMC firmware, through `Server Mgmt → Latch-Relay Mode`. It takes values 0 to 6.

| Mode | Known behaviour | Source |
| --- | --- | --- |
| 1 | Relays switch to normal at POST; amber LEDs go out | Factory value here; confirmed on the reference unit and on the CX-780 |
| 3 | Same visible result as 1 | Confirmed on the CX-780 |
| 0, 2, 4, 5, 6 | Unknown | Not tested |

The factory Versa OS contained no relay driver, kernel module or script, and no ipmitool raw command for the relays is known. An OS on this box can't see or change the relays.

AI-generated descriptions of the modes circulate in the CX-780 forum thread. They're guesses, so don't rely on them.

### Rules

- Keep Latch-Relay Mode at **1**.
- After any "Restore Defaults", CMOS clear or BIOS update, check it again. Nobody knows what the defaults set it to.
- Don't use ports 3–6 for anything that must keep working while the box is powered off. They're fine for normal use once the host is up.
- Don't test other modes on a unit that's cabled to a live WAN. An unknown mode could bridge a WAN port straight to a LAN port.

**Source:** [Netgate forum: pfSense and Riverbed CX-780](https://forum.netgate.com/topic/183887/pfsense-and-riverbed-cx-780), with reports from two CX-780 owners.

## Access methods

There are two ways into the box. The front serial port is for first contact and recovery. The BMC, over the network, does everything after that. Neither needs a monitor: the box has no video output at all.

| Method | Works when | What it gives you |
| --- | --- | --- |
| Front serial console | Host on | BIOS setup, POST codes, GRUB, the OS console |
| BMC web UI (`https://<BMC_IP>`) | Any time AC is connected | Power control, sensors, event log, SOL, virtual media, BMC settings |
| Serial over LAN (SOL) | Host on, BMC reachable | Exactly the same console as the front port, over the network |
| ipmitool over the network | Any time AC is connected | Everything the web UI does, scriptable |
| ipmitool in-band (from the host OS) | Host running Linux | BMC administration with no network or password |

### Serial console settings

These are for PuTTY with a USB-to-RJ45 console cable on the Windows laptop. Check Device Manager for the cable's COM port number.

| Setting | Value |
| --- | --- |
| Speed | **9600** for a unit straight from the factory (BIOS only); **115200** once the baseline is applied. GRUB and Linux always use 115200 |
| Data / parity / stop bits | 8 / None / 1 |
| Flow control | None |
| Keyboard → Function keys | **VT100+** (needed for F2/F3/F4 in setup) |
| Logging | All session output, to a timestamped file |
| Scrollback | 20,000 lines or more |

Save two sessions, one at 9600 and one at 115200. A new unit needs 9600 for setup but 115200 for GRUB, and the wrong speed looks exactly like a dead console.

### Entering BIOS setup

1. Open the console at the BIOS speed (9600 factory, 115200 after the baseline) with logging on.
2. Power on and wait for the single beep, about 37 s in.
3. When progress codes start appearing (`98 9D 9C … B2`), tap **Esc** repeatedly.
4. Keep tapping through `Press <DEL> or <ESC> to enter setup.` until `Entering Setup...` appears.

The prompt lasts 1 s on a factory unit and 5 s after the baseline. The same method works over SOL. A remote alternative, `ipmitool chassis bootdev bios` followed by a reset, still needs a clean retest (see the ipmitool guide).

### Root shell on the factory OS (no login needed)

Use this to run the inventory script on a unit that still has the Versa install. Don't log into Versa itself: it holds the previous owner's configuration.

1. At the GRUB menu (115200), press `e`.
2. Go to the end of the line that starts with `linux` and add `  init=/bin/bash `.
3. Press Ctrl-X to boot.

You get `root@(none):/#` with the root filesystem mounted read-only, so a hard reset can't damage anything. Then:

```
mount -t proc proc /proc; mount -t sysfs sysfs /sys     # needed by most tools
modprobe ipmi_si; modprobe ipmi_devintf                 # enables in-band ipmitool
echo b > /proc/sysrq-trigger                            # immediate reboot
echo o > /proc/sysrq-trigger                            # immediate power-off
```

Quirks of this shell:

- **Ctrl-C does nothing.** The shell has no controlling terminal, so any looping command must stop by itself.
- **The USB stick isn't `sdf`.** It appears after the BMC's virtual drives. `/dev/sdf` on the reference unit was the BMC's empty virtual disk ("no medium"); the stick was `/dev/sdg1`.

### BMC web interface

- Browse to `https://<BMC_IP>` and accept the self-signed certificate warning.
- Log in as `<BMC_USER>` (user ID 2, `admin` on the reference unit).
- The BMC answers whenever AC power is connected, even with the host off.
- **New unit with an unknown BMC address:** read it in `Server Mgmt → BMC network configuration`. The same screen can set a static address. The factory setting was DHCP on port 1 (PRI).
- The UI includes Remote Control (SOL), Image Redirection (virtual media), Power Control, Sensor, FRU, Logs & Reports, Settings and Maintenance. Details are in the BMC reference section.

### Serial over LAN

- **Start it** from the web UI (Remote Control → Serial Over LAN → Activate) or with `ipmitool sol activate`.
- **While SOL is active, the front console port stops accepting keystrokes.** It still shows output. Close SOL to get the front port back.
- **Leave ipmitool's SOL** by pressing Enter, then `~.`. If that doesn't work, run `ipmitool sol deactivate` from a second shell.
- **Speed:** SOL is set to 115.2 kbps to match the baseline console speed. Commands are in the ipmitool guide.

### Virtual media

The BMC can present an ISO or disk image to the host as a USB CD-ROM or hard disk. It shows in setup as `AMI Virtual CDROM0` / `AMI Virtual HDisk0`. Use it for OS installs with no USB stick in the box.

- **Not yet tested on this box.** The web UI's Image Redirection mounts an image from a network share set up under Settings → Media Redirection. The usual browser-based way to mount a local ISO lives in the KVM console, which this box can't show because it has no video. Treat virtual media as unproven until it's been tried.
- **The proven way to boot an installer** is a USB stick in the front USB-A port, chosen with Save & Exit → Boot Override in setup.

## BIOS setup reference, part 1: Main and Advanced

The setup utility is AMI Aptio, with seven top-level tabs: Main, Advanced, IntelRCSetup, Server Mgmt, Security, Boot, Event Logs, plus Save & Exit. It's driven entirely over serial.

**Keys:**

- Arrow keys move.
- Enter opens a submenu or option list.
- `+`/`-` change a value.
- Esc goes back.
- F2 restores previous values, F3 loads optimised defaults, F4 saves and exits. F-keys need PuTTY's VT100+ function-key mode.

**How to read the tables in parts 1–3.**

- **Factory** is what the reference unit shipped with.
- **Baseline** is what every unit should be set to. **Bold** marks a change from factory.
- **What it does / why** draws on the BIOS's own help text, plus how it matters for this box.
- Options not listed were read and are left at factory.

### Main

| Setting | Factory | Baseline | What it does / why |
| --- | --- | --- | --- |
| BIOS Information | Core 5.14, project 0ACJZ 0.11 x64 x0.45V, Access Level Administrator | n/a | Read-only. "Administrator" access means no setup password is set |
| Total Memory | 24576 MB | n/a | Read-only; a quick check after any RAM change |
| System Language | English | English | Only option |
| System Date / Time | A default date (clock never set) | **Current UTC** | The real-time clock. Keep it on UTC: the BIOS hands this clock to the BMC as UTC at boot, and FreeBSD and Linux both expect a UTC hardware clock |

### Advanced → Trusted Computing

The STMicro TPM 2.0 (firmware 73.4) is detected and enabled.

| Setting | Factory | Baseline | What it does / why |
| --- | --- | --- | --- |
| Security Device Support | Enable | Enable | Exposes the TPM to the OS. Disabling it hides the TPM and its EFI protocol |
| SHA-1 PCR Bank / SHA256 PCR Bank | Enabled / Enabled | Enabled / Enabled | Hash banks used for measured boot. SHA-1 can be turned off once the OS is confirmed to use SHA-256 only |
| Pending operation | None | **TPM Clear, once per unit** | Schedules a TPM operation for the next reboot. A clear wipes any keys the previous owner's software stored. Run it once when a unit is first commissioned, then it reverts to None |
| Platform / Storage / Endorsement Hierarchy | Enabled | Enabled | TPM key hierarchies; leave on |
| TPM2.0 UEFI Spec Version | TCG\_2 | TCG\_2 | Modern TCG2 event-log protocol |
| Physical Presence Spec Version | 1.3 | 1.3 | How the OS asks the firmware to change TPM state |
| TPM 2.0 Interface Type / Device Select | TIS / Auto | TIS / Auto | The TPM sits on the LPC/SPI bus using the TIS interface |

**Clearing the TPM (once per unit).**

- **Why:** the TPM may still hold keys or ownership set up by the previous owner's software. A clear wipes them and hands a blank TPM to the new OS. It doesn't disable the TPM or change its PCR banks.
- **How:** Advanced → Trusted Computing → Pending operation → **TPM Clear**, then Save Changes and Reset. The BIOS help warns that the box reboots an extra time to apply it.
- **Confirmation prompt:** the BIOS may stop on the console and ask you to confirm the clear. Read the prompt and press the key it names. F-keys need PuTTY's VT100+ function-key mode, and the prompt works over SOL too. This hasn't been seen on the reference unit yet, so note what appears.
- **Check:** back in setup, Pending operation reads None again and the TPM is still listed as present. In Linux, `/dev/tpm0` still exists.

### Advanced → ACPI Settings

| Setting | Factory | Baseline | What it does / why |
| --- | --- | --- | --- |
| Enable ACPI Auto Configuration | Disabled | Disabled | Lets the BIOS pick ACPI settings itself. Not needed |
| Enable Hibernation | Disabled | Disabled | S4 hibernation; meaningless for an appliance |
| Lock Legacy Resources | Disabled | Disabled | Stops the OS reassigning legacy I/O resources |

### Advanced → Serial Port Console Redirection

COM0 is the front RJ45 console, and SOL rides on the same port. This is the only console the box has.

| Setting | Factory | Baseline | What it does / why |
| --- | --- | --- | --- |
| COM0 Console Redirection | Enabled | Enabled | Sends the setup screens and POST output to serial. Turning it off leaves the box with no console at all |
| Terminal Type | VT100+ | VT100+ | VT100 with colour and function keys. Match PuTTY's keyboard setting |
| Bits per second | 9600 | **115200** | The BIOS console speed. 115200 matches GRUB, Linux and the SOL setting, so one terminal session covers the whole boot, and screens redraw about 12 times faster |
| Data Bits / Parity / Stop Bits / Flow Control | 8 / None / 1 / None | Same | Standard 8N1, no flow control |
| VT-UTF8 Combo Key Support | Enabled | Enabled | Accepts UTF-8 key sequences |
| Recorder Mode / Resolution 100x31 | Disabled / Disabled | Same | Text-capture and wide-screen options; not needed |
| Putty KeyPad | VT100 | VT100 | How keypad keys are interpreted |
| Legacy Console Redirection: Redirection COM Port | COM0 | COM0 | Where legacy boot loaders and option ROMs print |
| Legacy Console Redirection: Resolution / Redirect After POST | 80x24 / Always Enable | Same | Keeps legacy-mode output on serial after POST |

### Advanced → PCI Subsystem Settings

| Setting | Factory | Baseline | What it does / why |
| --- | --- | --- | --- |
| PCI Latency Timer / PCI-X Latency Timer | 32 / 64 bus clocks | Same | Conventional-PCI settings; nothing here uses them |
| VGA Palette Snoop | Disabled | Disabled | Legacy VGA feature; there's no VGA |
| PERR# / SERR# Generation | Disabled | Disabled | Legacy PCI error signalling. PCIe errors are handled by AER in IntelRCSetup |
| SR-IOV Support | Enabled | Enabled | Lets the I350, X552 and QAT expose virtual functions to VMs. Keep it on for Proxmox |
| BME DMA Mitigation | Disabled | Disabled (hardening option: Enabled) | Keeps bridges from mastering DMA until SMM is locked, which narrows boot-time DMA attacks. Test boot and NICs if you enable it |
| PCI Express Settings: Relaxed Ordering / Extended Tag / No Snoop | Enabled / Disabled / Enabled | Same | Device-level PCIe tuning; defaults suit the NICs |
| PCI Express Settings: Maximum Payload / Maximum Read Request | Auto / Auto | Same | Negotiated per device |
| PCI Express Settings: ASPM Support | Disabled | Disabled | Link power saving. The BIOS warns it can break devices, and it adds latency on NIC links |
| PCI Express Settings: Link Training Retry / Timeout | 5 / 1000 µs | Same | How hard the BIOS tries to bring a link up |
| PCI Express Settings: Unpopulated Links | Keep Link ON | Keep Link ON (efficiency option: Disable Link) | Powers down empty links. Saves a little power, but harmless to leave on |
| PCI Express GEN 2 Settings | Completion Timeout Default; ARI, AtomicOp, IDO, LTR, TLP-prefix blocking all Disabled; Target Link Speed Auto; HW autonomous width/speed Enabled | Same | Advanced link features; nothing on this board needs them |
| PCI Hot-Plug Settings | BIOS Hot-Plug Support Enabled; padding 4 K I/O, 16 M MMIO, 16 M prefetchable | Same | Resource padding for hot-plug, which this box doesn't use |

### Advanced → USB Configuration

The setup shows 1 EHCI and 1 xHCI controller. The "2 drives, 2 hubs" it reports are the BMC's virtual CD and hard disk.

| Setting | Factory | Baseline | What it does / why |
| --- | --- | --- | --- |
| Legacy USB Support | Enabled | Enabled | USB keyboard and boot support before an OS loads; needed to boot installers from USB |
| XHCI Hand-off / EHCI Hand-off | Enabled / Disabled | Same | Passes USB controller ownership to the OS |
| USB Mass Storage Driver Support | Enabled | Enabled | Needed to boot from a USB stick or the BMC's virtual media |
| Port 60/64 Emulation | Enabled | Enabled | Emulates a PS/2 keyboard for legacy software |
| USB transfer / device reset time-out, power-up delay | 20 s / 20 s / Auto | Same | Tolerances for slow devices |
| AMI Virtual CDROM0 / HDisk0 | Auto | Auto | Emulation type for the BMC's virtual media |

### Advanced → Network Stack Configuration

| Setting | Factory | Baseline | What it does / why |
| --- | --- | --- | --- |
| Network Stack | Disabled | Disabled | UEFI PXE and HTTP boot. Leave it off unless you deliberately network-boot: less attack surface, faster boot |

### Advanced → CSM Configuration

CSM is the legacy-BIOS compatibility layer. The factory OS boots in legacy mode, so it's on.

| Setting | Factory | Baseline | Target after OS planning | What it does / why |
| --- | --- | --- | --- | --- |
| CSM Support | Enabled | Enabled | **Disabled** | Legacy boot support. Secure Boot needs it off |
| Boot option filter | Legacy only | **UEFI and Legacy** | UEFI only | Which boot entries are offered. "UEFI and Legacy" lets a UEFI installer boot while the old OS still works |
| GateA20 Active / INT19 Trap Response / HDD Connection Order | Upon Request / Immediate / Adjust | Same | n/a | Legacy-boot behaviours |
| Option ROM execution: Network | Legacy | Legacy | Do not launch | Runs the Intel boot agent on each I350 port (the `IBA GE Slot 07xx` boot entries). Only needed for PXE; skipping it saves boot time |
| Option ROM execution: Storage / Video / Other PCI | Do not launch | Same | Same | No add-in controllers fitted |

### Advanced → NVMe, iSCSI, TLS Auth, RAM Disk

These are UEFI services nothing here uses. NVMe Configuration reads "No NVMe Device Found". iSCSI Configuration (initiator name and attempts) and TLS Auth Configuration (CA and client certificates for HTTPS boot) are empty. RAM Disk Configuration creates UEFI RAM disks. Leave them all untouched.

## BIOS setup reference, part 2: IntelRCSetup

IntelRCSetup exposes Intel's reference-code settings for the Xeon D: CPU, power management, memory, the integrated I/O (IIO), the chipset (PCH), the Management Engine and error handling. Setup prints a warning on entry, and it's deserved: most of these options are silicon tuning that should stay at factory. Every baseline change in this tab is in the first two tables.

### Processor Configuration

Reported: socket 0, CPUID 00050665, 2.300 GHz, max ratio 17h, min ratio 08h, microcode 0E00000C, L1 512 KB / L2 2 MB / L3 12 MB.

| Setting | Factory | Baseline | What it does / why |
| --- | --- | --- | --- |
| Hyper-Threading \[ALL\] | Disable | **Enable** | Gives 16 threads instead of 8. Riverbed turned it off for its data-plane software. A firewall or hypervisor gains throughput from it. The cost is that MDS-class leaks become possible between sibling threads, which is acceptable on a single-tenant box |
| Monitor/Mwait | Enable | Enable | Lets the OS idle cores efficiently; needed for deep C-states |
| Execute Disable Bit | Enable | Enable | NX memory protection; never disable |
| VMX | Enable | Enable | VT-x virtualisation, needed for Proxmox |
| Enable SMX / Enable Intel TXT Support | Disable / Disable | Same | Trusted Execution Technology. Unused; TXT also needs "EV DFX Features" disabled |
| AES-NI | Enable | Enable | Hardware AES. This is what makes IPsec and TLS fast, so keep it on |
| X2APIC | Disable | Disable | Extended interrupt controller mode. Not needed with 16 threads; Linux notes the BIOS "opt-out" and runs xAPIC with interrupt remapping |
| MSR Lock Control / Lock Chipset | Enable / Enable | Same | Locks CPU and chipset configuration registers after POST. A security measure: leave on |
| PPIN Control | Unlock/Enable | Same | Exposes the CPU's unique inventory number to software |
| DEBUG INTERFACE | Disable | Disable | CPU debug features; must stay off |
| Hardware / Adjacent / DCU Streamer / DCU IP prefetchers | Enable | Enable | Cache prefetchers; good for general workloads |
| DCU Mode / Direct Cache Access / DCA Prefetch Delay | 32KB 8-way / Auto / 32 | Same | L1 cache mode and NIC-to-cache DMA tuning |
| Down Stream PECI / SMM Save State / Targeted SMI | Disable | Same | Platform management internals |
| Cores Enabled (Socket 0) | 0 (all 8) | 0 | Number of cores to enable; 0 means all |

### Advanced Power Management Configuration

Riverbed ran the CPU flat out: no P-states, no C-states, Package C0/C1 only. The baseline lets it clock down and sleep when idle. The reference unit measured 48 W at idle with these settings. Each change below is safe for a firewall; see Efficiency and performance for the latency trade-off.

| Setting | Factory | Baseline | What it does / why |
| --- | --- | --- | --- |
| EIST (P-states) | Disable | **Enable** | Lets the OS vary CPU frequency with load. Disabled pins every core at 2.3 GHz. Also required before Turbo and the RAPL limits can be changed |
| CPU P State Control → Turbo Mode | Enable in the first BIOS walk, then Disable | **Enable** | Allows up to 2.7 GHz when power and thermal headroom allow. It read Disable after EIST was changed and had to be set again. Verify in the OS: `/sys/devices/system/cpu/intel_pstate/no_turbo` = 0 |
| CPU C State Control → CPU C State | Disable | **Enable** | Allows idle cores to enter sleep states |
| → Package C State limit | C0/C1 state | **C6 (non-retention)** | Deepest state the whole package may enter. This is where most of the idle power saving comes from |
| → CPU C6 report | Disable | **Enable** | Tells the OS that C6 exists (BIOS help: "recommended to be enabled") |
| → CPU C3 report | Disable | Disable | BIOS help: "recommended to be disabled" |
| → Enhanced Halt State (C1E) | Disable | **Enable** | Drops voltage and frequency in C1 |
| → OS ACPI Cx / C2C3TT | ACPI C2 / 0 | Same | How C6 is presented to the OS; transition timer on auto |
| CPU Advanced PM Tuning → Energy Perf BIAS → Energy Performance BIAS setting | Performance | **Balanced Performance** | A hint to the CPU's power controller. Balanced Performance keeps responsiveness while saving power |
| → Energy Performance Tuning | Disable | Disable | Disabled means the BIOS value above applies rather than the OS's |
| → Power/Performance Switch / Workload Configuration | Enable / UMA | Same | Dynamic EPB switching; workload profile |
| → Averaging Time Window / P0 TotalTimeThreshold (low/high) | 23 / 35 / 58 | Same | Internal heuristics for the switch above |
| CPU P State Control → P State Domain / P-state coordination | ALL / HW\_ALL | Same | Hardware coordination of frequency across cores (BIOS recommends HW\_ALL) |
| → SINGLE\_PCTL / SPD / PL2\_SAFETY\_NET\_ENABLE | no / Disable / Enable | Same | Fine-grained power-control MSR bits |
| → Energy efficient P-state | Enable | Enable | Lets the CPU trim frequency when it won't hurt performance |
| → Boot performance mode | Max Performance | Same | P-state used until the OS takes over |
| → XE Ratio Limit → Overclocking Lock | Enable | Enable | Locks turbo ratios against change |
| LOT26 Enable / UFS / CPU PM Tuning / IOTG Setting / Uncore CLR Freq OVRD / Config TDP | Enable / Enabled / Auto / Disable / Auto / Disable | Same | LOT26 only matters on desktop parts. UFS is uncore frequency scaling. The rest are power-tuning overrides |
| CPU HWPM State Control → Enable CPU HWPM / Autonomous | Disable / Disable | Same | Hardware-managed P-states. Off keeps frequency control in the OS (intel\_pstate or FreeBSD's est/hwpstate), which is the better-supported path |
| CPU T State Control → ACPI T-States | Disable | Disable | OS-driven clock throttling. Unneeded with P-states |
| CPU Thermal Management | Thermal Monitor Enabled; Bi-directional PROCHOT Input-only; PROCHOT response Pn clamping; PCH\_HOT and ME PCH temperature Enabled; CPU-to-PCH throttle Enabled | Same | Overheat protection. Never turn Thermal Monitor off |
| Program PowerCTL\_MSR | PKG C-state latency negotiation Enable; SW LTR ignored; SAPM, PHOLD\_SR, PHOLD\_CST\_PREVENTION Enable; FAST\_Brk\_Int/Snp Disable; Energy Efficient Turbo Disable | Same | Package idle internals. Energy Efficient Turbo off means turbo is never held back to save energy |
| Program PP0\_CURT\_CFG\_CTRL\_MSR / PSI CONFIG | Current override MANUAL but Current Config Disable; PSI thresholds 1/5/20 A; Lock Indication Disable | Same | Voltage-regulator current limits and phase shedding |
| Program CSR\_ENTRY\_CRITERIA / CSR\_SWLTROVRD | Auto / snoop and non-snoop latency overrides off | Same | Package C-state entry rules |
| DRAM RAPL Configuration | Mode 1; BW\_LIMIT\_TF 1; Extended Range Enable | Same | Memory power limiting |
| SOCKET RAPL Config → FAST\_RAPL\_NSTRIKE\_PL2\_DUTY\_CYCLE | 64 | Same | Turbo power-limit duty cycle (needs EIST on to change) |

### Common RefCode, QPI and Reserve Memory

| Setting | Factory | Baseline | Notes |
| --- | --- | --- | --- |
| MMCFG Base / MMIOH Base / MMIO High Size | 2G / 56T / 256G | Same | Address-map layout; only relevant for large add-in cards |
| Isoc Mode / MeSeg Mode / NUMA | Disable / Disable / Enable | Same | NUMA is trivially one node on this single-socket CPU |
| QPI Configuration | Link speed Fast, L0p/L1 Enable, COD Auto, etc. | Same | Socket-interconnect settings. Meaningless on a one-socket SoC ("Number of CPU 1") |
| Reserve Memory Range | Disabled | Disabled | Hides a memory page from the OS; debug aid |

### Memory Configuration

Detected: `Socket0.Ch0.Dimm0 2400MT/s Samsung SRx8 8GB` and `Socket0.Ch1.Dimm0 2400MT/s Samsung SRx4 16GB`.

| Setting | Factory | Baseline | What it does / why |
| --- | --- | --- | --- |
| Memory Frequency / Enforce POR | Auto / Auto | Same | Runs at the CPU's maximum of 2400 MT/s within Intel's supported rules |
| ECC Support / Data Scrambling | Auto / Auto | Same | ECC on; data scrambling improves signal integrity |
| Halt on mem Training Error / MRC Promote Warnings / Promote Warnings | Enabled / Enabled / Enable | Same | A bad DIMM stops POST rather than booting unstable. On this board that shows as a silent, fan-cycling POST loop |
| Memory Type | UDIMMs and RDIMMs | Same | Both ECC types accepted |
| MemTest / MemTestLoops / Attempt Fast Boot / Attempt Fast Cold Boot | Auto / 1 / Auto / Auto | Same | Boot-time memory test and training shortcuts |
| PPR Type / PPR Error Injection | PPR Disabled / Disabled | Same | Post-package repair of DRAM rows |
| Set Throttling Mode | CLTT | CLTT | Closed-loop throttling using the DIMMs' own temperature sensors |
| Memory Power Savings Mode / CK in SR / MDLL Off / Phase Shedding | Auto | Same | DRAM idle power saving |
| Channel / Rank Interleaving / Socket Interleave Below 4GB | Auto / Auto / Disable | Same | Spreads accesses across channels; the mismatched DIMM sizes limit this (see Hardware) |
| Memory RAS → Patrol Scrub / Interval / Demand Scrub | Enable / 24 h / Enable | Same | Finds and fixes correctable errors before they become uncorrectable |
| Memory RAS → Correctable Error Threshold / Device Tagging | 32767 / Disable | Same | Thresholds for sparing and tagging |
| Memory Timings & Voltage Override → DIMM profile | Disabled | Disabled | XMP-style profiles; never on server memory |
| ADR / BDAT / Enhanced Log Parsing / Per Bit Margin | Off | Same | NVDIMM and debug features |

### IIO Configuration (integrated I/O, PCIe)

| Setting | Factory | Baseline | What it does / why |
| --- | --- | --- | --- |
| IOU2 (IIO PCIe Port 1) bifurcation | x8 | x8 | The expansion slot as one x8 link. Splitting it (e.g. x4x4 for a two-drive NVMe carrier) is the lever for future cards; the option list wasn't recorded |
| IOU1 (IIO PCIe Port 3) bifurcation | x4x4x4x4 | Same | Four x4 links: 3A = I350 #1, 3B = I350 #2, 3C and 3D = no device |
| Per-port settings (Port 0/DMI, 1A, 2A–2D, 3A–3D) | Link Speed Auto, De-emphasis −6 dB, L0s off, error overrides off, Gen3 EQ Auto, Hide Port no, ECRC Auto; Port 3A offers Non-Transparent Bridge (Auto) | Same | Link tuning. Live status shows Port 3A/3B linked x4 at Gen2, Port 1A "did not train" (empty slot) |
| PCIe Hot Plug / PCIe ACPI Hot Plug | Disable / Disable | Same | No hot-plug slots |
| IIO PCIe Link on phase / PCIe Train by BIOS | Post chipset init / yes | Same | Link-training order |
| EV DFX Features | Disable | Disable | Silicon debug lock bits; must stay off |
| PCI Express Global Options | TX EQ WA Enable; WA 4167453 Disable; DMI VC1/VCp/VCm Disable; Power down unused ports yes; ASPM (global) L1 Only; Stop & Scream Disable | Same | Global link workarounds |
| IOAT Configuration | Enable IOAT Disable; No Snoop Disable; Disable TPH Enable | Same | The CBDMA copy engines and TLP hints |
| IIO General → TXT DPR memory setting | 3M DPR | Same | DMA-protected range for TXT |
| Intel VT for Directed I/O (VT-d) | Enabled | Enabled | The IOMMU. Needed for PCI passthrough and protects against rogue DMA |
| → ACS Control | Enable | Enable | Isolates devices from each other. This is why every NIC port has its own IOMMU group |
| → Interrupt Remapping | Enable | Enable | Required for safe passthrough |
| → Coherency Support (Non-Isoch / Isoch), VTd Azalea VCp Optimizations | Enable | Same | IOMMU coherency |
| IIO South Complex → "Disable SC GbE", "Disable SC GbE1", "Disable SC CPM" | Enable (all three) | Same | The labels read as disable switches, yet the SoC's 10GbE and QAT (CPM) are present and working. Treat them as enable switches and don't touch them |

### PCH Configuration (chipset)

| Setting | Factory | Baseline | What it does / why |
| --- | --- | --- | --- |
| PCH Devices → PCH M2 Slot 1 / Slot 2 | SATA3 / SATA3 | SATA3 | Selects SATA or PCIe for the M.2 sockets. PCIe is how a CX580 owner got NVMe working (see Known issues) |
| → PCH state after G3 | S5 | S5 | Chipset state after power loss. In practice the BMC's Power Control Policy decides whether the host starts |
| → Board Capability / DeepSx Power Policies / GP27 Wake | DeepSx / Disabled / Disabled | Same | Deep-sleep standby modes |
| → High Precision Timer / Boot Time with HPET | Disabled / Disabled | Same | Linux still finds an HPET through ACPI |
| → SMBUS Device / Serial IRQ Mode / PCH CRID / External SSC / PCH Display | Enabled / Quiet / Disabled / Disabled / Enabled | Same | Chipset basics |
| PCI Express Configuration (PCH root ports 2–8) | Ports enabled, L1 substates on, error reporting off, PCIe Speed Auto, MSI on; PCIe Clock Gating Enabled; function swapping Enabled | Same | No device sits on these today; they're the likely path for M.2 NVMe |
| PCH SATA → SATA Controller / Configure SATA as | Enabled / AHCI | Same | All six ports in AHCI mode; there's no RAID mode |
| → SATA AHCI LPM / Aggressive Link Power Mgmt | Enabled / Enabled | Same | Link power saving on idle drives |
| → Per port (0–5): Port / Hot Plug / eSATA / Mechanical Presence / Spin Up / Device Type | Enabled; hot-plug on the rear bays; eSATA off; HDD or SSD as fitted | Same | Port 2 DevSlp Disabled ("board rework needed") |
| → SATA HDD Unlock / SATA LED locate | Enabled / Enabled | Same | Lets the OS unlock ATA-password drives |
| USB (PCH) → xHCI Mode / Trunk Clock Gating / XHCI Idle L1 / Per-Port Disable Control | Auto / Enabled / Enabled / Disabled | Same (hardening option: disable unused USB ports) |  |
| Security Configuration → RTC Lock / BIOS Lock / Host Flash Lock-Down | Enabled / Enabled / Enabled | Same | Flash write protection. This is why no OS tool can flash the BIOS |
| → GPIO Lockdown / Gbe Flash Lock-Down | Disabled / Disabled | Same | Leave GPIO Lockdown off: board functions such as the relays may depend on GPIO changes |
| Networking → PCH Internal LAN / Wake on LAN / PXE ROM / EFI Network | Enabled / Disabled / Disabled / Disabled | Same | The chipset's own GbE isn't wired out ("LAN PCIe Port used: None") |
| Platform Thermal → PCH Thermal Device / Thermal Lock-Down | Disabled / Enabled | Same |  |

### Miscellaneous, Server ME and Runtime Error Logging

| Setting | Factory | Baseline | What it does / why |
| --- | --- | --- | --- |
| Misc → PCIe Max Read Request / Extended Tag / Latency Tolerance | 4096 B / Enable / Enable | Same | Global PCIe tuning |
| Misc → BIOS Guard | Disabled | Disabled | Intel's flash-update protection; not provisioned here |
| Misc → Serial Debug Message Level / Trace / Training Messages | Disable / Disabled / Disabled | Same | Turning these on floods the serial console with reference-code debug |
| Misc → Active Video / Target VGA | Offboard Device / CPU 0 | Same | There's no video device either way |
| Server ME → General | SPS 3.0.3 (build 59) operational and recovery images, "No Error"; features SiEn+NM+PECIProxy+ICC | n/a | Read-only. The ME runs Server Platform Services (power and thermal management), not the consumer ME |
| Server ME → ICC clock enables / spread spectrum, NM configuration, ME init timeout | Defaults | Same | Clock generator and Node Manager settings. Don't touch |
| Runtime Error Logging → System Errors / IIO / PCH / PCI-Ex error enable | Enable / yes / yes / yes | Same | Hardware errors are logged to the BMC event log |
| → Memory corrected Error | Disable | Disable (observability option: Enable) | Logs corrected ECC events. Worth enabling on a production unit to see a DIMM degrading before it fails |
| → S/W Error Injection Support | Disable | Disable | Must stay off: enabling unlocks an MSR for error injection |
| → WHEA Support / System Poison / Cloaking / Clear McBankErrors | Disable | Same | Windows error architecture and poison features |
| → PCIe Corrected / Uncorrected / Fatal error enable; SERR/PERR propagation | Enable / Enable / Enable; no / no | Same |  |

## BIOS setup reference, part 3: Server Mgmt, Security, Boot, Save & Exit, Event Logs

### Server Mgmt

This tab is the BIOS's view of the BMC. Read-only lines report Self Test PASSED, Device ID 32, revision 1, firmware 0.53, IPMI 2.0, and interfaces KCS and USB.

| Setting | Factory | Baseline | What it does / why |
| --- | --- | --- | --- |
| BMC Support | Enabled | Enabled | The BIOS-to-BMC link (KCS). Needed for SEL logging, the FRB-2 timer and BMC settings from setup |
| Wait For BMC | Disabled | Disabled | Makes POST wait for the BMC, which takes about 30 s to start after AC power. Only useful if the BIOS reports BMC errors after a power cut |
| FRB-2 Timer / timeout / policy | Enabled / 6 min / Do Nothing | Same (resilience option: policy Reset) | A POST watchdog run by the BMC. With Do Nothing a POST hang is only logged. Reset makes an unattended edge box recover by itself |
| OS Watchdog Timer / timeout / policy | Disabled / 10 min / Reset | **Disabled** | Arms the BMC watchdog at OS hand-off. If the OS never services it, the box resets every 10 minutes. Arm the watchdog from the OS instead (see OS notes) |
| Power Control Policy | Power Restore | Power Restore (spares: Do Not PowerUp) | What happens when AC returns: Do Not PowerUp, Last Power State, Power Restore (always on), or No Change. A firewall should come back by itself after an outage. A spare on the shelf is better set to Do Not PowerUp: it then sits in standby at about 12 W instead of idling at about 48 W |
| Latch-Relay Mode | 1 | **1 (verify)** | Bypass-relay behaviour on ports 3–6 (see Bypass relays). Recheck after any defaults load |
| BMC Warm Reset | Action | n/a | Restarts the BMC only; the host keeps running |
| System Event Log → SEL Components | Enabled | Enabled | Lets the BIOS log POST errors to the BMC event log |
| → Erase SEL / When SEL is Full | No / Do Nothing | Same | Clear the log with ipmitool at commissioning rather than here |
| → Log EFI Status Codes | Error code | Same | Logs firmware error codes (not progress codes) to the SEL |
| → View System Event Log | n/a | n/a | Read-only view: 192 entries from the previous owner on the reference unit |
| Bmc self test log → Erase Log / When log is full | Yes, on every reset / Clear Log | Same | The BMC self-test history; 0 of 20 used |
| BMC network configuration → Configuration Address | Unspecified | Unspecified | Unspecified means "the BIOS leaves BMC networking alone". Static or DHCP here makes the BIOS rewrite it at every boot. Manage BMC networking from the BMC or ipmitool and keep this Unspecified |
| → Station IP / mask / MAC / router | DHCP on the factory unit | `<BMC_IP>` set from the BMC | Read-only current values. The quickest way to find an unknown BMC's address |
| → BMC Ext. Network | Enabled | Enabled | Connects the BMC to the shared front port over NC-SI. Disabled cuts the BMC off the network entirely |
| → BMC Ext. Network port | Port1 | Port1 (option: Port2) | Which front port the BMC shares: PRI or AUX. Moving it to AUX frees PRI for the host |
| → IPV6 Support | Enabled (DHCPv6/SLAAC) | **Disabled** | Turns off the BMC's IPv6, so it can't pick up an address you didn't plan for |
| BMC User Settings → Add / Delete / Change User Settings | n/a | n/a | Manages BMC users from setup. **This is the recovery path for a lost BMC admin password** (needs console access) |

### Security

| Setting | Factory | Baseline | What it does / why |
| --- | --- | --- | --- |
| Administrator Password | Not set | **Set it and record it in the password manager** | Protects setup only. Matters because anyone with BMC access can reach setup over SOL. A lost password needs a CMOS clear, and the clear jumper isn't identified, so record it |
| User Password | Not set | Not set | A power-on password. It would stop unattended boots |
| HDD Security Configuration (P0–P4) | No passwords | None | ATA drive passwords. Use OS-level encryption instead |
| Secure Boot | Disabled; System Mode Setup; "Not Active" | Disabled until a UEFI OS is in place | See the Secure Boot steps below |
| Secure Boot Mode | Custom | Custom | Custom allows key management from setup |
| Key Management → Vendor Keys / Factory Key Provision | Valid / Disabled | Same | Factory keys exist in firmware but none are enrolled: PK, KEK, db, dbx, dbt and OsRecovery all show "No Keys" |
| Key Management actions | n/a | n/a | Restore Factory Keys; Reset To Setup Mode; Enroll Efi Image (adds a binary's hash to db); Export Secure Boot variables; Remove 'UEFI CA' from DB (breaks Linux shims); Restore DB defaults. Each variable has Details, Export, Update, Append and Delete, loading EFI\_SIGNATURE\_LIST, DER X.509, RSA-2048 or PE files from a FAT USB stick |

**Setting the administrator password.**

- **How:** Security → Administrator Password → Enter. Type the password, press Enter, then type it again. Setup accepts 3 to 20 characters. Then Save Changes and Reset.
- **What changes:** setup asks for the password on entry, from the front console and over SOL alike. Booting isn't affected: setup's help confirms that with only the administrator password set, it guards setup alone.
- **Why:** anyone with BMC access can reach setup over SOL and change any setting, including Latch-Relay Mode and Secure Boot. The password closes that path.
- **Store it first:** put it in the password manager before saving. There's no proven way to recover a lost one on this board: the CMOS-clear jumper isn't identified, and Aptio keeps setup settings in flash, so a battery pull may not clear it.
- **Don't set the User Password:** it would stop every boot at a prompt and break unattended restarts.

**Secure Boot steps (for later, after a UEFI install).**

1. Restore Factory Keys.
2. Open Key Management → Platform Key → Details. If the subject contains "DO NOT TRUST" or "DO NOT SHIP", the factory PK is AMI's public test key (the [PKfail](https://www.bleepingcomputer.com/news/security/pkfail-secure-boot-bypass-lets-attackers-install-uefi-malware/) issue) and must be replaced with your own PK.
3. Append Microsoft's 2023 certificates: "Microsoft UEFI CA 2023" to db and "Microsoft Corporation KEK 2K CA 2023" to KEK. The older 2011 certificates have expired.
4. Enable Secure Boot, save and test-boot.

### Boot

| Setting | Factory | Baseline | What it does / why |
| --- | --- | --- | --- |
| Setup Prompt Timeout | 1 s | **5 s** | How long "Press \<DEL> or \<ESC>" waits. 1 s is too short to catch reliably over serial |
| Bootup NumLock State | On | On |  |
| Quiet Boot | Disabled | Disabled | Keeps POST output on the console; essential for diagnosis |
| Boot mode select | DUAL | DUAL now, **UEFI** after OS planning | LEGACY, UEFI or DUAL. Must be UEFI for Secure Boot |
| FIXED BOOT ORDER Priorities (#1–#12) | Hard Disk0 (P0), Disk1 (P1), Disk2 (P2), Disk3 (P3), Disk4 (P4), rest Disabled | OS disk first after install; network entries disabled | Boot order by class. Per-class "BBS Priorities" submenus order the individual drives, network boot agents (`IBA GE Slot 0700–0703`) and CD/DVD |
| Delete Boot Option | n/a | n/a | Removes stale UEFI boot entries |

**Network boot entries.** In FIXED BOOT ORDER, set any slot holding a network entry (`IBA GE Slot …`) to Disabled. Once CSM is off (below), the Intel boot agents no longer load. With Network Stack disabled, no UEFI network entries appear either, so there's usually nothing left to disable.

**Final pre-install pass: switching to UEFI-only.**

- **When:** last, just before booting the installer, and after the drive wipe (Security hardening → Wiping the drives). The factory Versa install boots only in legacy mode, so after this the root shell is gone.
- **Why:** Secure Boot needs it. It removes the legacy boot path and the I350 option ROMs, which cuts attack surface and boot time. OPNsense and Proxmox both install and boot in UEFI mode.
- **How:**
  1. Advanced → CSM Configuration → CSM Support → **Disabled**.
  2. Boot → Boot mode select → **UEFI**.
  3. If one option greys out the other, set the one that's available, Save Changes and Reset, then re-enter setup and set the second.
  4. Save & Exit → Save as User Defaults, then Save Changes and Reset.
- **What to expect:** POST codes and setup still appear on the console at 115200, because console redirection is part of the firmware. The `IBA GE` entries disappear. Boot Override lists only UEFI-bootable media; the OPNsense serial image and the Proxmox ISO both qualify.
- **If nothing boots afterwards:** expected until an OS is installed. Otherwise the installer media isn't UEFI-bootable. Enter setup with Esc and use Boot Override.

### Save & Exit

| Action | Use it for |
| --- | --- |
| Save Changes and Reset | Normal way out after changes |
| Discard Changes and Exit / Reset | Leave without changing anything. Use this whenever you only came to look |
| Save as User Defaults | **Run it once the baseline is set**, so the baseline can be reloaded |
| Restore User Defaults | Reload the saved baseline |
| Restore Defaults | Loads the vendor defaults. **Afterwards check console speed, Latch-Relay Mode, HT and the power settings**: the defaults may not match the factory or baseline values |
| Boot Override | One-time boot from a listed device: P0–P4, the PXE agent (`IBA GE Slot 0700 v1586`), or the BMC's `AMI Virtual CDROM0`. The easiest way to boot an installer |

### Event Logs

| Setting | Factory | Baseline | What it does / why |
| --- | --- | --- | --- |
| Smbios Event Log | Enabled | Enabled | The BIOS's own event log, separate from the BMC SEL |
| Erase Event Log / When Log is Full | No / Do Nothing | Erase once at commissioning (optional) | Holds the previous owner's entries (log area resets and system boots) |
| Log System Boot Event / MECI / METW | Enabled / 1 / 60 | Same | Boot logging and the error-counting window |
| Log OEM Codes / Convert OEM Codes | Enabled / Disabled | Same |  |
| View Smbios Event Log | n/a | n/a | Read-only list |

**Erasing the SMBIOS event log (once, at commissioning).**

- **How:** Event Logs → Erase Event Log. Choose the option that erases once at the next reset, not the one that erases on every reset, then Save Changes and Reset.
- **Check:** View Smbios Event Log shows only new entries, and Erase Event Log should read No again.
- **Why:** the previous owner's entries are noise. A clean log makes a new fault stand out.
- **The BMC's event log (SEL) is separate:** clear it with `ipmitool sel clear`.

## BMC reference and configuration

The BMC is a separate small computer on the board: an ASPEED AST2520 running Riverbed-branded AMI MegaRAC SP-X 0.53.1108131520. It runs whenever AC power is connected, sees the host's console, power and sensors, and shares a front network port. Command-line use is covered in the ipmitool guide.

### Interfaces

| Interface | Path | Used for |
| --- | --- | --- |
| Web UI | HTTPS 443 on the shared port | Everything interactive |
| IPMI over LAN (RMCP+) | UDP 623 on the shared port | ipmitool from another machine |
| KCS | Inside the box (`/dev/ipmi0` on Linux, `ipmi(4)` on FreeBSD) | ipmitool from the host OS with no network or password |
| USB | Virtual hub on the host's USB bus | Virtual CD/hard disk; the BIOS also talks to the BMC this way |
| SSH | TCP 22 on the shared port | The BMC's own Linux shell (sysadmin) |

### Network

The BMC has no dedicated port. It shares front port 1 (PRI) with the host's first I350 port over NC-SI.

| Setting | Reference unit | Where to change it |
| --- | --- | --- |
| Shared port | Port 1 (PRI). Port 2 (AUX) also offered | BIOS: Server Mgmt → BMC network configuration → BMC Ext. Network port. Web: Settings → Network → Sideband Interface (NC-SI) |
| NC-SI mode | Manual switch, package 0, channel 0. Auto-failover between the two ports is available | Web: NC-SI page |
| IPv4 | Static `<BMC_IP>`/24, no gateway | Web: Network IP Settings, or `ipmitool lan set 1 …` |
| IPv6 | Disabled (factory: on, with SLAAC/DHCPv6) | Web, or BIOS |
| VLAN | Off (802.1Q tagging available) | Web: Network IP Settings |
| Hostname / DNS | Hostname auto (`AMI` + MAC). The previous owner's domain, DNS server and DNS registration were cleared | Web: DNS Configuration |
| Link | Autonegotiation, 1000/full | Web: Network Link Configuration |

**Design note.** Port 1 carries both host traffic and BMC traffic. Whatever OS runs on the host, treat port 1 as the management port: put it on the management network, or move the BMC to port 2 and give that port to management.

**Choosing the BMC's port.**

- **Port 1 (default):** fine if the host's port 1 will be its management interface anyway. Nothing to change.
- **Port 2:** frees PRI for other host traffic. The rule moves with the BMC: whichever port it shares must sit on the management network, and the host may use that port only for management.
- **How to move it:** in the BIOS, Server Mgmt → BMC network configuration → BMC Ext. Network port → Port2, then Save Changes and Reset. The web UI equivalent is Settings → Network → Sideband Interface (NC-SI). Then move the management cable to port 2.
- **Check:** `ping <BMC_IP>` answers through port 2, and `ipmitool lan print 1` shows the same BMC MAC. The address should carry over; if it doesn't, set it again in-band (Baseline Phase 4).
- **Avoid auto-failover between the ports:** it makes it unpredictable which port the BMC answers on.
- Moving the port hasn't been tested on the reference unit.

### Services

| Service | State | Port | Notes |
| --- | --- | --- | --- |
| web | Active | 443 | Session timeout 1800 s, up to 20 sessions |
| cd-media / hd-media | Active | 443 | Virtual media, one instance each |
| ssh | Active | 22 | Login as sysadmin. Set it inactive unless you use the BMC shell |
| solssh | Inactive | n/a | SOL over SSH; an alternative to ipmitool for the console |
| KVM | n/a | n/a | No graphical console: the host has no VGA |

**Turning off SSH.**

- **Why:** SSH gives a root shell on the BMC through the sysadmin account, whose factory password is public. Normal management doesn't need it: the web UI and IPMI cover everything.
- **How:** Settings → Services → select **ssh** → Modify. Set it to inactive, then Save. The BMC restarts the service and the web session may reload.
- **Check from WSL:** `nc -zv <BMC_IP> 22` should report the connection refused or timing out.
- **Leave these on:** web (443) and IPMI over LAN (623/udp) are the management tools. cd-media and hd-media serve virtual media; turn them off only if you'll never use it.

### Accounts

| Account | Purpose | State after baseline |
| --- | --- | --- |
| ID 1, anonymous (no name), Administrator | AMI default null user | Disabled with `ipmitool user disable 1`. An anonymous login attempt is refused (tested) |
| ID 2, `<BMC_USER>` (`admin`), Administrator | The one real admin | Password changed from factory |
| IDs 3–10 | Empty | n/a |
| sysadmin | The BMC's own Linux account (Maintenance → System Administrator), used for SSH | Password changed. The factory password for this account is widely published |

Users are listed per channel (1, 2 and 8). The UI shows every slot as "Active", which doesn't mean enabled. Test access with ipmitool rather than trusting that label.

**Passwords.**

- **Length:** IPMI 2.0 allows at most 20 characters. Keep BMC passwords to 20 or fewer; otherwise ipmitool may fail to log in even though the web UI accepts the password.
- **Unique per unit,** stored in the password manager under the unit's MFG serial. The RAKP flaw lets anyone on the management network collect a hash of the admin password and crack it offline, so length and randomness matter.
- **Admin (ID 2):** change it in-band with `ipmitool user set password 2`, which prompts for the password, or in Settings → User Management.
- **sysadmin:** Maintenance → System Administrator. Change the password, or untick Enable User Access to disable the login altogether.
- **Check:** log in to the web UI with the new password. From WSL, put the new password in `IPMI_PASSWORD` and run `bmc chassis power status`.

### Other settings

| Area | Reference unit | Notes |
| --- | --- | --- |
| SOL | Enabled, 115.2 kbps (volatile and non-volatile), privilege USER | Must match the BIOS console speed |
| RMCP+ cipher suites | 0, 1, 2, 3, 6, 7, 8, 11, 12, 15, 16, 17; suite 0 (no authentication) is disabled | ipmitool uses suite 17 or 3 |
| IPMI 1.5 auth types | MD2, MD5, password; MD5 enabled | Legacy; always use `-I lanplus` |
| Platform Event Filters / alerting | LAN alerting enabled, SNMP community `AMI`, no destinations | Nothing is sent. Configure SMTP or SNMP destinations only if you want alerts |
| SEL policy | 65,535-byte log; 205 entries from the previous owner on the reference unit | Clear at commissioning (ipmitool guide) |
| Remote syslog / audit log | Off | Point at the lab's syslog server once one exists |
| System Firewall | No rules | BMC-side IP and port allow-lists. A cheap hardening step: allow only the management subnet |
| SSL | AMI default self-signed certificate (CN "AMI"), valid for ten years | Replace it with your own certificate (Generate or Upload SSL) |
| Date & Time | Manual offset Etc/GMT; showed correct UTC | Set NTP to a lab time source if available |
| Video Recording → SOL triggers | Off | Can record SOL output on watchdog, power or reset events: useful for catching a crash on screen |
| Media Redirection | Remote media on, KVM single-port app on | Image Redirection mounts ISOs for installs |

**Optional settings, step by step.**

- **Inherited configuration.** On a second-hand unit these pages should be empty or disabled. Anything filled in belongs to the previous owner, so clear it:
  - Settings → External User Services: LDAP/E-Directory, Active Directory and RADIUS.
  - Settings → SMTP Settings: no mail server.
  - Settings → Platform Event Filter: no LAN destinations or alert policies.
  - Settings → Network Settings → DNS Configuration: cleared in the baseline.
- **Time (NTP).** Settings → Date & Time.
  - If the lab has an NTP server, switch to automatic NTP and enter it. Keep the time zone on UTC.
  - Without one, leave it manual: the BIOS sets the BMC clock at boot, which is another reason to keep the BIOS clock on UTC.
  - Why: correct times in the SEL and audit log, and in certificate validity checks.
- **System Firewall.** Worth it only if the management network is shared. Settings → System Firewall has three pages: General Firewall Settings, IP Address Firewall Rules and Port Firewall Rules.
  - The aim is to allow the management subnet and block everything else.
  - Rules can carry a start and end time. Create the block rule first with an end time 30 minutes ahead, so a mistake that locks you out expires by itself.
  - Test web and ipmitool access from the laptop, then recreate the rule without the timeout.
  - Not tested on the reference unit.
- **TLS certificate.** Settings → SSL Settings → Generate SSL Certificate (your own fields and validity), or Upload SSL Certificate (a certificate and key from your own CA). The web server restarts.
  - Why: the AMI default certificate is the same on every MegaRAC box, so it proves nothing about which BMC you're talking to.
- **Remote logging.** Settings → Log Settings → Advanced Log Settings: enable remote syslog to the lab's syslog server, and the audit log.
  - Why: a record of logins and changes kept off the box.
- **SNMP community.** Change it only if PEF alerts are used: `ipmitool lan set 1 snmp <string>`.

### Maintenance pages (look, don't press)

The pages are Backup Configuration, Restore Configuration, Preserve Configuration, Restore Factory Defaults, BMC Recovery (TFTP image `rom.ima`, boot retry 2, recovery retry 3), Firmware Image Location (web upload or TFTP), Firmware Update, HPM Firmware Update and System Administrator.

- **Backup Configuration is worth using:** take a backup once the BMC baseline is done.
- **Don't run any firmware page.** There's no Riverbed image to flash, and a failed BMC flash leaves only the BMC Recovery path.

**Taking a configuration backup.**

- **When:** after the BMC baseline is complete, and again after any later BMC change.
- **How:** Maintenance → Backup Configuration. Tick Check All, which covers groups such as Network & Services, IPMI, NTP, Authentication and SYSLOG, then download the file.
- **Where to keep it:** with the unit's records, named with the unit's MFG serial and the date. Protect it like a credential, because it may include account and password data.
- **Using it:** Restore Configuration loads it back onto the same unit, for example after Restore Factory Defaults. That's untested here. Don't use it to copy settings between units: each unit has its own address and passwords.

### Sensors and FRU at a glance

- **Sensors:** inlet and outlet air temperature; CPU, DIMM 1/2 and PCH temperatures; 15 voltage rails, including both Inphi PHYs' 1.8 V and 0.9 V; Fan1 and Fan2; and per-PSU status, temperature, fan and input watts.
- **When the host is off:** only the BMC rails, inlet and outlet temperatures and PSU readings are live. The rest show as disabled.
- **FRU 0:** chassis, board and product records (codename Snook).
- **FRU 1 and 2:** the two PSUs.

The full sensor list with thresholds is in the ipmitool guide.

### BMC baseline (in order)

1. Give it a static address on the management network (web UI or ipmitool) and keep the BIOS "Configuration Address" at Unspecified.
2. Disable IPv6.
3. Set SOL to 115.2 kbps.
4. Disable user ID 1, then prove an anonymous login fails.
5. Change the admin password and the sysadmin password.
6. Clear any inherited DNS settings and untick Register BMC.
7. Set ssh inactive unless needed.
8. Optional: add System Firewall rules, set NTP, replace the TLS certificate.
9. Clear the SEL, then take a configuration backup.

## Baseline bring-up procedure

This is the sequence that took the reference unit from "as received" to a known, documented, remotely manageable baseline. Run it on every unit, in this order. Allow about two hours per unit once you're familiar with it.

### Phase 0: Prepare (once)

1. **Laptop:**
   - PuTTY with two saved sessions, 9600 and 115200 (settings under Access methods).
   - A USB-to-RJ45 console cable.
   - WSL with `sudo apt install ipmitool`.
2. **USB stick:** FAT32, holding `cx3080-inventory.sh` v3 (Appendix C).
3. **Management network:** an isolated subnet with the laptop on it, cabled to front port 1 (PRI). Any private subnet set aside for management will do (`<MGMT_SUBNET>`).
4. **Rules for the whole procedure:**
   - Keep ports 2–12 unplugged.
   - Don't log in to the factory Versa OS.
   - Don't press unknown buttons or move jumpers.

**Why these rules.**

- **Ports 2–12 unplugged:** until the baseline is done, nothing on the box is trusted. If the factory OS ever booted normally, it would bring up the previous owner's network configuration. Only port 1 is needed, for the BMC.
- **No Versa login:** its configuration, keys and certificates belong to the previous owner. The root shell (Access methods) gives everything needed without it.
- **No unknown buttons or jumpers:** several headers are unidentified (Headers and jumpers), and J23 carries a jumper of unknown purpose.

**Credentials for each unit.** Before starting, create three password-manager entries named after the unit's MFG serial: BMC admin, BMC sysadmin and BIOS administrator. Keep BMC passwords to 20 characters or fewer (BMC reference → Accounts). No password goes in these documents or on a command line.

**USB stick space.** Leave room for a copy of `/opt/versa/firmware` (Firmware and microcode). Its size is unknown until the first unit is checked.

### Phase 1: Inspect

1. Take the lid off. Check both DIMMs are fully latched, the M.2 modules are screwed down and the fan module is seated.
2. Record the case label (serial and MFG number) in the unit register.
3. Refit the lid and drives. One PSU is enough for bring-up.

### Phase 2: First power-on

1. Console at **9600**, logging on. Connect AC and press the power button.
2. Check the healthy signature: loud fans, quiet at about 17 s, amber off on ports 3–6 at about 21 s, one beep at about 37 s, then progress codes and the setup prompt.
3. If there's no console output and the fans keep cycling up and down, power off and reseat the RAM (Known issues).

### Phase 3: BIOS baseline (console at 9600)

1. Enter setup: tap Esc once the progress codes appear after the beep.
2. Make these changes:

| Where | Setting | Set to |
| --- | --- | --- |
| Main | System Date / Time | Current **UTC** |
| Advanced → Serial Port Console Redirection → COM0 → Console Redirection Settings | Bits per second | 115200 |
| Advanced → CSM Configuration | Boot option filter | UEFI and Legacy |
| IntelRCSetup → Processor Configuration | Hyper-Threading \[ALL\] | Enable |
| IntelRCSetup → Advanced Power Management Configuration | EIST (P-states) | Enable |
| … → CPU P State Control | Turbo Mode | Enable (check it after enabling EIST) |
| … → CPU C State Control | CPU C State / Package C State limit / CPU C6 report / C1E | Enable / C6 (non-retention) / Enable / Enable |
| … → CPU Advanced PM Tuning → Energy Perf BIAS | Energy Performance BIAS setting | Balanced Performance |
| Server Mgmt → BMC network configuration | IPV6 Support | Disabled |
| Server Mgmt | Latch-Relay Mode / Power Control Policy / OS Watchdog Timer | Confirm 1 / Power Restore / Disabled |
| Boot | Setup Prompt Timeout | 5 |
| Security | Administrator Password | Set and record (recommended) |
| Advanced → Trusted Computing | Pending operation | TPM Clear (recommended, once) |

3. Save & Exit → **Save as User Defaults**, then **Save Changes and Reset**.
4. Switch PuTTY to **115200** straight away. From now on everything (BIOS, GRUB, Linux, SOL) runs at 115200.

### Phase 4: Root shell, BMC fixes and inventory (115200)

1. At GRUB, press `e`, append `  init=/bin/bash ` to the `linux` line, then Ctrl-X.
2. In the shell:

```
mount -t proc proc /proc; mount -t sysfs sysfs /sys
modprobe ipmi_si; modprobe ipmi_devintf
nproc                                                  # expect 16
cat /sys/devices/system/cpu/intel_pstate/no_turbo      # expect 0
ipmitool sol set non-volatile-bit-rate 115.2 1         # the channel number (1) is required
ipmitool sol set volatile-bit-rate 115.2 1
ipmitool user disable 1                                # the anonymous user
ipmitool user set password 2                           # prompts for the new admin password
ipmitool lan set 1 ipsrc static                        # only if the BMC isn't already set
ipmitool lan set 1 ipaddr <BMC_IP>
ipmitool lan set 1 netmask <NETMASK>
```

3. Insert the USB stick, find it, mount it and run the inventory. The stick is the last `sd` device; `sdf` is usually the BMC's empty virtual disk.

```
ls /dev/sd*
mount /dev/sdg1 /mnt && cd /mnt
bash cx3080-inventory.sh               # writes cx3080-<serial>-<time>.txt
bash cx3080-inventory.sh portmap 180   # move one cable through ports 1→8, ~5 s each
cd /; umount /mnt
echo o > /proc/sysrq-trigger           # power off
```

### Phase 5: BMC web interface (laptop browser)

1. Log in at `https://<BMC_IP>` as `<BMC_USER>`.
2. Maintenance → System Administrator: change the sysadmin password, or untick Enable User Access.
3. Settings → Network Settings → DNS Configuration: clear the inherited domain and DNS servers, untick Register BMC, then Save.
4. Settings → Services → ssh: set inactive unless needed.
5. Read the Sensor and FRU pages and compare them with the reference values (Hardware specification).
6. Maintenance → Backup Configuration: save a copy.

### Phase 6: Prove remote management (laptop, WSL)

Commands are in the ipmitool guide.

1. The anonymous login must fail.
2. `sol activate` shows the console.
3. `chassis power reset` reboots the box while you watch it on SOL.
4. Tap Esc over SOL to reach setup, then leave with Discard Changes and Exit.
5. Clear the SEL once everything works: `ipmitool sel clear`.

### Phase 7: Record

1. Fill in the unit's row in the unit register (Appendix A): serials, MACs, BMC address, firmware versions, drive hours, any deviations.
2. Keep the PuTTY logs and the inventory file with the unit's records.

## Security hardening

The biggest risk on this platform is the BMC, not the firewall OS. It runs old firmware with known critical flaws and has no update path, it shares a front port, and it can power-cycle the box and reach setup. Isolate the management plane first; every other control is secondary.

**Status key:** Done = applied on the reference unit; To do = recommended and not yet applied; Optional = worth it in some deployments; Later = needs the OS install first.

### 1. Management-plane isolation

| Control | Why | How | Status |
| --- | --- | --- | --- |
| BMC only on an isolated management network or VLAN, with no route to the internet or WAN | MegaRAC SP-X of this age is very likely exposed to [CVE-2024-54085](https://www.csoonline.com/article/3848376/critical-vulnerability-in-ami-megarac-bmc-allows-servers-takeover.html), a remote authentication bypass. IPMI 2.0 itself leaks salted password hashes to anyone who asks (RAKP). Neither can be patched here | Cable PRI (or AUX, if the BMC is moved) only to the management switch or VLAN. Optionally tag BMC traffic with its own VLAN ID | To do (lab subnet in use) |
| Never expose 443, 623/udp or 22 on the BMC address beyond the management network | Same | Upstream firewall rules | To do |
| BMC System Firewall allow-list | Defence in depth if the management network is shared | BMC web: Settings → System Firewall: allow only the admin workstation or management subnet | Optional |
| Host OS must never bridge or route port 1 to the WAN | The BMC rides on port 1 | Assign port 1 only to the management role in OPNsense or Proxmox | Later |

### 2. BMC accounts and services

| Control | Why | How | Status |
| --- | --- | --- | --- |
| Disable anonymous user ID 1 and test it | The AMI null user is an administrator | `ipmitool user disable 1`; anonymous login must fail | Done |
| Unique, long admin password per unit | The RAKP hash leak makes short passwords crackable offline | Password manager; `ipmitool user set password 2` | Done (reference unit) |
| Change the sysadmin password, or disable the account | It's the BMC's Linux login, and its factory password is public | Maintenance → System Administrator | Done |
| Turn off BMC SSH | Removes a login service nobody uses | Settings → Services → ssh → inactive | To do |
| Disable BMC IPv6 | Stops an unplanned address on the management LAN | BIOS or web UI | Done |
| Remove inherited configuration (DNS, registration, LDAP/AD/RADIUS, SMTP, alert destinations) | Previous owner's infrastructure details | Check each settings page | Done (DNS cleared; others were empty) |
| Replace the default TLS certificate | The AMI default is shared by every MegaRAC box | Settings → SSL Settings | Optional |
| Change the SNMP community `AMI` if alerting is ever enabled | Default community string | `ipmitool lan set 1 snmp <string>` | Optional |
| Keep RMCP+ cipher suite 0 disabled and always use `-I lanplus` | Suite 0 means no authentication; IPMI 1.5 uses MD5 | Already the factory state | Done |

### 3. Firmware and boot chain

| Control | Why | How | Status |
| --- | --- | --- | --- |
| BIOS Administrator password | Anyone with console or SOL access can otherwise change any setting | Security tab; record the password | To do |
| Keep BIOS Lock, Host Flash Lock-Down and RTC Lock on | Blocks OS-level reflashing of the BIOS | IntelRCSetup → PCH → Security Configuration | Done (factory) |
| Keep debug features off: DEBUG INTERFACE, EV DFX, S/W Error Injection, Serial Debug Messages | Each opens a debug or injection path | Leave at factory | Done (factory) |
| UEFI-only boot, CSM off, network boot off | Removes the legacy boot path and PXE | Advanced → CSM; Boot → Boot mode select | Later |
| Secure Boot with your own PK (check for PKfail) plus Microsoft 2023 certificates | Prevents unsigned boot code. The factory PK may be AMI's public test key | BIOS part 3, Secure Boot steps | Later |
| TPM clear at commissioning | Wipes any keys the previous owner's software stored | Advanced → Trusted Computing → Pending operation | To do |
| Measured boot and TPM-sealed disk keys | Detects boot-chain tampering; protects disks if stolen | OS feature (Proxmox/Linux); optional | Later |
| Current CPU microcode from the OS | The BIOS microcode (0x0E00000C) predates several fixes | OPNsense `os-cpu-microcode-intel` plugin; Proxmox `intel-microcode` package | Later |

### 4. Previous owner's data

| Control | Why | How | Status |
| --- | --- | --- | --- |
| Wipe all five drives before reuse | The Versa disk holds the previous owner's network configuration, keys and certificates | SSDs: `blkdiscard` on the whole device (the Intel and Virtium drives read zeros after TRIM). HDDs: ATA secure erase or a full overwrite. ATA security reads "frozen" after boot, so secure erase needs a hot-plug of the rear-bay drive first | To do (after checking `/opt/versa/firmware` for firmware images) |
| Clear the BMC SEL and the BIOS SMBIOS event log | Removes previous-owner history | `ipmitool sel clear`; Event Logs → Erase | To do |

#### Wiping the drives, step by step

**Before you start.** This can't be undone. Check that:

1. the inventory file and port map are copied off the USB stick;
2. `/opt/versa/firmware` has been checked and, if not empty, copied (Firmware and microcode);
3. every drive's model and serial is in Appendix A.

**Where to run it.** Not from the root shell: the factory Ubuntu runs from P1, and its decade-old tools may lack `blkdiscard`.

- Use a current Linux live system on a USB stick in the front USB-A port, booted with Save & Exit → Boot Override.
- At its boot menu, add `console=ttyS0,115200n8` to the kernel line so that its console comes out of the serial port. The Proxmox installer ISO has serial-console entries built in.
- This step hasn't been run on the reference unit yet; record what works.

**Identify the drives.** Run `lsblk -o NAME,MODEL,SERIAL,SIZE,TRAN` and match each model and serial against Appendix A. The live stick and the BMC's virtual CD and disk also show up as `sd` devices; leave those alone.

| Drive | Method | Why | Time |
| --- | --- | --- | --- |
| Intel D3-S4510 (P2, P3) and Virtium (P4) | `blkdiscard /dev/sdX` | The inventory shows all three report "Deterministic read ZEROs after TRIM", so after a whole-device discard they read back as zeros | Seconds |
| Seagate (P0, P1) | `dd if=/dev/zero of=/dev/sdX bs=1M status=progress` | A full overwrite; spinning disks have no TRIM | About 2–3 hours each |
| Seagate, alternative | ATA enhanced secure erase (below) | Also erases sectors the drive has remapped | About 160 minutes each (the drive's own estimate) |

**ATA secure erase.** Every drive reports "frozen" after boot, which blocks the erase command. Pulling and reinserting a rear-bay drive while the system runs (hot-plug is on for those bays) usually clears it. `wipe` below is a throwaway password that the erase removes:

```
hdparm -I /dev/sdX | grep -i frozen          # must say "not frozen"
hdparm --user-master u --security-set-pass wipe /dev/sdX
hdparm --user-master u --security-erase-enhanced wipe /dev/sdX
```

If the erase is interrupted, the drive stays locked with that password. Unlock it with `hdparm --user-master u --security-disable wipe /dev/sdX`.

**Check each drive.** `cmp -n 104857600 /dev/zero /dev/sdX` prints nothing if the first 100 MB read back as zeros. If an SSD doesn't pass, overwrite it with `dd`.

**Then clear the logs:** the BMC event log (`ipmitool sel clear`), and the BIOS's SMBIOS event log (BIOS reference part 3 → Event Logs).

### 5. Physical

Whoever can touch the box owns it. They can use the console port, the reset pinhole, front USB boot or the internal headers. Keep production units in a locked space if that matters. The BIOS admin password and Secure Boot raise the bar for someone with only casual access.

### 6. Detection

| Control | Why | How | Status |
| --- | --- | --- | --- |
| Send BMC logs to a syslog server | Login and configuration-change history off the box | BMC: Settings → Log Settings → Advanced (remote syslog, audit log) | Optional |
| Watch sensors and the SEL | Fan, PSU and temperature failures are visible early | ipmitool polling or an exporter (ipmitool guide) | Optional |
| Log corrected memory errors | A degrading DIMM shows before it fails | IntelRCSetup → Runtime Error Logging → Memory corrected Error | Optional |

## Efficiency and performance tuning

With the baseline BIOS settings, the reference unit drew 48 W at idle and 12 W in standby, on one PSU. The baseline lets the CPU clock down and sleep when idle while keeping turbo and all 16 threads for bursts. For a home-lab firewall that's the right balance: the deep-sleep wake-up cost is microseconds, far below anything a gigabit WAN link will notice.

### CPU power states

| Knob | Baseline | Effect | Change it when |
| --- | --- | --- | --- |
| EIST (P-states) | On | Frequency follows load (0.8–2.3 GHz) | Never turn off; it also gates Turbo |
| Turbo | On | Up to 2.7 GHz on lightly threaded work. Helps single-stream throughput through the firewall (one big download, one PPPoE session) | Leave on |
| Package C-state limit | C6 (non-retention) | The main idle-power saver. Waking costs on the order of 100 µs | Capping at C1/C1E only matters for latency-critical work. Do it in the OS (Linux `intel_idle.max_cstate=1`, FreeBSD `hw.acpi.cpu.cx_lowest=C1`) rather than in the BIOS |
| C1E | On | Lower voltage in light idle | Same as above |
| Hyper-Threading | On | More throughput across many flows and VMs | Off only if you want MDS isolation between threads |
| Energy Performance Bias | Balanced Performance | Biases the power controller towards responsiveness | Performance for benchmarking |

**The OS has to take part.** On OPNsense, turn on PowerD (System → Settings → Miscellaneous → Power Savings) so FreeBSD steps the clock down. Linux and Proxmox use `intel_pstate` automatically; check `no_turbo` = 0 after any BIOS change.

### Network

| Topic | Recommendation |
| --- | --- |
| Which ports for what | Port 1 is management (the BMC shares it). Ports 3–6 are dead when the box is off: fine for LAN or WAN, but nothing that must survive a power-off. SFP+ 9–12 have the most headroom (10 Gb/s, up to 64 queues) |
| Queues and RSS | Each I350 port has up to 8 queue pairs and each X552 port up to 64. Let the driver use one queue per core (8–16); the default is usually right |
| Offloads | On a pf-based firewall (OPNsense), follow OPNsense's guidance and leave TSO/LRO off. Checksum offload is fine. On Proxmox bridges, defaults are fine |
| Virtualising the firewall | Best performance comes from passing whole ports (or SR-IOV VFs) into the OPNsense VM. Every port has its own IOMMU group, so this works per port. Bridged virtio NICs cost more CPU but are simpler |
| Flow control | Usually off on firewall interfaces |

### Power and hardware choices

| Choice | Effect |
| --- | --- |
| Fewer spinning disks | Each 7,200 rpm 2.5" drive adds a few watts. If the two Seagates aren't needed, pull them and run from the M.2 SSDs |
| Matched DIMM pair | Restores full two-channel interleave (today only 16 of the 24 GB interleave) |
| One PSU or two | Two give redundancy. At \~50 W both PSUs run far below their efficient range, so one PSU is slightly cheaper to run. Not yet measured |
| Unpopulated PCIe links | Advanced → PCI Express Settings → Unpopulated Links → Disable Link saves a little power; the gain is unmeasured |
| Fans | BMC-controlled; no fan curve is exposed. Idle speed is about 3,400 rpm |

### Still to measure

Run these on the first unit that gets its final OS.

- Idle power with the final OS and PowerD/intel\_pstate active.
- Power under a full-throughput test.
- Temperatures and fan speeds under that load.
- Standby draw with two PSUs connected.

## Firmware and microcode

Only one firmware component can be safely updated today: CPU microcode, loaded by the OS at every boot. BIOS and BMC images exist only from Riverbed and aren't public. Flashing anything else risks a soldered-chip brick for little gain.

| Component | Version on the reference unit | Update path | Recommendation |
| --- | --- | --- | --- |
| CPU microcode | 0x0E00000C in BIOS (Ubuntu loaded 0x0E000012) | OS package: OPNsense `os-cpu-microcode-intel`, Proxmox/Debian `intel-microcode`. Carries 0x0E000014 or later | **Do it.** Free, reversible, applied on every boot |
| BIOS (AMI Aptio, project 0ACJZ) | 0.11 x64 x0.45V | Riverbed image only. BIOS Lock and Host Flash Lock-Down block OS-side flashing | Leave it. If a Riverbed image turns up, test on a spare unit first |
| Intel ME (Server Platform Services) | 3.0.3 (build 59), operational and recovery | Bundled with the BIOS image | Leave it |
| BMC (MegaRAC SP-X) | 0.53.1108131520 | Riverbed image only, via Maintenance → Firmware Update or HPM | Leave it and isolate the BMC (Security hardening) |
| I350 NIC NVM | 1.63 | Intel's update tool, which usually refuses cards with an OEM subsystem ID (here 1b2e:1244) | Not needed |
| X552 NIC NVM | 0x800008f7 / 0x800008f8 | Tied to the BIOS image (SoC-integrated) | Not needed |
| Intel D3-S4510 SSDs | XC311132 | Solidigm Storage Tool | Optional; check for a newer release when the OS is built |
| Seagate ST1000NX0423 | TN05 | Seagate tools | Not needed |
| Virtium StorFly | 0202-000 | Vendor only | Not needed |
| PSUs | Revision S3F | n/a | n/a |

### Where Riverbed's images might be

The factory Versa install has a directory `/opt/versa/firmware`. That's the likeliest place Riverbed shipped BIOS and BMC update images.

- **Check it on every unit before its drives are wiped.** The root shell can list it and copy it to the USB stick without logging into Versa.
- **Compare versions across all your units.** If any unit has a newer BIOS or BMC than the reference unit, that's also worth knowing.

**Copying it from the root shell,** with the stick mounted at `/mnt` (Baseline Phase 4):

```
ls -laR /opt/versa/firmware | head -50      # what's there (also in the inventory file)
du -sh /opt/versa/firmware                  # size; FAT32 can't hold a single file over 4 GB
mkdir -p /mnt/firmware-<UNIT_SERIAL>
cp -r /opt/versa/firmware/. /mnt/firmware-<UNIT_SERIAL>/
(cd /opt/versa/firmware && find . -type f -exec md5sum {} +) > /mnt/firmware-<UNIT_SERIAL>.md5
sync
```

- The checksum list lets you compare units without opening every copy: identical lists mean identical images.
- This only reads the factory disk. Don't flash anything you find (see "If you ever flash").
- Then fill in the "`/opt/versa/firmware` checked" row of Appendix A.

### If you ever flash

1. Flash a spare unit, never the production one.
2. Take a BMC configuration backup first and record every BIOS baseline setting. A flash may reset both.
3. Have recovery options in mind:
   - BMC Recovery (TFTP, image `rom.ima`) for the BMC.
   - An SPI programmer on the 2×4 header above the PCIe slot for the BIOS. That header is unconfirmed.
4. After any BIOS flash, re-apply the baseline. Check console speed and Latch-Relay Mode first.

## OS notes

The planned build is OPNsense, either bare metal or as a VM on Proxmox. Either OS runs on this box with in-box drivers for every network port. The things to plan for are the serial-only console, the BMC on port 1, and QAT being unusable under OPNsense.

### Common to both

| Topic | Note |
| --- | --- |
| Install media | No VGA, so use a serial-console installer at 115200. Boot it from the front USB-A port or from BMC virtual media (setup → Save & Exit → Boot Override) |
| Boot mode | Install in **UEFI** mode (Boot option filter "UEFI and Legacy" or UEFI only), so Secure Boot is possible later and CSM can be turned off |
| Install disk | The Intel D3-S4510 M.2 pair (power-loss protection) suits a mirror. The 30 GB Virtium suits a minimal boot disk. The Seagates are optional bulk storage |
| Wipe first | The factory drives hold the previous owner's Versa install and configuration. Wipe them before the install (Security hardening), after checking `/opt/versa/firmware` |
| Port 1 | Shared with the BMC. Give it the management role only |
| Ports 3–6 | Normal NICs while running; dead when powered off |
| Microcode | Install the OS microcode package on day one |

**Port plan worksheet.** Fill in the Role column for each build before the install, and keep it with the unit's records. Proxmox names ports by PCI address instead, for example `enp7s0f0` for port 1; check against the MACs in Appendix A.

| Port | Label | Factory Linux / FreeBSD name | PCI | Constraint | Role |
| --- | --- | --- | --- | --- | --- |
| 1 | PRI | eth0 / igb0 | 07:0.0 | Shared with the BMC by default: management only. Wake-on-LAN capable |  |
| 2 | AUX | eth1 / igb1 | 07:0.1 | Takes on the BMC instead, if it's moved here |  |
| 3 | LAN0\_0 | eth2 / igb2 | 07:0.2 | Dead when the box is off |  |
| 4 | WAN0\_0 | eth3 / igb3 | 07:0.3 | Dead when the box is off |  |
| 5 | LAN0\_1 | eth4 / igb4 | 09:0.0 | Dead when the box is off. Wake-on-LAN capable |  |
| 6 | WAN0\_1 | eth5 / igb5 | 09:0.1 | Dead when the box is off |  |
| 7 | — | eth6 / igb6 | 09:0.2 | None |  |
| 8 | — | eth7 / igb7 | 09:0.3 | None |  |
| 9–12 | SFP+ | eth8–eth11 / ix0–ix3 | 03:0.0/1, 05:0.0/1 | 10 Gb/s; cage order not yet confirmed |  |

### OPNsense (FreeBSD 14)

| Topic | Note |
| --- | --- |
| Image | The [serial image](https://docs.opnsense.org/manual/install.html) (USB, UEFI-capable, console at 115200) |
| Console after install | System → Settings → Administration → Console: primary console Serial, speed 115200 |
| NIC drivers and names | I350 → `igb0`–`igb7`; X552 → `ix0`–`ix3`. Names follow PCI order, so `igb0` should be port 1 (PRI) through `igb7` = port 8. Confirm each against the MAC table in the unit register before assigning |
| SFP+ modules | If the X552 rejects a third-party module, the FreeBSD `ix` driver has an "allow unsupported SFP" tunable (`hw.ix.unsupported_sfp=1`). Untested here |
| AES-NI | System → Settings → Miscellaneous → Cryptography: AES-NI CPU acceleration |
| QAT | **Not usable.** FreeBSD 14 dropped support for this QAT generation ([review D35817](https://reviews.freebsd.org/D35817)) |
| Power | Turn on PowerD (System → Settings → Miscellaneous → Power Savings) |
| Microcode | Plugin `os-cpu-microcode-intel` |
| Watchdog | FreeBSD's `ipmi(4)` driver can drive the BMC watchdog. Leave the BIOS "OS Watchdog Timer" off and arm it from the OS |
| Secure Boot | Not supported by OPNsense out of the box. Possible only by signing its boot files with your own keys and re-signing after every update |
| Offloads | Keep OPNsense's defaults (TSO/LRO off) |

### Proxmox VE (Debian Linux)

| Topic | Note |
| --- | --- |
| Installer | ISO boot menu entry "Install Proxmox VE (Terminal UI, Serial Console)" ([Proxmox wiki](https://pve.proxmox.com/wiki/Installation)) |
| Console after install | GRUB serial terminal and `console=ttyS0,115200n8` on the kernel line (the installer's serial option sets this up) |
| NIC drivers | `igb` and `ixgbe`, both in the kernel |
| IOMMU / passthrough | VT-d, ACS and interrupt remapping are on in the BIOS. Each NIC port is its own IOMMU group: pass whole ports, or SR-IOV VFs (8 per I350 port, 64 per X552 port), to the OPNsense VM. Check `dmesg` for DMAR/IOMMU and add `intel_iommu=on` if needed |
| QAT | No driver in the standard kernel. Intel's out-of-tree QAT 1.7 driver supported this generation (Versa loaded `qat_d15xx`), but may not build on a current Proxmox kernel. Not worth pursuing for a firewall |
| Watchdog | Proxmox HA defaults to `softdog`. To use the BMC watchdog, set `WATCHDOG_MODULE=ipmi_watchdog` in `/etc/default/pve-ha-manager` |
| ipmitool | `apt install ipmitool`: in-band BMC control with no network or password |
| Microcode | `intel-microcode` (Debian non-free-firmware) |
| TPM | Available for host measured boot, or as a virtual TPM for VMs |
| Secure Boot | Supported from Proxmox VE 8.1 with Microsoft-signed shims. Needs the 2023 certificates once 2023-only shims ship |
| Hugepages | The factory OS reserved 4 × 1 GB hugepages for its data plane. Not needed unless you run DPDK |

## Known issues, quirks and open items

### Known issues and quirks

| Symptom | Cause | Fix |
| --- | --- | --- |
| No console output at all; fans cycle up and down repeatedly | POST loop: memory training fails on a badly seated DIMM, and "Halt on mem Training Error" stops POST before the console starts | Power off, reseat both DIMMs, retry |
| Console blank or garbled; Esc/Del/F-keys do nothing in the BIOS but do reach GRUB | Speed mismatch: a factory BIOS console runs at **9600**, GRUB and Linux at **115200** | 9600 for setup on a factory unit; the baseline moves the BIOS to 115200 |
| Setup prompt missed | Prompt is only 1 s on a factory unit | Tap Esc from the moment progress codes appear; the baseline sets 5 s |
| A USB stick in the front port boots instead of the disk | USB is ahead in the boot order | Insert the stick after boot, or use Boot Override deliberately |
| `ipmitool chassis bootdev bios` seemed to be ignored | Never cleanly tested: the attempts were made while the console speed was wrong | Retest at 115200 (ipmitool guide) |
| Front console stops accepting keys | SOL is active and owns the input | Close SOL, or run `ipmitool sol deactivate` |
| `~.` doesn't exit ipmitool SOL | The escape only counts as the first key after Enter | Enter, then `~.`. Fallback: `ipmitool sol deactivate` from another shell |
| Ctrl-C does nothing in the `init=/bin/bash` shell | No controlling terminal | Use commands that stop by themselves (inventory script v3 portmap timer) |
| `ipmitool sol set …` fails with "Invalid data field in request" | Channel number missing | Add the channel: `… 115.2 1` |
| `Could not open device at /dev/ipmi0` | IPMI kernel modules not loaded | `modprobe ipmi_si; modprobe ipmi_devintf` |
| BMC web login fails | The username was given as "2", the user ID | Log in with the name (`admin`) |
| Turbo Mode reads Disable after EIST was enabled | Setup dependency between EIST and Turbo | Re-enable Turbo after changing EIST; check `no_turbo` = 0 |
| BMC event log entries dated hours in the future | BIOS clock set to local time; the BIOS hands it to the BMC as UTC | Keep the BIOS clock on UTC |
| BMC UI shows every user slot "Active" | It's not the enabled flag | Test access with ipmitool |
| `ipmitool fru print` warns "FRU Area length too large" and prints stubs | BMC FRU format quirk | Use the web FRU page, or `fru print 0/1/2` |
| `ixgbe … port expander access failed with -18` in the kernel log | Driver probes an expander this board doesn't fit | Harmless |
| DMI says the BIOS ROM is socketed | DMI template default | The chip is soldered |
| USB stick isn't `/dev/sdf` | The BMC's virtual CD and disk enumerate first | Use the last `sd` device (`sdg` on the reference unit) |
| `lsblk -o …` and `ip -br` fail on the factory OS | Ubuntu 14.04 tools are too old | Inventory script v3 falls back automatically |

### Open items

| Item | What's known | How to close it |
| --- | --- | --- |
| SFP+ cage-to-interface order and module compatibility | Cages 9–12 sit on PCI 03:0.0/1 and 05:0.0/1; MAC order suggests 9 = first | `portmap 120` with a module or DAC |
| NVMe in the M.2 sockets | A CX580 owner got a PCIe 3.0 x2 NVMe drive working by setting `PCH M2 Slot 2` to PCIe, at the cost of a \~2-minute POST hang at code 92 ([Netgate thread](https://forum.netgate.com/topic/183887/pfsense-and-riverbed-cx-780)) | Test on a spare unit with an NVMe drive |
| CPU root ports 00:3.2 and 00:3.3 | Enabled Gen3 x4 ports with nothing attached | Probe with an NVMe test above, or trace the board |
| Expansion slot with a card; bifurcation options | Gen3 x8 electrical, x16 physical, empty | Fit a NIC or NVMe carrier and read the IOU2 option list |
| Maximum RAM | Firmware says 64 GB (2 × 32 GB) | Fit two 32 GB RDIMMs |
| Identify LED; SYS LEDs 1–4 | `chassis identify` is accepted; the rear rocker isn't the LED | Watch the front panel during `ipmitool chassis identify 15` |
| Headers J21, J22, J23, CON2, SWB1, 2×4 | Unknown function; J23 jumper fitted | Leave alone unless recovering a brick |
| TPM location; second UART (ttyS1) | Both present, purpose and location unknown | Low priority |
| Contents of `/opt/versa/firmware` | Possibly Riverbed BIOS/BMC images | List it from the root shell before wiping |
| Latch-Relay Modes 0, 2, 4–6 | Untested | Only on a unit with no live cabling, if ever needed |
| Power and thermals under load; two-PSU standby | Idle and standby measured on one PSU | Measure on the first production build |

## Appendix A: Unit register

One column per unit. Unit 1 is the reference unit. Fill the others from their inventory files (the field names say where each value comes from). Passwords never go here; they live in the password manager under the unit's MFG serial.

| Field (source) | Unit 1 (reference) | Unit 2 | Unit 3 | Unit 4 | Unit 5 | Unit 6 |
| --- | --- | --- | --- | --- | --- | --- |
| Case label SN (front label) | `<case serial>` |  |  |  |  |  |
| MFG / system serial (`dmidecode -s system-serial-number`) | `<UNIT_SERIAL>` (DNI followed by 9 characters) |  |  |  |  |  |
| Board serial (dmidecode type 2) | Two 10-digit numbers joined by + |  |  |  |  |  |
| Board built (BMC FRU) | From FRU 0 |  |  |  |  |  |
| BIOS (setup Main) | 0ACJZ 0.11 x0.45V |  |  |  |  |  |
| BMC firmware (`ipmitool mc info`) | 0.53.1108131520 |  |  |  |  |  |
| ME firmware (IntelRCSetup → Server ME) | SPS 3.0.3 (build 59) |  |  |  |  |  |
| BMC MAC (`ipmitool lan print 1`) | 6C:B9:C5:xx:xx:xx |  |  |  |  |  |
| BMC address / user | `<BMC_IP>` / admin (ID 2) |  |  |  |  |  |
| Port 1–2 MACs (PRI, AUX) | 00:0e:b6:xx:xx:xx, two consecutive addresses |  |  |  |  |  |
| Port 3–8 MACs | 00:0e:b6:xx:xx:xx, a separate block of six, in port order |  |  |  |  |  |
| SFP+ MACs (PCI 03:0.0/1, 05:0.0/1) | The next four addresses after port 8's |  |  |  |  |  |
| RAM (dmidecode type 17) | 8 GB (A1) + 16 GB (B1), 2400 MT/s |  |  |  |  |  |
| P0 drive / serial | ST1000NX0423 / `<serial>` |  |  |  |  |  |
| P1 drive / serial | ST1000NX0423 / `<serial>` (old Versa root) |  |  |  |  |  |
| P2 drive / serial | Intel SSDSCKKB240G8 / `<serial>` |  |  |  |  |  |
| P3 drive / serial | Intel SSDSCKKB240G8 / `<serial>` |  |  |  |  |  |
| P4 drive / serial | Virtium VSFBM4CC030G-15A / `<serial>` |  |  |  |  |  |
| Drive power-on hours (`smartctl -x`) | 15,953 |  |  |  |  |  |
| BMC power-on time (`ipmitool chassis poh`) | 641 days |  |  |  |  |  |
| PSU1 / PSU2 serials (BMC FRU 1/2) | `<serial>` / `<serial>` |  |  |  |  |  |
| `/opt/versa/firmware` checked | Not yet |  |  |  |  |  |
| Drives wiped | Not yet |  |  |  |  |  |
| Baseline applied (date) | YYYY-MM-DD |  |  |  |  |  |
| Deviations / notes | Turbo needed re-enabling after EIST; BMC DNS inherited from previous owner (cleared) |  |  |  |  |  |

## Appendix B: POST code reference

The BIOS prints AMI Aptio V progress codes on the serial console. Only the boot-device phase (BDS, 0x90 and up) reaches serial: earlier phases run before the console starts. That's why a memory-training hang shows a blank console. The last code printed tells you where a boot stopped.

| Code | Meaning | Seen on this box |
| --- | --- | --- |
| 92 | PCI bus initialisation started | Yes. A 2-minute hang here was reported on a CX580 with NVMe enabled |
| 98 | Console input devices connect | Yes, the first code on screen |
| 9A / 9B / 9C / 9D | USB init started / reset / detect / enable | 9C and 9D repeat |
| B4 | USB hot-plug | 4 times: the BMC's virtual hub, CD and disk appearing |
| A0 / A1 / A2 / A3 | IDE (SATA) init started / reset / detect / enable | A0, then A2 repeated for the drives |
| B2 | Legacy option ROM initialisation | Repeats: the I350 network boot agents |
| A9 | Start of setup | After Esc |
| AB | Setup input wait | Shown in setup's bottom-right corner |
| AD / AE | Ready to boot / legacy boot event | Hand-over to the boot loader |
| AA / AC | OS in ACPI mode (APIC / PIC) | Port 80 only |
| D0–DF | Errors: D0 CPU init, D4 PCI resources exhausted, D6 no console output, DB flash update failed, and others | Any of these on screen with a stalled boot is the fault |

**Phase ranges:** SEC 0x01–0x0F; PEI 0x10–0x5F, with memory at 0x2B–0x2F and errors at 0x50–0x5F; DXE 0x60–0x8F; BDS 0x90–0xCF. Source: [AMI Aptio V POST codes (Supermicro)](https://www.supermicro.com/manuals/other/AMI_AptioV_BIOS_POST_Codes_for_SM_Motherboards.pdf).

The full boot as seen on the reference unit's console:

1. `98 9D 9C 9D 9C B4 B4 B4 B4 92 A0 A2 A2 A2 A2 A2 … B2`
2. The version banner, then `Press <DEL> or <ESC> to enter setup.`
3. `Entering Setup...` (A9, then AB).

## Appendix C: Inventory script (v3)

The script below is the complete `cx3080-inventory.sh` v3. It produces the hardware dump this article is built from.

- Run it from the GRUB root shell (Baseline Phase 4) or from any Linux with root.
- It only reads, except that it loads NIC and IPMI drivers and brings links up with no IP addresses.
- `portmap` mode watches link state while you move a cable through the ports, then stops by itself.
- It doesn't read the factory OS's configuration. It lists `/opt/versa/firmware` because Riverbed's firmware images may be there.

```bash
#!/usr/bin/env bash
# cx3080-inventory.sh v3 - hardware reference dump for a Riverbed SteelHead CX-3080 / SteelConnect EX-3080
# (DNI SNRACK-1553N board, Xeon D-1553N).
#
# Designed to run from the box's existing Ubuntu install booted with init=/bin/bash (no Versa services,
# no networking), but works on any Linux. Read-only apart from: bringing NIC links up (no IPs), loading
# drivers, and writing the output file to the current directory.
#
# Usage (from a USB stick mounted at /mnt):
#   bash cx3080-inventory.sh               -> writes cx3080-<serial>-<timestamp>.txt in the current dir
#   bash cx3080-inventory.sh portmap [s]   -> live carrier watcher for mapping physical ports; stops by
#                                             itself after s seconds (default 180). Ctrl-C does NOT work in
#                                             an init=/bin/bash shell (no controlling terminal), hence the timer.
#
# Console: BIOS 9600 8N1 by default (115200 after the BIOS change), GRUB/Linux 115200 8N1.
#
# v3: portmap self-stops and is also logged to portmap-<serial>.txt; fallbacks for the old lsblk/ip on
#     Ubuntu 14.04; adds turbo/cpuidle state, partition table, FRU-by-ID output and a listing of
#     /opt/versa/firmware (where Riverbed's BIOS/BMC images may be).

set -u

physifs() { for p in /sys/class/net/*; do [ -e "$p/device" ] && echo "${p##*/}"; done; }

bring_up() {
  for m in igb ixgbe i40e e1000e; do modprobe -q "$m" 2>/dev/null; done
  for n in $(physifs); do ip link set "$n" up 2>/dev/null; done
}

if [ "${1:-}" = "portmap" ]; then
  secs="${2:-180}"
  bring_up
  PSN=$(cat /sys/class/dmi/id/product_serial 2>/dev/null | tr -cd '[:alnum:]-')
  PLOG="portmap-${PSN:-unknown}.txt"
  echo "Plug ONE cable (to a live switch/laptop) into each front port in order 1..12, ~5 s each."
  echo "Stops by itself after ${secs} s (Ctrl-C won't work here). Also logging to $(pwd)/$PLOG"
  end=$(( $(date +%s) + secs ))
  declare -A last
  while [ "$(date +%s)" -lt "$end" ]; do
    for n in $(physifs); do
      c=$(cat /sys/class/net/$n/carrier 2>/dev/null || echo "?")
      if [ "${last[$n]:-x}" != "$c" ]; then
        printf '%s  %-14s carrier=%s  mac=%s  pci=%s  speed=%s\n' "$(date +%T)" "$n" "$c" \
          "$(cat /sys/class/net/$n/address)" "$(basename "$(readlink -f /sys/class/net/$n/device)")" \
          "$(cat /sys/class/net/$n/speed 2>/dev/null || echo -)" | tee -a "$PLOG"
        last[$n]=$c
      fi
    done
    sleep 1
  done
  sync
  echo "Port map finished -> $(pwd)/$PLOG"
  exit 0
fi

[ "$(id -u)" -eq 0 ] || { echo "Please run as root"; exit 1; }
mountpoint -q /proc || mount -t proc proc /proc
mountpoint -q /sys  || mount -t sysfs sysfs /sys

for c in lspci lsusb dmidecode ethtool smartctl hdparm sensors ipmitool timeout; do
  command -v "$c" >/dev/null 2>&1 || echo "note: '$c' not installed - that section will be skipped"
done

SN=$(dmidecode -s system-serial-number 2>/dev/null | tr -cd '[:alnum:]-')
OUT="cx3080-${SN:-unknown}-$(date +%Y%m%d-%H%M).txt"
run() { echo "===== $* ====="; timeout 90 "$@" 2>&1; echo; }

modprobe -q ipmi_si 2>/dev/null; modprobe -q ipmi_devintf 2>/dev/null
bring_up
echo "Waiting 10 s for NIC links / SFP detection..."
sleep 10

{
  echo "##### SYSTEM"
  run date -u
  run uname -a
  run cat /proc/cmdline
  run bash -c '[ -d /sys/firmware/efi ] && echo "Boot mode: UEFI" || echo "Boot mode: legacy BIOS"'
  run dmidecode
  run lscpu
  run bash -c "sed -n '1,/^\$/p' /proc/cpuinfo"
  run bash -c "grep -m1 microcode /proc/cpuinfo"
  run bash -c 'ls /sys/devices/system/cpu/cpu0/cpufreq/ 2>&1; cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_frequencies 2>&1; ls /sys/devices/system/cpu/cpu0/cpuidle/ 2>&1'
  run bash -c 'cd /sys/devices/system/cpu/cpu0/cpufreq 2>/dev/null && for f in cpuinfo_min_freq cpuinfo_max_freq scaling_governor; do echo "$f: $(cat $f 2>&1)"; done; echo "intel_pstate no_turbo: $(cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>&1)"; for s in /sys/devices/system/cpu/cpu0/cpuidle/state*; do echo "${s##*/}: $(cat $s/name 2>/dev/null) latency=$(cat $s/latency 2>/dev/null)us disabled=$(cat $s/disable 2>/dev/null)"; done'
  run cat /proc/meminfo

  echo "##### PCIe / USB"
  run lspci -tv
  run lspci -nnkvvv
  run lsusb
  run lsusb -t

  echo "##### STORAGE"
  run bash -c 'lsblk -o NAME,MODEL,SERIAL,SIZE,ROTA,TRAN,HCTL 2>/dev/null || lsblk -o NAME,MODEL,SIZE,ROTA,TYPE,FSTYPE,MOUNTPOINT 2>/dev/null || lsblk'
  run bash -c 'cat /proc/partitions; command -v blkid >/dev/null && blkid -o list 2>/dev/null'
  run bash -c 'for b in /sys/block/sd*; do echo "${b##*/} -> $(readlink -f $b/device)"; done'
  for d in /dev/sd? /dev/nvme?n1; do
    [ -e "$d" ] || continue
    run smartctl -x "$d"
    run hdparm -I "$d"
  done

  echo "##### NETWORK"
  run bash -c 'ip -br link 2>/dev/null || ip -o link'
  run bash -c 'for p in /sys/class/net/*; do [ -e $p/device ] && echo "${p##*/}  $(cat $p/address)  $(basename $(readlink -f $p/device))  carrier=$(cat $p/carrier 2>/dev/null)"; done'
  for n in $(physifs); do
    run ethtool -i "$n"
    run ethtool "$n"
    run ethtool -m "$n"
  done

  echo "##### IOMMU GROUPS"
  run bash -c 'shopt -s nullglob; gs=(/sys/kernel/iommu_groups/*)
    if [ ${#gs[@]} -eq 0 ]; then echo "No IOMMU groups (VT-d off, or kernel lacks intel_iommu=on)"; exit 0; fi
    for g in $(ls /sys/kernel/iommu_groups | sort -n); do echo "group $g:"
      for d in /sys/kernel/iommu_groups/$g/devices/*; do echo "   $(lspci -nns ${d##*/})"; done
    done'

  echo "##### TPM / WATCHDOG / SERIAL / I2C"
  run bash -c 'ls -l /dev/tpm* /dev/tpmrm* /dev/watchdog* /dev/ipmi* /dev/ttyS* 2>&1'
  run bash -c 'for f in /sys/class/tpm/tpm0/device/description /sys/class/tpm/tpm0/device/caps /sys/class/tpm/tpm0/tpm_version_major; do [ -e $f ] && { echo "$f:"; cat $f; }; done; ls /sys/class/tpm/ 2>&1'
  run bash -c 'cat /proc/tty/driver/serial 2>&1'
  run bash -c 'ls -l /sys/bus/i2c/devices/ 2>&1; for a in /sys/bus/i2c/devices/i2c-*/name; do echo "$a: $(cat $a)"; done'
  run bash -c 'ls /sys/class/gpio 2>&1'

  echo "##### BMC / IPMI"
  run ipmitool mc info
  run ipmitool chassis status
  run ipmitool chassis poh
  run ipmitool chassis bootparam get 5
  run ipmitool mc watchdog get
  run ipmitool fru print
  for id in 0 1 2; do run ipmitool fru print $id; done
  run ipmitool sdr elist full
  run ipmitool sensor
  run ipmitool lan print 1
  run ipmitool channel info 1
  run ipmitool sol info 1
  run ipmitool user list 1
  run ipmitool sel info

  echo "##### THERMALS"
  run sensors

  echo "##### DRIVERS / VENDOR BYPASS CONTROL (code only, no configs)"
  run lsmod
  run bash -c "find /lib/modules/\$(uname -r) -iname '*bypass*' -o -iname '*bpctl*' -o -iname '*relay*' -o -iname '*rvbd*' 2>/dev/null"
  run bash -c 'cat /etc/modules 2>/dev/null; ls /etc/modprobe.d/ 2>/dev/null'
  run bash -c 'ls /opt/versa 2>/dev/null'
  run bash -c 'ls -laR /opt/versa/firmware 2>/dev/null | head -200'   # possible Riverbed BIOS/BMC images
  run bash -c "grep -rIn -i -E 'latch|relay|bypass|ipmitool raw' /opt/versa/scripts /opt/versa/bin /usr/local/bin /usr/local/sbin 2>/dev/null | grep -v -i -E 'passw|secret|key' | head -300"

  echo "##### KERNEL LOG"
  run dmesg
} > "$OUT" 2>&1

sync
echo "Done -> $(pwd)/$OUT"
```

## Appendix D: Pre-OS-install run sheet

Everything to change or check on a unit between "as received" and booting the OS installer, in working order. It pulls together the baseline procedure, the BIOS and BMC references and the security and efficiency sections, so you can work down a single list. Each item says where to go, what to set and how to confirm it.

**How to use it.**

- Do one full pass per unit. Ticks in this doc are shared, so untick everything before starting the next unit, or export a copy per unit.
- Items marked **(optional)** are worth doing in some deployments. Everything else is required.
- Record values in the unit register (Appendix A). Passwords go in the password manager only.
- D8 is irreversible. Don't start it until its preconditions are ticked.

### D1. Prepare

*Details:* Baseline bring-up procedure → Phase 0 (including why the rules exist and the credentials to create); Access methods → Serial console settings; the ipmitool guide's setup section.

- [ ] Laptop: PuTTY sessions saved at 9600 and 115200, with logging set to "All session output" and a timestamped file name
- [ ] WSL with ipmitool: `sudo apt install ipmitool`
- [ ] USB stick (FAT32) holding `cx3080-inventory.sh` v3, with spare room for a firmware copy
- [ ] Isolated management subnet with the laptop cabled to front port 1 (PRI). Ports 2–12 unplugged
- [ ] Password-manager entries created for this unit (BMC admin, BMC sysadmin, BIOS administrator), named by the unit's MFG serial
- [ ] The unit's column started in Appendix A

### D2. Hardware

*Details:* Physical layout → Inside the case; Hardware specification → Memory (fitting a matched pair) and Storage; OS notes → Common to both (install disk); Efficiency → Power and hardware choices.

- [ ] Lid off: both DIMMs fully latched, M.2 modules screwed down, fan module seated, no loose cables
- [ ] (optional) A matched DIMM pair fitted, for full two-channel interleave
- [ ] Drive plan decided: Intel M.2 pair for an OS mirror, Virtium for a minimal boot disk, Seagates optional bulk storage. Leave every drive fitted until D8
- [ ] Case label serial and MFG number recorded in Appendix A
- [ ] Lid refitted. One PSU is enough for bring-up; fit both for production

### D3. First power-on (console at 9600)

*Details:* Physical layout → Healthy power-on signature; Known issues; Appendix B (POST codes).

- [ ] Healthy signature seen: fans quiet at \~17 s, amber off on ports 3–6 at \~21 s, one beep at \~37 s, then progress codes and the setup prompt
- [ ] If there's no output and the fans keep cycling: power off and reseat the RAM (Known issues)

### D4. BIOS settings (enter setup at 9600: tap Esc after the beep)

*Details:* each setting's factory value, baseline and reason are in BIOS setup reference parts 1–3. Step-by-step procedures: Clearing the TPM (Advanced → Trusted Computing), Setting the administrator password (Security), and Choosing the BMC's port (BMC reference → Network).

**Main**

- [ ] System Date / System Time → current **UTC**, not local time

**Advanced**

- [ ] Serial Port Console Redirection → COM0 → Console Redirection Settings → Bits per second → **115200**
- [ ] CSM Configuration → Boot option filter → **UEFI and Legacy** (the factory disk must still boot for D5)
- [ ] Trusted Computing → Pending operation → **TPM Clear** (once per unit; accept any confirmation prompt at the next boot)
- [ ] Network Stack Configuration → Network Stack → confirm **Disabled**
- [ ] (optional, hardening) PCI Subsystem Settings → BME DMA Mitigation → Enabled. Check that every NIC still comes up in D5
- [ ] (optional, efficiency) PCI Subsystem Settings → PCI Express Settings → Unpopulated Links → Disable Link

**IntelRCSetup**

- [ ] Processor Configuration → Hyper-Threading \[ALL\] → **Enable**
- [ ] Advanced Power Management Configuration → EIST (P-states) → **Enable**
- [ ] … → CPU P State Control → Turbo Mode → **Enable**. Check it *after* changing EIST, because the EIST change can flip it
- [ ] … → CPU C State Control → CPU C State **Enable**; Package C State limit **C6 (non-retention)**; CPU C6 report **Enable**; Enhanced Halt State (C1E) **Enable**
- [ ] … → CPU Advanced PM Tuning → Energy Perf BIAS → Energy Performance BIAS setting → **Balanced Performance**
- [ ] Confirm these are still at factory: VT-d, ACS Control, Interrupt Remapping and SR-IOV Enabled; BIOS Lock, Host Flash Lock-Down and RTC Lock Enabled; DEBUG INTERFACE, EV DFX Features and S/W Error Injection Disabled
- [ ] (optional, observability) Runtime Error Logging → Memory corrected Error → Enable

**Server Mgmt**

- [ ] BMC network configuration → IPV6 Support → **Disabled**
- [ ] BMC network configuration → Configuration Address → confirm **Unspecified**
- [ ] BMC network configuration → BMC Ext. Network port → decide now: **Port1** (default) or Port2. Cable the management network to that port from here on
- [ ] Latch-Relay Mode → confirm **1**
- [ ] Power Control Policy → **Power Restore** for a production unit, **Do Not PowerUp** for a spare on the shelf
- [ ] OS Watchdog Timer → confirm **Disabled** (the OS arms the watchdog later)
- [ ] (optional, resilience) FRB-2 Timer Policy → Reset, so a hung POST recovers by itself

**Security**

- [ ] Administrator Password → set it and store it in the password manager. A lost password needs a CMOS clear, and the clear jumper isn't identified

**Boot**

- [ ] Setup Prompt Timeout → **5**
- [ ] Quiet Boot → confirm **Disabled**

**Save & Exit**

- [ ] Save as User Defaults
- [ ] Save Changes and Reset, then switch PuTTY to **115200** straight away. The progress codes and setup prompt must now appear at 115200

### D5. Root shell on the factory disk (115200)

*Details:* Access methods → Root shell; Baseline Phase 4; BMC reference → Accounts (password rules); Firmware and microcode → Where Riverbed's images might be (copy commands); Appendix C.

At GRUB press `e`, add `init=/bin/bash` to the end of the `linux` line, then Ctrl-X. In the shell, run `mount -t proc proc /proc; mount -t sysfs sysfs /sys` and `modprobe ipmi_si; modprobe ipmi_devintf`.

- [ ] `nproc` returns **16**
- [ ] `cat /sys/devices/system/cpu/intel_pstate/no_turbo` returns **0**
- [ ] SOL speed: `ipmitool sol set non-volatile-bit-rate 115.2 1`, then `ipmitool sol set volatile-bit-rate 115.2 1`
- [ ] Anonymous user off: `ipmitool user disable 1`
- [ ] Admin password, unique per unit: `ipmitool user set password 2` (it prompts)
- [ ] BMC address, if not already set: `ipmitool lan set 1 ipsrc static`, then `ipaddr <BMC_IP>` and `netmask <NETMASK>`, with no gateway on an isolated subnet. Confirm with `ipmitool lan print 1`
- [ ] Stick mounted: `ls /dev/sd*`, then mount the last `sd` device's partition (`mount /dev/sdg1 /mnt` on the reference unit)
- [ ] Inventory: `bash cx3080-inventory.sh` writes `cx3080-<serial>-<time>.txt` to the stick
- [ ] Port map: `bash cx3080-inventory.sh portmap 180`, moving one cable through ports 1 → 8, about 5 s each. Expect the same order as the reference unit
- [ ] (optional) SFP+ cage order, if a module or DAC is to hand: `bash cx3080-inventory.sh portmap 120`
- [ ] Riverbed firmware: check the `/opt/versa/firmware` listing in the inventory file. If it holds anything, copy it before D8: `cp -r /opt/versa/firmware /mnt/firmware-<UNIT_SERIAL>`
- [ ] `sync; cd /; umount /mnt`. Leave the shell running for D7

### D6. BMC web interface (`https://<BMC_IP>`, logged in as `<BMC_USER>`)

*Details:* BMC reference → Services (turning off SSH), Accounts (passwords), Other settings (optional settings, step by step) and Maintenance pages; Security hardening sections 1 and 2.

- [ ] Maintenance → System Administrator: change the sysadmin password, or untick Enable User Access
- [ ] Settings → Services → ssh → **inactive**, unless you use the BMC shell
- [ ] Settings → Network Settings → DNS Configuration: clear any inherited domain and DNS servers, untick Register BMC, then Save
- [ ] Directory and alert settings are empty: LDAP/E-Directory, Active Directory, RADIUS, SMTP and alert destinations
- [ ] Settings → Date & Time: NTP to a lab time source if there is one; otherwise confirm the time reads UTC
- [ ] Sensor and FRU pages match the reference values (Hardware specification); note any differences in Appendix A
- [ ] (optional) Settings → System Firewall: allow only the management subnet or admin workstation. Test from the laptop before logging out; if you lock yourself out, use BIOS Server Mgmt or in-band ipmitool to recover
- [ ] (optional) Settings → SSL Settings: replace the AMI default certificate
- [ ] (optional) Settings → Log Settings: send remote syslog and the audit log to the lab syslog server
- [ ] (optional, only if alerting is used) change the SNMP community from `AMI`

### D7. Prove remote management (WSL)

*Details:* the ipmitool guide (setup, recipes and labs); Access methods → Serial over LAN; Known issues (the `~.` escape).

Set up once per WSL session: `read -rsp 'BMC password: ' IPMI_PASSWORD; echo; export IPMI_PASSWORD`, then `alias bmc='ipmitool -I lanplus -H <BMC_IP> -U <BMC_USER> -E'`. Keep a second tab open for `bmc sol deactivate`.

- [ ] Anonymous login refused: `ipmitool -I lanplus -H <BMC_IP> -U '' chassis status`, pressing Enter at the password prompt, fails while `ping <BMC_IP>` works
- [ ] `bmc sol activate`, then Enter, shows the root-shell prompt
- [ ] From the second tab, `bmc chassis power reset`: POST appears over SOL at 115200, Esc reaches setup, and you leave with Discard Changes and Exit
- [ ] `bmc sel time get` shows current UTC
- [ ] (optional, open item) `bmc chassis bootdev bios` then `bmc chassis power reset` opens setup without pressing Esc
- [ ] `bmc sol deactivate`

### D8. Wipe the previous owner's data (irreversible)

*Details:* Security hardening → 4. Previous owner's data → Wiping the drives, step by step.

**Preconditions:**

- [ ] The inventory and port-map files are copied off the stick to the unit's records
- [ ] `/opt/versa/firmware` has been checked, and copied if not empty
- [ ] Appendix A is filled in for this unit, including drive models and serials

**Where to run it.** The factory Ubuntu runs from P1 and its tools may lack `blkdiscard`. Use a current Linux live USB or installer shell instead: boot it with Save & Exit → Boot Override, and at its boot menu add `console=ttyS0,115200n8` to the kernel line.

- [ ] Every drive identified by model and serial before wiping: `lsblk -o NAME,MODEL,SERIAL,SIZE`, cross-checked with Appendix A. The live stick and the BMC's virtual media also appear as `sd` devices
- [ ] SSDs (Intel P2 and P3, Virtium P4): `blkdiscard /dev/sdX`
- [ ] HDDs (Seagate P0 and P1): `dd if=/dev/zero of=/dev/sdX bs=1M status=progress` (about 2 hours per drive), or ATA secure erase (needs a hot-plug first; see Security hardening)
- [ ] Spot-check each drive: `cmp -n 104857600 /dev/zero /dev/sdX` prints nothing when the first 100 MB are zeros. If an SSD isn't zeroed after `blkdiscard`, overwrite it with `dd`
- [ ] (optional) Pull the Seagates if the build won't use them; each saves a few watts

### D9. Final BIOS pass, just before the installer

*Details:* BIOS setup reference part 3 → Boot (network boot entries; final pre-install pass) and Event Logs (erasing the SMBIOS event log).

Do this last. After it, nothing legacy will boot.

- [ ] Boot → Boot mode select → **UEFI**
- [ ] Advanced → CSM Configuration → CSM Support → **Disabled**. This removes the legacy boot path and the I350 network boot agents
- [ ] Boot → boot order: network entries disabled. The install disk goes first after the install
- [ ] (optional) Event Logs → Erase Event Log → Yes, to clear the previous owner's SMBIOS log
- [ ] Secure Boot left **Disabled** for the install
- [ ] Save as User Defaults again, so the saved baseline includes UEFI-only
- [ ] Save Changes and Reset. Progress codes and the setup prompt still appear at 115200

### D10. Close out

*Details:* BMC reference → Maintenance pages (taking a configuration backup); Security hardening → 1. Management-plane isolation; OS notes (install media, port plan worksheet); Access methods → Virtual media; Appendix A.

- [ ] BMC event log cleared, so the OS stage starts clean: `bmc sel clear`
- [ ] BMC Maintenance → Backup Configuration taken. Store the file with the unit's records and protect it like a credential, as it may contain account settings
- [ ] Appendix A complete for this unit, including the "`/opt/versa/firmware` checked" row
- [ ] PuTTY logs, inventory and port-map files filed with the unit's records
- [ ] Management cabling final: the BMC port reaches only the management network, with no route to the WAN or internet
- [ ] Port plan written down: port 1 (or 2, if the BMC moved) for management only; WAN and LAN assignments; ports 3–6 are dead when the box is off; SFP+ roles
- [ ] Install media ready: the OPNsense serial image, or the Proxmox ISO's "Terminal UI, Serial Console" entry, on USB or BMC virtual media, at 115200
- [ ] (optional) Unit labelled with its unit number and BMC address

### Left for after the install (don't do these yet)

| Item | Why it waits |
| --- | --- |
| Secure Boot: PKfail check, your own PK, Microsoft 2023 certificates | Needs a UEFI OS in place to test against (Secure Boot steps, BIOS part 3) |
| CPU microcode package | Comes from the OS |
| PowerD (OPNsense) or the intel\_pstate check (Proxmox) | OS settings |
| Hardware watchdog | Armed from the OS through its IPMI driver; the BIOS OS Watchdog Timer stays off |
| Measured boot, TPM-sealed disk keys | OS features |
| Interface assignment, offloads, NTP in the OS | OS configuration (OS notes) |
| Power and thermals under load | Need the final OS |

### Keep track of what's outstanding

Pausing part-way through is normal: SFP+ mapping needs a module, and the wipe needs time. Note anything from D1–D10 that's still open in the unit's "Deviations / notes" row of Appendix A, so the next person can pick the unit up where it was left.

## Sources

- [Intel Xeon D-1553N specifications (Intel)](https://www.intel.com/content/www/us/en/products/sku/123002/intel-xeon-processor-d1553n-12m-cache-2-30-ghz/specifications.html)
- [Netgate forum: pfSense and Riverbed CX-780](https://forum.netgate.com/topic/183887/pfsense-and-riverbed-cx-780)
- [AMI Aptio V BIOS POST codes (Supermicro)](https://www.supermicro.com/manuals/other/AMI_AptioV_BIOS_POST_Codes_for_SM_Motherboards.pdf)
- [FreeBSD review D35817: old QAT driver renamed, newer devices dropped](https://reviews.freebsd.org/D35817)
- [Linux kernel QAT driver list (Kconfig)](https://raw.githubusercontent.com/torvalds/linux/master/drivers/crypto/intel/qat/Kconfig)
- [CSO Online: critical vulnerability in AMI MegaRAC BMC (CVE-2024-54085)](https://www.csoonline.com/article/3848376/critical-vulnerability-in-ami-megarac-bmc-allows-servers-takeover.html)
- [BleepingComputer: PKfail Secure Boot bypass](https://www.bleepingcomputer.com/news/security/pkfail-secure-boot-bypass-lets-attackers-install-uefi-malware/)
- [AlmaLinux: Microsoft 2023 Secure Boot certificate transition](https://wiki.almalinux.org/documentation/secure-boot-2023-certificates)
- [Intel Linux processor microcode releases](https://github.com/intel/Intel-Linux-Processor-Microcode-Data-Files)
- [OPNsense installation manual (image types)](https://docs.opnsense.org/manual/install.html)
- [Proxmox VE installation wiki](https://pve.proxmox.com/wiki/Installation)
