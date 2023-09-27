# Installation
MedCATtrainer is a docker-compose packaged Django application.

## Download from Dockerhub
Clone the repo, run the default docker-compose file and default env var: 
```shell
$ git clone https://github.com/CogStack/MedCATtrainer
$ cd MedCATtrainer
$ docker-compose up
```

This will use the pre-built docker images available on DockerHub. If your internal firewall does on permit access to DockerHub, you can build 
directly from source.

## MedCAT v0.x models
If you have MedCAT v0.x models, and want to use the trainer please use the following docker-compose file:
This refences the latest built image for the trainer that is still compatible with [MedCAT v0.x.](https://pypi.org/project/medcat/0.4.0.6/) and under.
```shell
$ docker-compose -f docker-compose-mc0x.yml up
```

## Build images from source
The above commands runs the latest release of MedCATtrainer, if you'd prefer to build the Docker images from source, use
```shell
$ docker-compose -f docker-compose-dev.yml up
```

To change environment variables, such as the exposed host ports and language of spaCy model, use:
```shell
$ cp .env-example .env
# Set local configuration in .env
``` 

## Troubleshooting 
If the build fails with an error code 137, the virtual machine running the docker
daemon does not have enough memory. Increase the allocated memory to containers in the docker daemon
settings CLI or associated docker GUI.

On MAC: https://docs.docker.com/docker-for-mac/#memory

On Windows: https://docs.docker.com/docker-for-windows/#resources

### (Optional) Environment Variables
Environment variables are used to configure the app:

|Parameter|Description|
|---------|-----------|
|MEDCAT_CONFIG_FILE|MedCAT config file as described [here](https://github.com/CogStack/MedCAT/blob/master/medcat/config.py)|
|BEHIND_RP| If you're running MedCATtrainer, use 1, otherwise this defaults to 0 i.e. False|
|MCTRAINER_PORT|The port to run the trainer app on|

Set these and re-run the docker-compose file.

You'll need to `docker stop` the running containers if you have already run the install.
