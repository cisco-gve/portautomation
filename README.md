**Port Automation for ACI**

This web tool allows you to create EPGs, switch profiles, VLAN pools and other ACI constructs to automate the ports deployment using a simple GUI

So far is able to create:

* Tenants
* EPGs
* Bridge domains
* VRFs
* PortChannels profiles
* Access Ports profiles
* Associate ports and port channels with profiles
* VLAN Pools
* Attachable Entities Profiles
* Physical domains

Runs on top of a Django Application and uses Javascript (Angular JS) to create an interactive HTML
application

HTML user interface works better in Chrome and Firefox

Contacts:
* Cesar Obediente ( cobedien@cisco.com )
* Santiago Flores ( sfloresk@cisco.com )

**Container Installation**

You will need docker installed in your machine.

Create an env variable file called envfile with the list of your apics:

```
APICS=https://apic1.cisco.com/,https://apic1.cisco.com/,https://apic1.cisco.com/
```

Execute the following command:

````
docker run -p 8080:8080  -it --env-file envfile --name aciportautomation sfloresk/aciportautomation
````


Go to http://localhost:8080 to access the system

To stop the container:

```
docker rm -f aciportautomation
```


**Source Installation**

As this is a Django application you will need to either integrate the application in your production environment or you can
get it operational in a virtual environment on your computer/server. In the distribution is a requirements.txt file that you can
use to get the package requirements that are needed. The requirements file is located in the root directory of the distribution.

It might make sense for you to create a Python Virtual Environment before installing the requirements file. For information on utilizing
a virtual environment please read http://docs.python-guide.org/en/latest/dev/virtualenvs/. Once you have a virtual environment active then
install the packages in the requirements file.

`(virtualenv) % pip install -r requirements.txt
`

To run the the application execute in the root directory of the distribution:
```
 export APICS=https://apic1.cisco.com/,https://apic1.cisco.com/,https://apic1.cisco.com/
 python manage.py makemigrations
 python manage.py migrate
 python manage.py runserver 0.0.0.0:<PORT>
```

