import argparse
import json
import csv
import os
import psutil
import time
from tabulate import tabulate

def collect_system_info():
    # System Information
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    disk_usage = [psutil.disk_usage(part.mountpoint) for part in psutil.disk_partitions()]
    processes = sorted(psutil.process_iter(attrs=['pid', 'name', 'cpu_percent']),
                       key=lambda p: p.info['cpu_percent'],
                       reverse=True)[:5]
    
    return {
        'cpu_usage': cpu_usage,
        'memory': {
            'total': memory_info.total,
            'used': memory_info.used,
            'free': memory_info.available
        },
        'disk': [
            {
                'device': part.mountpoint,
                'total': usage.total,
                'used': usage.used,
                'free': usage.free
            } for part, usage in zip(psutil.disk_partitions(), disk_usage)
        ],
        'top_processes': [
            {
                'pid': proc.info['pid'],
                'name': proc.info['name'],
                'cpu_percent': proc.info['cpu_percent']
            } for proc in processes
        ]
    }

def check_alerts(system_info):
    alerts = []
    if system_info['cpu_usage'] > 80:
        alerts.append("Warning: CPU usage exceeded 80%!")
    if system_info['memory']['used'] / system_info['memory']['total'] > 0.75:
        alerts.append("Warning: Memory usage exceeded 75%!")
    for disk in system_info['disk']:
        if disk['used'] / disk['total'] > 0.90:
            alerts.append(f"Warning: Disk space on {disk['device']} exceeded 90%!")
    return alerts

def write_report(system_info, format, output_file):
    if format == 'text':
        with open(output_file, 'w') as file:
            file.write("System Performance Report\n")
            file.write(tabulate([
                ['CPU Usage', f"{system_info['cpu_usage']}%"],
                ['Memory Usage', f"Total: {system_info['memory']['total']}, Used: {system_info['memory']['used']}, Free: {system_info['memory']['free']}"],
                ['Disk Usage', '\n'.join([f"{disk['device']}: Total {disk['total']}, Used {disk['used']}, Free {disk['free']}" for disk in system_info['disk']])]
            ], headers=['Metric', 'Value']))
    elif format == 'json':
        with open(output_file, 'w') as file:
            json.dump(system_info, file, indent=4)
    elif format == 'csv':
        with open(output_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['CPU Usage', f"{system_info['cpu_usage']}%"])
            writer.writerow(['Memory Usage', f"Total: {system_info['memory']['total']}, Used: {system_info['memory']['used']}, Free: {system_info['memory']['free']}"])
            for disk in system_info['disk']:
                writer.writerow([f"Disk {disk['device']}", f"Total {disk['total']}, Used {disk['used']}, Free {disk['free']}"])

def main():
    parser = argparse.ArgumentParser(description="System Performance Monitor")
    parser.add_argument('--interval', type=int, default=10, help='Monitoring interval in seconds')
    parser.add_argument('--format', choices=['text', 'json', 'csv'], default='text', help='Output file format')
    parser.add_argument('--output', default='system_report', help='Output file name (without extension)')
    args = parser.parse_args()

    try:
        while True:
            system_info = collect_system_info()
            alerts = check_alerts(system_info)
            
            if alerts:
                print("\n".join(alerts))
            
            output_file = f"{args.output}.{args.format}"
            write_report(system_info, args.format, output_file)
            print(f"Report written to {output_file}")
            
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Monitoring stopped.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
