import os

from netmalies.settings import BASE_DIR

# Modify this path accordingly
# Root path
root_path='../examples/'

# Data path
EXAMPLE_ROOT = os.path.join(root_path, 'scenario_4')
MONITORING_ROOT = os.path.join('data', 'monitoring', 'output')
# last GRAPH_SIZE samples to depict in the monitoring graph
GRAPH_SIZE = 100
# Every SYNC_SECONDS the graph will be updated
SYNC_SECONDS = 60
