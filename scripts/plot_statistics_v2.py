import re
import os
import yaml
import logging.config
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("TkAgg") 
import matplotlib.pyplot as plt



def to_bool(x):
    return str(x).strip().lower() in ("1","true","t","yes","y","si","sí")


def launch_show_output(staticFiles="./data/sources/local/monitor/parsed", logscale=True, ucld=0.0, uclq=0.0):

    # Logging config (evita el YAMLLoadWarning)
    with open('logging_static.yaml', 'r') as f:
        logging.config.dictConfig(yaml.safe_load(f))

    # Lista de ficheros
    filesOrdered = np.sort(os.listdir(staticFiles))
    logging.debug("Got %s output files ", len(filesOrdered))

    # Quita auxiliares
    filesOrdered = filesOrdered[(filesOrdered != 'stats.log') & (filesOrdered != 'weights.dat')]
    logging.debug("Removed unuseless files. Total files to process: %s ", len(filesOrdered))

    q_values, d_values = [], []

    num_pat = re.compile(r'[-+]?(?:\d*\.\d+|\d+)')  # captura enteros y floats

    for fname in filesOrdered:
        fpath = os.path.join(staticFiles, fname)
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as fh:
                s = fh.read()

            nums = num_pat.findall(s)
            # esperamos al menos: timestamp, UCLq, UCLd, Q, D  -> tomamos los dos últimos (Q y D)
            if len(nums) >= 2:
                q_values.append(float(nums[-2]))
                d_values.append(float(nums[-1]))
            else:
                logging.warning("No numeric data found in %s", fpath)

        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt received. Exiting ...")
            return
        except Exception as e:
            logging.warning("Problem reading %s. ERROR: %s", fpath, e)

    if not q_values or not d_values:
        logging.error("No hay observaciones válidas (q_values/d_values vacíos). Revisa el formato de los .dat.")
        return

    q_range = np.arange(len(q_values))
    d_range = np.arange(len(d_values))

    # --- Plot Q ---
    ax = plt.subplot(2, 1, 1)
    if to_bool(logscale):
        ax.set_yscale("log", nonpositive='clip')
    plt.axhline(y=float(uclq), xmin=0, xmax=1, color='red', linestyle='--')
    plt.bar(q_range, q_values)
    plt.xlabel('Obs')
    plt.ylabel(r'$Q_{1,1}$', fontsize=16)

    # --- Plot D ---
    ax = plt.subplot(2, 1, 2)
    if to_bool(logscale):
        ax.set_yscale("log", nonpositive='clip')
    plt.axhline(y=float(ucld), xmin=0, xmax=1, color='red', linestyle='--')
    plt.bar(d_range, d_values)
    plt.xlabel('Obs')
    plt.ylabel(r'$D_{1,1}$', fontsize=16)

    plt.tight_layout()
    plt.savefig("monitoring.svg")
    plt.savefig("monitoring.pdf")
    plt.show()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 5:
        print("Uso: plot_statistics_v2.py <path_to_data> <logscale> <ucld> <uclq>")
        print('Ejemplo: plot_statistics_v2.py ../data/monitoring/output/ True 9.0 32.0')
        sys.exit(1)

    folder = sys.argv[1]
    logscale = to_bool(sys.argv[2])   # convierte "True/False", "sí/no", etc. a bool
    ucld = float(sys.argv[3])
    uclq = float(sys.argv[4])

    launch_show_output(folder, logscale, ucld, uclq)