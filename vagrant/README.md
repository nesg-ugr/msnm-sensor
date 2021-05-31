Descripción
------------

**Vagrant**. En esta sección se detalla la creación del escenario con 3 máquinas virtuales (cliente, servidor y router) desplegando la herramienta MSNM-Sensor en [Docker Hub](https://hub.docker.com/r/eliasgrana34/msnm-sensor)

Vagrant gestiona y automatiza el despliegue de máquinas virtuales operando sobre otros hipervisores de virtualización como VirtualBox. En este caso, lo utilizaremos para desplegar el escenario en cuestión con 3 máquinas virtuales Ubuntu con conexión a través de redes privadas.
Ansible automatiza el despliegue y la ejecución de scripts de manera paralela y centralizada. En este caso lo utilizamos juntamente con vagrant para configurar e instalar las dependencias necesarias en las máquinas virtuales para poder desplegar la herramienta MSNM-Sensor de manera automatizada


Configuración
------------
Para llevar a cabo este despliegue necesitamos tener instalado en el equipo tanto la herramienta Vagrant como Ansible. 

Una vez hecho esto, copiamos los ficheros Vagrantfile y playbook.yml en el mismo directorio.

Despliegue
------------

Para el despliegue del escenario, únicamente es necesario arrancar vagrant con el fichero Vagrantfile en el mismo directorio. Para ello, ejecutamos:

$ vagrant up

