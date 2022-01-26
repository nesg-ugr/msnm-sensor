Description
------------

**Docker**. This section details the creation of the Docker image which includes the MSNM-Sensor tool in a container running Ubuntu 18 and with the necessary dependencies. The tool is installed under the /home/msnm/ path.

* [Docker Hub](https://hub.docker.com/r/eliasgrana34/msnm-sensor)

In version 1 of the Docker Hub the MSNM-Sensor tool is deployed on Python2 while in version 2 the tool is deployed on Python3.


## Installation


#### Requirements

It should be noted that the MSNM-Sensor tool is intended to monitor the host. In our case, since we are testing with Netflow data, we need to install the MSNM-Sensor tool on the host and run the script under the msnm-sensor/scripts/netflow directory:

    $ sudo sh activateNetflow.sh


This generates logs in the /tmp/netflow_captures/ folder by default. When creating the container, we must take into account that we must make a copy (a volume) so that the Netflow logs are stored both on the host and in the container. This is done in the Create a container section


#### How to create an image

Locally and from a computer which has Docker installed we copy the Dockerfile file and from that same directory we create an image corresponding to the Dockerfile using the following command:


    $ docker build -t msnm .

This command creates a Docker image based on the Dockerfile whose name is msnm. To check that it has been created, we use the command:


    $ docker images
<pre>   
  REPOSITORY                                      TAG       IMAGE ID       CREATED         SIZE
  
  eliasgrana34/msnm-sensor  2   1f39514f47ad    3 months ago    891MB
  
  msnm                                            latest    1f39514f47ad   3 months ago    891MB
</pre>

#### How to create a container

Once we have the image created, we can run a docker container based on this image with the following command:

    $ docker run -t -d --cap-add=ALL --privileged --network host -v /tmp/netflow_captures:/tmp/netflow_captures -v /etc/timezone:/etc/timezone:ro -v /etc/localtime:/etc/localtime:ro --name test msnm 
 
 



Where we add the necessary privileges, the host network and copy the netflow captures directory of the host computer (/tmp/netflow_captures) and the time zone of the host computer to avoid synchronization problems.

To check that the container is running we use the docker ps command:

    $ docker ps

|CONTAINER ID|   IMAGE  |   COMMAND   |    CREATED    |     STATUS    |     PORTS  |   NAMES |
| ------------| --------- | ---------- | ------------- | ------------- | ---------- | -------- |
|1db9c4dbd441|   msnm  |    "/bin/bash"  | 4 seconds ago  | Up 2 seconds    |         | test |


#### How to run a container

First method:

We can execute it manually from inside the container. To be able to enter commands from inside the container we execute the following command:

    $ docker exec -it test /bin/bash


Once inside, we execute the msnm script as shown below:

    root@msnm:/home/msnm/msnm-sensor/scripts# ./start_experiment.sh ../examples/scenario_4/



Second method:

We can run it from outside the machine by entering the command directly:

    $ docker exec test bash ./start_experiment.sh ../examples/scenario_4/




