Descripción
------------

**Docker**. En esta sección se detalla la creación de la imagen de Docker la cual incluye la herramienta MSNM-Sensor en un contenedor ejecutando Ubuntu 18 y con las dependencias necesarias. La herramienta se instala bajo la ruta /home/msnm/

* [Docker Hub](https://hub.docker.com/r/eliasgrana34/msnm-sensor)

En la versión 1 la herramienta MSNM-Sensor está ejecutándose en Python2 mientras que en la versión 2 la herramienta está desplegada sobre Python3.


Preinstalación
------------
Es necesario tener en cuenta que la herramienta MSNM-Sensor está pensada para monitorizar al equipo host. En nuestro caso, como las pruebas las estamos realizando con los datos de Netflow, necesitamos que en el equipo host se instale la herramienta MSNM-Sensor y se ejecute el script bajo el directorio msnm-sensor/scripts/netflow:

$ sudo sh activateNetflow.sh

Esto genera logs en el fichero /tmp/netflow_captures/ por defecto. En el momento de crear el contenedor, debemos tener en cuenta que debemos realizar una copia (un volumen) para que los logs de Netflow se almacenen tanto en el equipo host como en contenedor. Esto se realiza en el paso de Ejecución



Instalación
------------

De manera local y desde un equipo el cual tenga instalado Docker copiamos el fichero Dockerfile y desde ese mismo directorio creamos una imagen correspondiente al Dockerfile mediante el siguiente comando:

docker build -t msnm .

Este comando crea una imagen Docker basado en el Dockerfile cuyo nombre va a ser msnm. Para comprobar que se ha creado, utilizamos el comando:
$ docker images
REPOSITORY                       TAG       IMAGE ID       CREATED         SIZE
eliasgrana34/msnm-sensor         2         1f39514f47ad   2 months ago    891MB
msnm                             latest    1f39514f47ad   2 months ago    891MB



Ejecución
------------
Una vez que tenemos la imagen creada, podemos ejecutar un contenedor de docker basado en esta imagen con el siguiente comando:

$ docker run -t -d --cap-add=ALL --privileged --network host -v /tmp/netflow_captures:/tmp/netflow_captures -v /etc/timezone:/etc/timezone:ro -v /etc/localtime:/etc/localtime:ro --name test msnm

En donde le añadimos los privilegios necesarios, la red del host y copiamos el directorio de las capturas de netflow del equipo host (/tmp/netflow_captures) y la zona horaria del equipo host para evitar problemas de sincronización.

Para comprobar que el contenedor está ejecutándose utilizamos el comando docker ps:

$ docker ps

|CONTAINER ID|   IMAGE  |   COMMAND   |    CREATED    |     STATUS    |     PORTS  |   NAMES |
| ------------| --------- | ---------- | ------------- | ------------- | ---------- | -------- |
|1db9c4dbd441|   msnm  |    "/bin/bash"  | 4 seconds ago  | Up 2 seconds    |         | test |

Puesta en marcha
------------

Primer método:

Podemos ejecutarlo de manera manual desde el interior del contenedor. Para poder introducir comandos desde el interior del contenedor ejecutamos el siguiente comando:

$ docker exec -it test /bin/bash

Una vez dentro, ejecutamos el script de msnm tal como se muestra a continuación:

root@msnm:/home/msnm/msnm-sensor/scripts# ./start_experiment.sh ../examples/scenario_4/

Segundo método:

Podemos ejecutarlo desde el exterior de la máquina introduciendo el comando directamente:

docker exec test bash ./start_experiment.sh ../examples/scenario_4/


