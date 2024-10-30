import os
import sys
import logging
import traceback
import yaml  # Para cargar el archivo YAML
from datetime import datetime
from msnm.modules.source.source import Source
from msnm.modules.thread.thread import MSNMThread
from msnm.exceptions.msnm_exception import DataSourceError
from msnm.utils import dateutils
import subprocess  # Para ejecutar monitor_v3.py



class MonitorDataSource(Source):
    """
    *MonitorDataSource*. Contiene los métodos básicos para ejecutar `monitor_v3.py`, gestionar y parsear los datos generados.
    """

    def __init__(self, config_path='sensor.yaml'):
        super(MonitorDataSource, self).__init__()
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        """
        Carga el archivo de configuración YAML.
        """
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                logging.debug(f"Configuración cargada: {config}")  # Imprimir configuración cargada
                return config
        except Exception as e:
            raise Exception(f"Error loading configuration file: {str(e)}")

    def parse(self, file_to_parse, file_parsed, **kwargs):
        """
        Parsear los datos generados por monitor_v3.py y guardarlos como un archivo CSV.

        Parameters
        ----------
        file_to_parse: str
            Ruta al archivo log generado para parsear.
        file_parsed: str
            Ruta al archivo CSV de salida parseado.

        Raises
        ------
        DataSourceError
        """

        method_name = "parse()"

        try:
            # Lógica de parsing específica para el archivo generado por monitor_v3.py
            parsed_lines = []
            with open(file_to_parse) as f:
                for line in f:
                    # Procesar cada línea y adaptarla al formato CSV
                    parsed_lines.append(line.strip())  # Ejemplo, modificar según la estructura real

            # Guardar el archivo CSV
            with open(file_parsed, 'w') as f:
                f.write("\n".join(parsed_lines))

        except DataSourceError as dse:
            raise dse
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback, limit=5, file=sys.stdout)
            raise DataSourceError(self, sys.exc_info()[0], method_name)

    def start(self):
        # Overridden from Source
        self._monitorThread = MonitorDataSourceThread(self)
        self._monitorThread.setName("MonitorDataSourceThread")
        self._monitorThread.start()

    def stop(self):
        # Overridden from Source
        self._monitorThread.stop()


class MonitorDataSourceThread(MSNMThread):
    """
    *MonitorDataSourceThread*. Hilo que maneja la ejecución de monitor_v3.py, la recolección de datos y el parseo.

    Attributes
    ----------
    _monitor_instance: MonitorDataSource
        Una instancia de MonitorDataSource
    """

    def __init__(self, monitor_instance):
        super(MonitorDataSourceThread, self).__init__()
        self._monitor_instance = monitor_instance
        self.config = self._monitor_instance.config  # Configuración cargada desde sensor.yaml

    def run(self):
        method_name = "run()"

        try:
            while not self._stopped_event.isSet():
                logging.info("Running monitor data source thread ...")

                # Leer la configuración directamente desde el YAML cargado
                try:
                    script_path = self.config['DataSources']['local']['MonitorDataSource']['script_path']
                    log_folder = self.config['DataSources']['local']['MonitorDataSource']['log_folder']
                    parsed_folder = self.config['DataSources']['local']['MonitorDataSource']['parsed_folder']
                    monitoring_interval = self.config['DataSources']['local']['MonitorDataSource']['monitoring_interval']

                    ts = self.config['GeneralParams']['ts_monitoring_interval']

                except KeyError as e:
                    logging.error(f"Key error accessing configuration: {e}")
                    return  # O manejarlo de otra manera

                # Ejecutar el script monitor_v3.py
                logging.debug(f"Executing monitor_v3.py script at {script_path}")
                process = subprocess.Popen(['python3', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()

                if process.returncode != 0:
                    logging.error(f"Error executing monitor_v3.py: {stderr.decode().strip()}")
                    continue

                # Guardar la salida en un archivo
                monitor_log_file = os.path.join(log_folder, f"monitor_{ts}.log")
                with open(monitor_log_file, 'w') as log_file:
                    log_file.write(stdout.decode().strip())

                # Parsear el archivo generado
                monitor_parsed_file = os.path.join(parsed_folder, f"monitor_{ts}.csv")
                self._monitor_instance.parse(monitor_log_file, monitor_parsed_file)

                # Manejar el archivo CSV generado
                logging.debug(f"Processed and saved parsed data to {monitor_parsed_file}")

                # Esperar antes de la siguiente ejecución
                self._stopped_event.wait(monitoring_interval)

        except DataSourceError as edse:
            logging.error("Error processing monitor data source: %s", edse.get_msg())
            raise edse
        except Exception as e:
            logging.error("General error in monitor data source thread: %s", str(e))
            raise

