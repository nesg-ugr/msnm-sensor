# -*- coding: utf-8 -*-

"""
    :mod:`monitor`
    ===========================================================================
    :synopsis: For monitoring process status
    :author: Roberto Magán Carrión
    :contact: roberto.magan@uca.es, rmagan@ugr.es, robertomagan@gmail.com
    :organization: University of Cádiz, University of Granada
    :project: I2P Crawler
    :since: 0.0.1
"""

import psutil as ps
import datetime
import time
import argparse


def monitoring(interval):
    """

    System and process monitoring. It is monitors process with the desired pid.

    :param pid: int, PID of the process to monitor
    :param interval: int, sample interval in seconds.
    """

    ts = datetime.datetime.now()

    SEP = ","

    head = "ts," \
    	   "s_mem_total," \
           "s_mem_available," \
           "s_mem_used," \
           "s_mem_free," \
           "s_swap_total," \
           "s_swap_used," \
           "s_swap_free," \
           "s_swap_percent," \
           "s_disk_usage.total," \
           "s_disk_usage.used," \
           "s_disk_usage.free," \
           "s_disk_usage.percent," \
           "s_io_counters.read," \
           "s_io_counters.write," \
           "s_io_counters.read_bytes," \
           "s_io_counters.write_bytes," \
           "s_io_counters.read_time," \
           "s_io_counters.write_time," \
           "s_io_counters.read_merged_counts," \
           "s_io_counters.write_merged_counts," \
           "s_io_counters.busy_time," \
           "s_syscalls.ctx_switches," \
           "s_syscalls.interrupts," \
           "s_syscalls.soft_interrupts," \
           "s_syscalls.syscalss," \
           "s_cpu_fan," \
           "s_cpu_percent" + "\n"

    with open("output.csv", "w") as f:
        f.writelines(head)
        f.flush()

        while 1:
            ts = ts + datetime.timedelta(seconds=interval)

            s_mem_info = ps.virtual_memory()
            s_swap_info = ps.swap_memory()
            s_syscalls = ps.cpu_stats()
            s_disk_usage = ps.disk_usage('/')
            s_io_counters = ps.disk_io_counters()
            #s_cpu_fan = ps.sensors_fans()


            to_write = str(ts) + SEP
            to_write += str(s_mem_info.total) + SEP
            to_write += str(s_mem_info.available) + SEP
            to_write += str(s_mem_info.used) + SEP
            to_write += str(s_mem_info.free) + SEP
            to_write += str(s_swap_info.total) + SEP
            to_write += str(s_swap_info.used) + SEP
            to_write += str(s_swap_info.free) + SEP
            to_write += str(s_swap_info.percent) + SEP       
            to_write += str(s_disk_usage.total) + SEP
            to_write += str(s_disk_usage.used) + SEP
            to_write += str(s_disk_usage.free) + SEP
            to_write += str(s_disk_usage.percent) + SEP
            to_write += str(s_io_counters.read_count) + SEP
            to_write += str(s_io_counters.write_count) + SEP
            to_write += str(s_io_counters.read_bytes) + SEP
            to_write += str(s_io_counters.write_bytes) + SEP
            to_write += str(s_io_counters.read_time) + SEP
            to_write += str(s_io_counters.write_time) + SEP
            #to_write += str(s_io_counters.read_merged_count) + SEP
            #to_write += str(s_io_counters.write_merged_count) + SEP
            #to_write += str(s_io_counters.busy_time) + SEP
            to_write += str(s_syscalls.ctx_switches) + SEP
            to_write += str(s_syscalls.interrupts) + SEP
            to_write += str(s_syscalls.soft_interrupts) + SEP
            to_write += str(s_syscalls.syscalls) + SEP
            #to_write += str(s_cpu_fan) + SEP
            to_write += str(ps.cpu_percent()) + "\n"

            f.writelines(to_write)
            f.flush()

            time.sleep(interval)
            

            to_write = ""


if __name__ == '__main__':
    parser = argparse.ArgumentParser()


    parser.add_argument(
        'interval', type=int, help='Sample time to monitor in seconds.'
    )


    args = parser.parse_args()


    monitoring(args.interval)
