import psutil
import time
import os
import getpass
import platform
import datetime
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

def get_system_info():
    table = Table(box=box.SIMPLE, show_header=False, expand=True)
    table.add_column("Property", style="bold cyan")
    table.add_column("Value", justify="right")
    
    os_name = f"{platform.system()} {platform.release()}"
    arch = platform.machine()
    hostname = platform.node()
    processor = platform.processor()
    
    # Menghitung Uptime
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    uptime_delta = datetime.timedelta(seconds=uptime_seconds)
    uptime_str = str(uptime_delta).split('.')[0] # Format: 0:00:00
    
    table.add_row("OS", os_name)
    table.add_row("Arsitektur", arch)
    table.add_row("Hostname", hostname)
    table.add_row("Uptime", uptime_str)
    
    # Memotong string processor jika terlalu panjang agar tabel tidak rusak
    if len(processor) > 28:
        processor = processor[:25] + "..."
    table.add_row("Prosesor", processor)
    
    return Panel(table, title="[blue]Spesifikasi Sistem", border_style="blue")

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

def get_temp_info():
    table = Table(box=box.SIMPLE, show_header=False, expand=True)
    table.add_column("Komponen")
    table.add_column("Suhu", justify="right")
    
    has_temps = False
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
            
    if not has_temps:
        table.add_row("Sensor", "N/A (Butuh Akses Admin)")
        
    return Panel(table, title="[red]Suhu", border_style="red")

def generate_dashboard():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=8),
        Layout(name="upper", ratio=1),
        Layout(name="lower", ratio=2)
    )
    
    layout["header"].update(get_header())
    
    # Memasukkan Spesifikasi Sistem ke barisan atas bersama CPU dan RAM
    layout["upper"].split_row(
        Layout(get_system_info(), name="sys_info"),
        Layout(get_cpu_info(), name="cpu"),
        Layout(get_ram_info(), name="ram")
    )
    # Memasukkan Penyimpanan dan Suhu ke barisan bawah
    layout["lower"].split_row(
        Layout(get_disk_info(), name="disk", ratio=2),
        Layout(get_temp_info(), name="temp", ratio=1)
    )
    
    return layout

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
    
    with Live(generate_dashboard(), refresh_per_second=2, screen=True) as live:
        try:
            while True:
                time.sleep(0.5)
                live.update(generate_dashboard())
        except KeyboardInterrupt:
            os.system("cls" if os.name == "nt" else "clear")

if __name__ == "__main__":
    main()
