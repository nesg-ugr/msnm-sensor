Description
------------

**Vagrant**. This section details the creation of the scenario with 3 virtual machines (client, server and router) by deploying the MSNM-Sensor tool in
 [Docker Hub](https://hub.docker.com/r/eliasgrana34/msnm-sensor)

Vagrant manages and automates the deployment of virtual machines operating over other virtualization hypervisors such as VirtualBox. In this case, we will use it to deploy the scenario with 3 Ubuntu virtual machines with connection through private networks.
Ansible automates the deployment and execution of scripts in a parallel and centralized way. In this case we use it together with vagrant to configure and install the necessary dependencies in the virtual machines to be able to deploy the MSNM-Sensor tool in an automated way.



Requirements
------------
To perform this deployment we need to have both Vagrant and Ansible installed on the computer. 

Once this is done, we copy the Vagrantfile and playbook.yml files into the same directory.

Deployment
------------

To deploy the scenario, it is only necessary to start vagrant with the Vagrantfile file in the same directory. To do this, run:

	$ vagrant up



