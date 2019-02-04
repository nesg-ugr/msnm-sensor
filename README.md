Description
------------

**MSNMSensor** (Multivariate Statistical Network Monitoring Sensor) shows the practical suitability of the approaches found in [PCA-MSNM](https://www.sciencedirect.com/science/article/pii/S0167404816300116) and in [Hierarchical PCA-MSNM](http://ieeexplore.ieee.org/document/7823895/) works. The first one present the MSNM approach and new multivariate statistical methodology for network anomaly detection while the second one proposes uses the previous one in a hierarchical and structured network systems. The main idea behind these works, is the use of multivariate statistical techniques to generate useful information in the form of two statistics. Such a light information comes from lower to higher levels in a network hierarchy. This way, the root sensor (for example, a border router) received all the statistical information being able to compute its own statistics (Q,D). By inspecting this statistics, a security analyst can determine if anomalous event are happening when some of the statistic values are above certain control limits.

![MSNMSensor](blocks.png "MSNM Sensor functional blocks")

**MSNMSensor** is conceived to be extremely scalable and aseptic because just two parameters are sent among levels or devices in the monitored network or system. Additionally, the MSNMSensor is able to manage multiple and heterogeneous type data sources at each monitored devices thanks to the [FCParser (Feature as a Counter Parser)](https://github.com/josecamachop/FCParser)

![MSNMSensor working in levels](hierarchy.png "MSNM Sensor working all togeter")

## Installation

#### Requirements

MSNSensor runs with python 2.7 Also, the following dependencies has to be installed.

  * numpy >= 1.14
  * scipy >=1.0
  * pyyaml >= 3.12
  * IPy >= 0.83
  * pandas >= 0.22
  * watchdog >= 0.8.3
  * [FCParser (Feature as a Counter Parser)](https://github.com/josecamachop/FCParser)

#### How to install

Creating a python execution environment is, probably the better way to run the application. So I recommend you to create one
before doing the requeriments installation. Anaconda environment can help you and, if you decide to use it, run the following
commands:

    $ conda create -n py27 python=2.7
    $ conda activate py27

Running the previous command will install everything needed.

	(py27) $ pip install -r requirements.txt
	
#### How to run an example

Please see instructions at [examples](examples/README.md)


## License
GPL v3

Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
Everyone is permitted to copy and distribute verbatim copies
of this license document, but changing it is not allowed
