import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'msnm', 'modules', 'source')))
from msnm.modules.source.MonitorDataSource import MonitorDataSource, DataSourceError

# Configuración básica de logging para visualizar la salida en consola
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')



def main():
    try:
        # Ruta del archivo sensor.yaml
        config_path = 'config/sensor.yaml'

        # Ruta correcta del archivo de configuración
        monitor_data_source = MonitorDataSource(config_path=config_path)

        # Hilo de monitoreo
        logging.info("Iniciando el monitoreo con MonitorDataSource...")
        monitor_data_source.start()

        # Detener el monitoreo después de un breve período de prueba
        input("Presione Enter para detener el monitoreo...")
        monitor_data_source.stop()
        logging.info("Monitoreo detenido.")


    except DataSourceError as e:
        logging.error(f"DataSourceError: {e}")
    except Exception as e:
        logging.error(f"Error inesperado: {e}")


if __name__ == "__main__":
    main()
