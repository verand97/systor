import psutil
import time
import os
import getpass
import platform
import datetime
import threading
import subprocess
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich import box
from rich.align import Align
from rich.console import Console
from rich.text import Text

console = Console()

VERAND_LOGO = r"""
 _    ____________  ___    _   ______     _______  _________________  ____ 
| |  / / ____/ __ \/   |  / | / / __ \   / ___/\ \/ / ___/_  __/ __ \/ __ \
| | / / __/ / /_/ / /| | /  |/ / / / /   \__ \  \  /\__ \ / / / / / / /_/ /
| |/ / /___/ _, _/ ___ |/ /|  / /_/ /   ___/ /  / /___/ // / / /_/ / _, _/ 
|___/_____/_/ |_/_/  |_/_/ |_/_____/   /____/  /_//____//_/  \____/_/ |_|  
"""

def get_header():
    return Panel(
        Align.center(Text(VERAND_LOGO, style="bold cyan")), 
        border_style="cyan", 
        box=box.ROUNDED
    )

import winreg
import ctypes
import locale

SYS_INFO_CACHE = {}

def init_sys_info_cache():
    global SYS_INFO_CACHE
    try:
        # OS Info
        k_os = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion')
        os_name = winreg.QueryValueEx(k_os, 'ProductName')[0]
        
        if os_name.startswith("Windows 10") and int(platform.version().split('.')[2]) >= 22000:
            os_name = os_name.replace("Windows 10", "Windows 11")
        
        build = platform.version().split('.')[2]
        arch = "64-bit" if platform.machine().endswith('64') else "32-bit"
        SYS_INFO_CACHE['os'] = f"{os_name} {arch} (10.0, Build {build})"
        winreg.CloseKey(k_os)
    except:
        SYS_INFO_CACHE['os'] = f"{platform.system()} {platform.release()} {platform.machine()}"
        
    try:
        # BIOS Info
        k_bios = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'HARDWARE\DESCRIPTION\System\BIOS')
        SYS_INFO_CACHE['manufacturer'] = winreg.QueryValueEx(k_bios, 'SystemManufacturer')[0]
        SYS_INFO_CACHE['model'] = winreg.QueryValueEx(k_bios, 'SystemProductName')[0]
        SYS_INFO_CACHE['bios'] = winreg.QueryValueEx(k_bios, 'BIOSVersion')[0]
        winreg.CloseKey(k_bios)
    except:
        SYS_INFO_CACHE['manufacturer'] = "Unknown"
        SYS_INFO_CACHE['model'] = "Unknown"
        SYS_INFO_CACHE['bios'] = "Unknown"
        
    try:
        # CPU Info
        k_cpu = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'HARDWARE\DESCRIPTION\System\CentralProcessor\0')
        cpu_name = winreg.QueryValueEx(k_cpu, 'ProcessorNameString')[0].strip()
        cores = psutil.cpu_count(logical=True)
        freq = psutil.cpu_freq().max if psutil.cpu_freq() else 0
        freq_ghz = freq / 1000 if freq > 1000 else (freq if freq > 0 else 2.4) # Default fallback
        freq_str = f"~{freq_ghz:.1f}GHz"
        SYS_INFO_CACHE['processor'] = f"{cpu_name} ({cores} CPUs), {freq_str}"
        winreg.CloseKey(k_cpu)
    except:
        SYS_INFO_CACHE['processor'] = platform.processor()
        
    # Language
    try:
        lang = locale.windows_locale.get(ctypes.windll.kernel32.GetUserDefaultUILanguage(), 'Unknown')
        lang_map = {'en_US': 'English', 'id_ID': 'Indonesian'}
        base_lang = lang.split('_')[0]
        display_lang = lang_map.get(lang, "English") if base_lang == 'en' else lang
        if base_lang == 'en': display_lang = "English"
        if base_lang == 'id': display_lang = "Indonesian"
        SYS_INFO_CACHE['language'] = f"{display_lang} (Regional Setting: {display_lang})"
    except:
        SYS_INFO_CACHE['language'] = "English (Regional Setting: English)"
        
    SYS_INFO_CACHE['dx'] = "DirectX 12" if platform.system() == "Windows" and int(platform.release()) >= 10 else "DirectX 11"
    SYS_INFO_CACHE['computer_name'] = platform.node()

init_sys_info_cache()

def get_system_info():
    table = Table(box=box.SIMPLE, show_header=False, expand=True)
    table.add_column("Property", justify="right", style="white")
    table.add_column("Value", justify="left", style="white")
    
    current_time = datetime.datetime.now().strftime("%A, %d %B %Y, %H:%M:%S")
    
    # Memory
    mem = psutil.virtual_memory()
    total_mb = int(mem.total / (1024 * 1024))
    mem_str = f"{total_mb}MB RAM"
    
    # Page file
    swap = psutil.swap_memory()
    swap_used_mb = int(swap.used / (1024 * 1024))
    swap_free_mb = int(swap.free / (1024 * 1024))
    page_str = f"{swap_used_mb}MB used, {swap_free_mb}MB available"
    
    table.add_row("Current Date/Time:", current_time)
    table.add_row("Computer Name:", SYS_INFO_CACHE['computer_name'])
    table.add_row("Operating System:", SYS_INFO_CACHE['os'])
    table.add_row("Language:", SYS_INFO_CACHE['language'])
    table.add_row("System Manufacturer:", SYS_INFO_CACHE['manufacturer'])
    table.add_row("System Model:", SYS_INFO_CACHE['model'])
    table.add_row("BIOS:", SYS_INFO_CACHE['bios'])
    table.add_row("Processor:", SYS_INFO_CACHE['processor'])
    table.add_row("Memory:", mem_str)
    table.add_row("Page file:", page_str)
    table.add_row("DirectX Version:", SYS_INFO_CACHE['dx'])
    
    return Panel(table, title="[blue]System Information", border_style="blue")

def get_cpu_info():
    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_freq = psutil.cpu_freq()
    
    table = Table(box=box.SIMPLE, show_header=False, expand=True)
    table.add_column("Property")
    table.add_column("Value", justify="right")
    
    color = "green"
    if cpu_percent > 80:
        color = "red"
    elif cpu_percent > 60:
        color = "yellow"
        
    table.add_row("Penggunaan", f"[{color}]{cpu_percent}%[/{color}]")
    if cpu_freq:
        table.add_row("Frekuensi", f"{cpu_freq.current:.0f} MHz")
    table.add_row("Jumlah Core", f"{psutil.cpu_count(logical=True)}")
    
    return Panel(table, title="[cyan]CPU", border_style="cyan")

def get_ram_info():
    mem = psutil.virtual_memory()
    
    total = mem.total / (1024 ** 3)
    used = mem.used / (1024 ** 3)
    
    table = Table(box=box.SIMPLE, show_header=False, expand=True)
    table.add_column("Property")
    table.add_column("Value", justify="right")
    
    color = "green"
    if mem.percent > 80:
        color = "red"
    elif mem.percent > 60:
        color = "yellow"
    
    table.add_row("Total", f"{total:.2f} GB")
    table.add_row("Terpakai", f"{used:.2f} GB")
    table.add_row("Persentase", f"[{color}]{mem.percent}%[/{color}]")
    
    return Panel(table, title="[magenta]RAM", border_style="magenta")

def get_disk_info():
    partitions = psutil.disk_partitions()
    table = Table(box=box.SIMPLE, expand=True)
    table.add_column("Drive")
    table.add_column("Total", justify="right")
    table.add_column("Terpakai", justify="right")
    table.add_column("Sisa", justify="right")
    table.add_column("Pemakaian %", justify="right")
    
    for p in partitions:
        if 'cdrom' in p.opts or p.fstype == '':
            continue
        try:
            usage = psutil.disk_usage(p.mountpoint)
            total = usage.total / (1024 ** 3)
            used = usage.used / (1024 ** 3)
            free = usage.free / (1024 ** 3)
            percent = usage.percent
            
            color = "green"
            if percent > 85:
                color = "red"
            elif percent > 70:
                color = "yellow"
                
            table.add_row(
                p.device,
                f"{total:.1f} GB",
                f"{used:.1f} GB",
                f"{free:.1f} GB",
                f"[{color}]{percent}%[/{color}]"
            )
        except PermissionError:
            continue
            
    return Panel(table, title="[yellow]Penyimpanan (Storage)", border_style="yellow")

# Variabel global untuk cache suhu di Windows
WIN_TEMP_CACHE = "N/A"
WIN_TEMP_COLOR = "green"

def fetch_win_temp_worker():
    global WIN_TEMP_CACHE, WIN_TEMP_COLOR
    while True:
        try:
            output = subprocess.check_output(
                ["powershell", "-Command", "(Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature).CurrentTemperature"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                text=True
            ).strip()
            
            temp_kelvin_tenths = None
            for line in output.split('\n'):
                if line.strip().isdigit():
                    temp_kelvin_tenths = int(line.strip())
                    break
            
            if temp_kelvin_tenths is not None:
                temp_celsius = (temp_kelvin_tenths / 10.0) - 273.15
                if temp_celsius > 80:
                    WIN_TEMP_COLOR = "red"
                elif temp_celsius > 65:
                    WIN_TEMP_COLOR = "yellow"
                else:
                    WIN_TEMP_COLOR = "green"
                WIN_TEMP_CACHE = f"{temp_celsius:.1f}°C"
        except Exception:
            pass
        time.sleep(3)

if platform.system() == "Windows":
    threading.Thread(target=fetch_win_temp_worker, daemon=True).start()

def get_temp_info():
    table = Table(box=box.SIMPLE, show_header=False, expand=True)
    table.add_column("Komponen")
    table.add_column("Suhu", justify="right")
    
    has_temps = False
    
    # Coba psutil terlebih dahulu (untuk Linux/Mac atau sistem Windows yang terdukung)
    if hasattr(psutil, "sensors_temperatures"):
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        label = entry.label or name
                        
                        color = "green"
                        if entry.current > 80:
                            color = "red"
                        elif entry.current > 65:
                            color = "yellow"
                            
                        table.add_row(f"{label}", f"[{color}]{entry.current}°C[/{color}]")
                        has_temps = True
        except Exception:
            pass
            
    # Fallback ke WMI / PowerShell jika di Windows dan psutil gagal
    if not has_temps and platform.system() == "Windows":
        if WIN_TEMP_CACHE != "N/A":
            table.add_row("Thermal Zone", f"[{WIN_TEMP_COLOR}]{WIN_TEMP_CACHE}[/{WIN_TEMP_COLOR}]")
            has_temps = True
            
    if not has_temps:
        table.add_row("Sensor", "N/A (Butuh Akses Admin / WMI)")
        
    return Panel(table, title="[red]Suhu", border_style="red")

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=8),
        Layout(name="upper", ratio=2),  # Diubah menjadi 2 agar panel atas lebih tinggi
        Layout(name="lower", ratio=1)   # Diubah menjadi 1
    )
    layout["upper"].split_row(
        Layout(name="sys_info", ratio=2),
        Layout(name="cpu", ratio=1),
        Layout(name="ram", ratio=1)
    )
    layout["lower"].split_row(
        Layout(name="disk", ratio=2),
        Layout(name="temp", ratio=1)
    )
    return layout

def update_layout(layout):
    layout["header"].update(get_header())
    layout["sys_info"].update(get_system_info())
    layout["cpu"].update(get_cpu_info())
    layout["ram"].update(get_ram_info())
    layout["disk"].update(get_disk_info())
    layout["temp"].update(get_temp_info())

def show_logo():
    os.system("cls" if os.name == "nt" else "clear")
    console.print("\n" * 3)
    console.print(Align.center(Text(VERAND_LOGO, style="bold cyan")))
    console.print(Align.center(Text("P R O F E S S I O N A L   S Y S T E M   M O N I T O R", style="bold yellow")))
    console.print("\n")
    console.print(Align.center(Text("Akses Diterima. Menginisialisasi sistem...", style="bold green")))
    time.sleep(2.5)

def login_screen():
    # Menjeda sebentar agar terminal buffer tenang
    time.sleep(0.2)
    
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        console.print("\n")
        console.print(Align.center(Text(VERAND_LOGO, style="bold cyan")))
        console.print(Align.center(Text("P R O F E S S I O N A L   S Y S T E M   M O N I T O R", style="bold yellow")))
        console.print("\n")
        console.print(Align.center(Panel.fit("[bold blue]SYS-MONITOR AUTHENTICATION[/bold blue]", border_style="blue")))
        console.print("\n")
        
        # Membersihkan sisa tombol Enter di keyboard buffer (khusus Windows)
        try:
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getch()
        except ImportError:
            pass
            
        console.print("        [bold cyan]Username:[/bold cyan] ", end="")
        
        # Menggunakan input bawaan Python (lebih tahan buffer dibanding console.input)
        try:
            username = input().strip()
        except EOFError:
            username = ""
            
        # Jika kosong (karena ter-skip), ulang ke awal tampilan
        if not username:
            continue
            
        password = getpass.getpass("        \033[1;36mPassword:\033[0m ")
        
        if username.lower() == "verand" and password == "12345":
            show_logo()
            break
        else:
            console.print("\n        [bold red]Akses Ditolak. Username atau Password salah.[/bold red]")
            time.sleep(1.5)

def main():
    login_screen()
    psutil.cpu_percent()
    
    dashboard_layout = make_layout()
    update_layout(dashboard_layout)
    
    # screen=True prevents command prompt overlap, refresh_per_second syncing reduces flicker
    with Live(dashboard_layout, refresh_per_second=2, screen=True) as live:
        try:
            while True:
                time.sleep(0.5)
                update_layout(dashboard_layout)
        except KeyboardInterrupt:
            os.system("cls" if os.name == "nt" else "clear")

if __name__ == "__main__":
    main()
