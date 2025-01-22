# -*- coding: utf-8 -*-

"""
    :mod:`monitor`
    ===========================================================================
    :synopsis: For monitoring process status
    :author: Juan Manuel Piña Ruiz
    :contact: manupiru@correo.ugr.es, jmanpir@gmail.com
    :organization: University of Granada
    :project: I2P Crawler
    :since: 0.0.1
"""

import psutil as ps
import datetime
import argparse
import schedule
import time
import csv
import os

data_buffer = []


def read_data():
    """
    Read system monitoring data.
    """
    ts = datetime.datetime.now()

    s_mem_info = ps.virtual_memory()
    s_swap_info = ps.swap_memory()
    s_syscalls = ps.cpu_stats()
    s_disk_usage = ps.disk_usage('/')
    s_io_counters = ps.disk_io_counters()

    data = {
        "ts": ts,
        #"s_mem_total": s_mem_info.total,
        "s_mem_available": s_mem_info.available,
        "s_mem_used": s_mem_info.used,
        "s_mem_free": s_mem_info.free,
        #"s_swap_total": s_swap_info.total,
        "s_swap_used": s_swap_info.used,
        "s_swap_free": s_swap_info.free,
        "s_swap_percent": s_swap_info.percent,
        #"s_disk_usage_total": s_disk_usage.total,
        "s_disk_usage_used": s_disk_usage.used,
        "s_disk_usage_free": s_disk_usage.free,
        "s_disk_usage_percent": s_disk_usage.percent,
        "s_io_counters_read": s_io_counters.read_count,
        "s_io_counters_write": s_io_counters.write_count,
        "s_io_counters_read_bytes": s_io_counters.read_bytes,
        "s_io_counters_write_bytes": s_io_counters.write_bytes,
        "s_io_counters_read_time": s_io_counters.read_time,
        "s_io_counters_write_time": s_io_counters.write_time,
        "s_syscalls_ctx_switches": s_syscalls.ctx_switches,
        "s_syscalls_interrupts": s_syscalls.interrupts,
        "s_syscalls_soft_interrupts": s_syscalls.soft_interrupts,
        "s_syscalls_syscalls": s_syscalls.syscalls,
        "s_cpu_percent": ps.cpu_percent()
    }

    data_buffer.append(data)
    #print(f"Datos leídos y almacenados: {ts}")


def generate_csv(output_directory):
    """
    Generate CSV with accumulated system monitoring data.
    """
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(output_directory, f"output_{ts}.csv")

    # head = [
    #  "ts", "s_mem_available", "s_mem_used", "s_mem_free",
    #  "s_swap_used", "s_swap_free", "s_swap_percent",
    #   "s_disk_usage_used", "s_disk_usage_free", "s_disk_usage_percent",
    #   "s_io_counters_read", "s_io_counters_write", "s_io_counters_read_bytes", "s_io_counters_write_bytes",
    #   "s_io_counters_read_time", "s_io_counters_write_time", "s_syscalls_ctx_switches", "s_syscalls_interrupts",
    #   "s_syscalls_soft_interrupts", "s_syscalls_syscalls", "s_cpu_percent"
    #]

    with open(filename, "w", newline='') as f:
        writer = csv.writer(f)

        for entry in data_buffer:
            writer.writerow(entry.values())  # Escribir solo los valores del diccionario

    print(f"Fichero {filename} generado.")
    data_buffer.clear()


def start_monitoring(interval, output_directory):
    """
    Start the monitoring process with the specified interval.

    :param interval: int, sample interval in minutes.
    """
    schedule.every(60).seconds.do(read_data) #TODO Que venga el dato del generalparams
    schedule.every(interval).minutes.do(generate_csv, output_directory)

    print(f"Monitoring iniciado. Leyendo datos cada 60 segundo y generando fichero CSV cada {interval} minuto(s).")

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    DEFAULT_OUTPUT_DIRECTORY = "./data/sources/local/monitor/raw/" #TODO Que esta ruta venga del sensor.yaml y no este hardocedada

    parser = argparse.ArgumentParser()
    parser.add_argument('interval', type=int, help='Sample time to monitor in minutes.')
    parser.add_argument('--output_directory', type=str, default=DEFAULT_OUTPUT_DIRECTORY,
                        help='Directory to save the CSV files (default: ../sources/data/local/monitor).')
    args = parser.parse_args()

    # Ensure the output directory exists
    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)

    start_monitoring(args.interval, args.output_directory)
