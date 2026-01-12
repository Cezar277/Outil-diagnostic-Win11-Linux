#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System Diagnostics Tool - Compatible Windows/Linux
Auteur: CEZAR277
"""

import platform
import socket
import psutil
import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
import winreg

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def clear_screen():
    """Nettoie l'écran selon l'OS"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_system_info():
    """Récupère les informations système de base"""
    info = {}
    info['hostname'] = socket.gethostname()
    info['os'] = f"{platform.system()} {platform.release()}"
    info['os_version'] = platform.version()
    info['architecture'] = platform.machine()
    info['processor'] = platform.processor()
    
    info['cpu_physical_cores'] = psutil.cpu_count(logical=False)
    info['cpu_total_cores'] = psutil.cpu_count(logical=True)
    info['cpu_freq'] = psutil.cpu_freq().current if psutil.cpu_freq() else "N/A"
    
    mem = psutil.virtual_memory()
    info['ram_total'] = f"{mem.total / (1024**3):.2f} GB"
    info['ram_used'] = f"{mem.used / (1024**3):.2f} GB"
    info['ram_percent'] = f"{mem.percent}%"
    
    disk = psutil.disk_usage('/')
    info['disk_total'] = f"{disk.total / (1024**3):.2f} GB"
    info['disk_used'] = f"{disk.used / (1024**3):.2f} GB"
    info['disk_percent'] = f"{disk.percent}%"
    
    try:
        info['ip_address'] = socket.gethostbyname(socket.gethostname())
    except:
        info['ip_address'] = "N/A"
    
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    info['uptime'] = str(uptime).split('.')[0]
    
    return info

def display_system_info():
    """Affiche les informations système style neofetch"""
    clear_screen()
    info = get_system_info()
    
    print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}     Outil diagnostic v1.0{Colors.ENDC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.ENDC}\n")
    
    if platform.system() == "Windows":
        logo = """
        ████████████████
        ████████████████
        ████  ████  ████
        ████  ████  ████
        ████████████████
        ████████████████
        ████  ████  ████
        ████  ████  ████
        ████████████████
        ████████████████
        """
    else:
        logo = """
           .--.
          |o_o |
          |:_/ |
         //   \ \\
        (|     | )
       /'\_   _/`\\
       \___)=(___/
        """
    
    logo_lines = logo.strip().split('\n')
    
    print(f"{Colors.GREEN}Informations Système:{Colors.ENDC}")
    print(f"{Colors.CYAN}{'─'*60}{Colors.ENDC}")
    
    print(f"{Colors.BOLD}Hostname:{Colors.ENDC} {info['hostname']}")
    print(f"{Colors.BOLD}OS:{Colors.ENDC} {info['os']}")
    print(f"{Colors.BOLD}Architecture:{Colors.ENDC} {info['architecture']}")
    print(f"{Colors.BOLD}Processeur:{Colors.ENDC} {info['processor'][:50]}...")
    print(f"{Colors.BOLD}CPU Cores:{Colors.ENDC} {info['cpu_physical_cores']} physiques / {info['cpu_total_cores']} logiques")
    print(f"{Colors.BOLD}CPU Freq:{Colors.ENDC} {info['cpu_freq']} MHz")
    print(f"{Colors.BOLD}RAM:{Colors.ENDC} {info['ram_used']} / {info['ram_total']} ({info['ram_percent']})")
    print(f"{Colors.BOLD}Disque:{Colors.ENDC} {info['disk_used']} / {info['disk_total']} ({info['disk_percent']})")
    print(f"{Colors.BOLD}IP:{Colors.ENDC} {info['ip_address']}")
    print(f"{Colors.BOLD}Uptime:{Colors.ENDC} {info['uptime']}")
    
    print(f"\n{Colors.CYAN}{'─'*60}{Colors.ENDC}")

def get_smart_attribute(output, attr_name):
    """Helper to parse SMART attribute from smartctl output"""
    lines = output.split('\n')
    for line in lines:
        if attr_name in line:
            parts = line.split()
            if len(parts) > 9:
                return parts[9]
    return "N/A"

def scan_components():
    """Option 1: Scanner les composants et vérifier leur état avec estimation de durée de vie"""
    clear_screen()
    print(f"{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}SCAN DES COMPOSANTS - DIAGNOSTIC AVANCÉ{Colors.ENDC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.ENDC}\n")
    
    results = []
    
    print(f"Test du CPU...")
    cpu_percent = psutil.cpu_percent(interval=2)
    cpu_temp = "N/A"
    cpu_life = "N/A (Durée de vie typique: >10 ans si températures <85°C)"
    
    if hasattr(psutil, 'sensors_temperatures'):
        temps = psutil.sensors_temperatures()
        if temps:
            for name, entries in temps.items():
                for entry in entries:
                    if 'cpu' in name.lower() or 'core' in name.lower():
                        cpu_temp = f"{entry.current}°C"
                        break
    
    cpu_status = "OK" if cpu_percent < 80 and (cpu_temp == "N/A" or float(cpu_temp[:-2]) < 85) else "Charge ou température élevée"
    results.append(f"CPU: {cpu_status} (Usage: {cpu_percent}%, Temp: {cpu_temp}, Durée de vie estimée: {cpu_life})")
    
    print(f"Test de la RAM...")
    mem = psutil.virtual_memory()
    mem_status = "OK" if mem.percent < 85 else "Usage élevé"
    mem_life = "N/A (Pas de métrique standard; durée de vie typique: >10 ans sans erreurs)"
    results.append(f"RAM: {mem_status} (Usage: {mem.percent}%, Durée de vie estimée: {mem_life})")
    
    print(f"Test des disques avec analyse SMART...")
    smart_installed = True
    try:
        subprocess.check_output(['smartctl', '--version'])
    except:
        smart_installed = False
        results.append("smartmontools non installé - Impossible d'estimer durée de vie des disques. Installez via apt/yum ou téléchargez pour Windows.")
    
    if smart_installed:
        for partition in psutil.disk_partitions():
            if partition.mountpoint:
                try:
                    device = partition.device
                    if platform.system() == "Windows":
                        device = r'\\.\PhysicalDrive' + device.replace('\\', '').replace(':', '') 
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_status = "OK" if usage.percent < 90 else "Espace faible"
                    
                    info_output = subprocess.check_output(['smartctl', '-i', device]).decode()
                    health_output = subprocess.check_output(['smartctl', '-H', device]).decode()
                    attr_output = subprocess.check_output(['smartctl', '-A', device]).decode()
                    
                    is_ssd = "Solid State Device" in info_output or "SSD" in info_output
                    health = "OK" if "PASSED" in health_output else "Problème détecté"
                    
                    if is_ssd:
                        wear = get_smart_attribute(attr_output, "Media_Wearout_Indicator") or get_smart_attribute(attr_output, "Wear_Leveling_Count") or get_smart_attribute(attr_output, "Percentage_Used")
                        life_percent = f"{100 - int(wear)}%" if wear != "N/A" and wear.isdigit() else "N/A"
                        disk_life = f"{life_percent} restante (basé sur usure)"
                    else: 
                        reallocated = get_smart_attribute(attr_output, "Reallocated_Sector_Ct")
                        power_hours = get_smart_attribute(attr_output, "Power_On_Hours")
                        disk_life = f"Basé sur erreurs: {reallocated} secteurs réalloués, Heures allumé: {power_hours}. Typique >5 ans si erreurs basses."
                    
                    results.append(f"Disque {partition.device}: {disk_status}, Santé SMART: {health}, Usage: {usage.percent}%, Durée de vie estimée: {disk_life}")
                except Exception as e:
                    results.append(f"Disque {partition.device}: Erreur SMART - {str(e)}")
    else:
        for partition in psutil.disk_partitions():
            if partition.mountpoint:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_status = "OK" if usage.percent < 90 else "Espace faible"
                results.append(f"Disque {partition.device}: {disk_status} (Usage: {usage.percent}%) - Pas d'info durée de vie sans smartmontools")
    
    print(f"🔍 Test réseau...")
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        net_status = "OK"
    except:
        net_status = "Pas de connexion"
    results.append(f"Réseau: {net_status} (Pas de métrique de durée de vie)")
    
    battery = psutil.sensors_battery()
    if battery:
        print(f"Test batterie...")
        bat_status = "OK" if battery.percent > 20 else "Batterie faible"
        charging = "En charge" if battery.power_plugged else "Sur batterie"
        cycles = "N/A"
        life_percent = "N/A"
        
        if platform.system() == "Linux":
            try:
                with open('/sys/class/power_supply/BAT0/cycle_count', 'r') as f:
                    cycles = f.read().strip()
                with open('/sys/class/power_supply/BAT0/charge_full_design', 'r') as f:
                    design = int(f.read().strip())
                with open('/sys/class/power_supply/BAT0/charge_full', 'r') as f:
                    full = int(f.read().strip())
                life_percent = f"{(full / design * 100):.1f}% capacité restante"
            except:
                pass
        elif platform.system() == "Windows":
            cycles = "Installez 'batteryinfo' via pip pour cycles (non supporté nativement)"
        
        results.append(f"Batterie: {bat_status} ({battery.percent}% - {charging}), Cycles: {cycles}, Durée de vie: {life_percent}")
    
    print(f"\n{Colors.GREEN}RÉSULTATS DU DIAGNOSTIC:{Colors.ENDC}")
    print(f"{Colors.CYAN}{'─'*60}{Colors.ENDC}")
    
    for result in results:
        if "OK" in result:
            print(f"{Colors.GREEN}{result}{Colors.ENDC}")
        elif "Danger" in result:
            print(f"{Colors.WARNING}{result}{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}{result}{Colors.ENDC}")
    
    ok_count = sum(1 for r in results if "OK" in r)
    total_count = len(results)
    score = (ok_count / total_count) * 100 if total_count > 0 else 0
    
    print(f"\n{Colors.CYAN}{'─'*60}{Colors.ENDC}")
    if score >= 80:
        print(f"{Colors.GREEN}SCORE GLOBAL: {score:.0f}% - Système en bonne santé!{Colors.ENDC}")
    elif score >= 60:
        print(f"{Colors.WARNING}SCORE GLOBAL: {score:.0f}% - Quelques points d'attention{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}SCORE GLOBAL: {score:.0f}% - Maintenance recommandée{Colors.ENDC}")
    
    input(f"\n{Colors.CYAN}Appuyez sur Entrée pour continuer...{Colors.ENDC}")

def get_windows_license():
    """Option 2: Récupérer la clé de licence Windows"""
    clear_screen()
    print(f"{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}RÉCUPÉRATION CLÉ DE LICENCE WINDOWS{Colors.ENDC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.ENDC}\n")
    
    if platform.system() != "Windows":
        print(f"{Colors.WARNING} Cette fonction n'est disponible que sur Windows!{Colors.ENDC}")
        input(f"\n{Colors.CYAN}Appuyez sur Entrée pour continuer...{Colors.ENDC}")
        return
    
    key = None
    
    try:
        print(f"🔍 Recherche de la clé de licence (WMI)...")
        cmd = 'wmic path softwarelicensingservice get OA3xOriginalProductKey'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line and not 'OA3xOriginalProductKey' in line:
                    potential_key = line.strip()
                    if potential_key and potential_key != '':
                        key = potential_key
                        print(f"\n{Colors.GREEN}✓  Clé trouvée (OEM via WMI):{Colors.ENDC}")
                        print(f"{Colors.BOLD}{Colors.CYAN}{key}{Colors.ENDC}")
                        break
        
        if not key:
            print(f"Tentative alternative via PowerShell...")
            ps_cmd = "(Get-WmiObject -query 'select * from SoftwareLicensingService').OA3xOriginalProductKey"
            result2 = subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, text=True)
            
            potential_key = result2.stdout.strip()
            if potential_key:
                key = potential_key
                print(f"\n{Colors.GREEN}Clé trouvée (OEM via PowerShell):{Colors.ENDC}")
                print(f"{Colors.BOLD}{Colors.CYAN}{key}{Colors.ENDC}")
        
        if not key:
            print(f"Tentative via Registry...")
            reg_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform"
            aReg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            aKey = winreg.OpenKey(aReg, reg_path)
            key = winreg.QueryValueEx(aKey, "BackupProductKeyDefault")[0]
            print(f"\n{Colors.GREEN}Clé trouvée (Registry):{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.CYAN}{key}{Colors.ENDC}")
        
        if key:
            save_to_file = input(f"\nVoulez-vous sauvegarder la clé dans un fichier? (o/n): ")
            if save_to_file.lower() == 'o':
                filename = f"windows_key_{socket.gethostname()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, 'w') as f:
                    f.write(f"Hostname: {socket.gethostname()}\n")
                    f.write(f"Date: {datetime.now()}\n")
                    f.write(f"OS: {platform.system()} {platform.release()}\n")
                    f.write(f"Clé Windows: {key}\n")
                print(f"{Colors.GREEN}Clé sauvegardée dans: {filename}{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠️ Aucune clé trouvée.{Colors.ENDC}")
            print(f"Cela peut arriver si Windows a été installé avec une clé retail ou volume.")
            
    except Exception as e:
        print(f"{Colors.FAIL}Erreur lors de la récupération: {e}{Colors.ENDC}")
        print(f"Assurez-vous d'exécuter le script en tant qu'administrateur.")
    
    input(f"\n{Colors.CYAN}Appuyez sur Entrée pour continuer...{Colors.ENDC}")

def performance_test():
    """Option 3: Test de performance et rapport de santé"""
    clear_screen()
    print(f"{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}TEST DE PERFORMANCE & RAPPORT DE SANTÉ{Colors.ENDC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.ENDC}\n")
    
    report = {}
    
    print(f"Test de performance CPU...")
    start = time.time()
    for i in range(1000000):
        _ = i ** 2
    cpu_time = time.time() - start
    report['cpu_benchmark'] = f"{cpu_time:.3f} secondes"
    
    print(f"Test de vitesse disque...")
    test_file = "test_speed.tmp"
    data = b"0" * (10 * 1024 * 1024) 
    
    start = time.time()
    with open(test_file, 'wb') as f:
        f.write(data)
    write_time = time.time() - start
    write_speed = 10 / write_time
    
    start = time.time()
    with open(test_file, 'rb') as f:
        _ = f.read()
    read_time = time.time() - start
    read_speed = 10 / read_time
    
    os.remove(test_file)
    
    report['disk_write'] = f"{write_speed:.2f} MB/s"
    report['disk_read'] = f"{read_speed:.2f} MB/s"
    
    print(f"Test de latence réseau...")
    try:
        import subprocess
        if platform.system() == "Windows":
            cmd = ["ping", "-n", "4", "8.8.8.8"]
        else:
            cmd = ["ping", "-c", "4", "8.8.8.8"]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if platform.system() == "Windows":
            for line in result.stdout.split('\n'):
                if 'Moyenne' in line or 'Average' in line:
                    latency = line.split('=')[-1].strip()
                    report['network_latency'] = latency
                    break
        else:
            for line in result.stdout.split('\n'):
                if 'avg' in line:
                    latency = line.split('/')[4]
                    report['network_latency'] = f"{latency} ms"
                    break
    except:
        report['network_latency'] = "N/A"
    
    print(f"Analyse des processus...")
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append(proc.info)
        except:
            pass
    
    top_cpu = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:5]
    top_mem = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:5]
    
    print(f"\n{Colors.GREEN}RAPPORT DE PERFORMANCE:{Colors.ENDC}")
    print(f"{Colors.CYAN}{'─'*60}{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Benchmarks:{Colors.ENDC}")
    print(f"  CPU Benchmark: {report['cpu_benchmark']}")
    print(f"  Vitesse écriture disque: {report['disk_write']}")
    print(f"  Vitesse lecture disque: {report['disk_read']}")
    print(f"  Latence réseau: {report.get('network_latency', 'N/A')}")
    
    print(f"\n{Colors.BOLD}Top 5 processus (CPU):{Colors.ENDC}")
    for proc in top_cpu:
        print(f"  {proc['name'][:30]:30} - {proc['cpu_percent']:.1f}%")
    
    print(f"\n{Colors.BOLD}Top 5 processus (RAM):{Colors.ENDC}")
    for proc in top_mem:
        print(f"  {proc['name'][:30]:30} - {proc['memory_percent']:.1f}%")
    
    score = 0
    if cpu_time < 0.5:
        score += 35
    elif cpu_time < 1.0:
        score += 20
    else:
        score += 10
    
    if write_speed > 50:
        score += 35
    elif write_speed > 20:
        score += 20
    else:
        score += 10
    
    if report.get('network_latency') and 'ms' in report['network_latency']:
        try:
            lat = float(report['network_latency'].split()[0])
            if lat < 50:
                score += 30
            elif lat < 100:
                score += 20
            else:
                score += 10
        except:
            score += 15
    else:
        score += 15
    
    print(f"\n{Colors.CYAN}{'─'*60}{Colors.ENDC}")
    if score >= 80:
        print(f"{Colors.GREEN}🚀 SCORE DE PERFORMANCE: {score}/100 - Excellente!{Colors.ENDC}")
    elif score >= 60:
        print(f"{Colors.WARNING}SCORE DE PERFORMANCE: {score}/100 - Bonne{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}SCORE DE PERFORMANCE: {score}/100 - À améliorer{Colors.ENDC}")
    save = input(f"\nVoulez-vous sauvegarder le rapport complet? (o/n): ")
    if save.lower() == 'o':
        filename = f"performance_report_{socket.gethostname()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        full_report = {
            'hostname': socket.gethostname(),
            'date': str(datetime.now()),
            'system': platform.system(),
            'performance': report,
            'score': score,
            'top_cpu_processes': top_cpu,
            'top_mem_processes': top_mem
        }
        
        with open(filename, 'w') as f:
            json.dump(full_report, f, indent=2, default=str)
        
        print(f"{Colors.GREEN}Rapport sauvegardé dans: {filename}{Colors.ENDC}")
    
    input(f"\n{Colors.CYAN}Appuyez sur Entrée pour continuer...{Colors.ENDC}")

def main_menu():
    """Menu principal"""
    while True:
        display_system_info()
        
        print(f"\n{Colors.BOLD}{Colors.GREEN}OPTIONS DISPONIBLES:{Colors.ENDC}")
        print(f"{Colors.CYAN}{'─'*60}{Colors.ENDC}")
        print(f"  {Colors.BOLD}1{Colors.ENDC} - Scanner les composants et vérifier leur état")
        print(f"  {Colors.BOLD}2{Colors.ENDC} - Récupérer la clé de licence Windows")
        print(f"  {Colors.BOLD}3{Colors.ENDC} - Test de performance et rapport de santé")
        print(f"  {Colors.BOLD}4{Colors.ENDC} - Rafraîchir l'affichage")
        print(f"  {Colors.BOLD}0{Colors.ENDC} - Quitter")
        print(f"{Colors.CYAN}{'─'*60}{Colors.ENDC}")
        
        choice = input(f"\n{Colors.BOLD}Votre choix: {Colors.ENDC}")
        
        if choice == '1':
            scan_components()
        elif choice == '2':
            get_windows_license()
        elif choice == '3':
            performance_test()
        elif choice == '4':
            continue
        elif choice == '0':
            print(f"\n{Colors.GREEN}Au revoir!{Colors.ENDC}")
            sys.exit(0)
        else:
            print(f"{Colors.WARNING}Option invalide!{Colors.ENDC}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        required_modules = ['psutil']
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            print(f"{Colors.WARNING}Modules manquants: {', '.join(missing_modules)}{Colors.ENDC}")
            print(f"Installation avec: pip install {' '.join(missing_modules)}")
            install = input("Voulez-vous les installer maintenant? (o/n): ")
            if install.lower() == 'o':
                for module in missing_modules:
                    subprocess.run([sys.executable, '-m', 'pip', 'install', module])
                print(f"{Colors.GREEN}Installation terminée! Relancez le script.{Colors.ENDC}")
            sys.exit(1)
        
        main_menu()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Programme interrompu par l'utilisateur{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.FAIL}Erreur critique: {e}{Colors.ENDC}")
        sys.exit(1)
