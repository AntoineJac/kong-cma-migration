# Kong KIC Minikube quick start up

## KDF Repository Overview

This repository contains a code assets to quickly start up the KIC inside a Minikube environment.
A simple ingress rule is present using the cors-plugin-dev and a pre-kong-plugin.


## Prerequesites

For most of the sections outline below the engagement model with the customer will
consist of the following steps:

- Minikube installed on your machine
  - https://minikube.sigs.k8s.io/docs/start/
- Kubectl cli installed
  - https://kubernetes.io/docs/tasks/tools/
- Docker and Docker desktop installed
  - https://docs.docker.com/engine/install/
- Ngrok installed and configured
  - https://ngrok.com/docs/getting-started


## Installation

1 - Reach the git directory with the shell script:

	$ cd PATH/KongSamples/KIC_Minikube_Setup 

2 - Run the shell script:

	$ ./installEnv.sh


## Reach the localhost proxy

	$ curl --location --request GET 'http://127.0.0.1:80/hello' \
	  --header 'X-TEST-ID: helloTestId'


### Access the resource on the web with Ngrok

The script will generate a Minikube cluster and expose your localhost server running on your local machine to the internet with Ngrok reverse proxy.
After the script has finished running you will obtain a Ngrok url that you can then reach on the web:

	$ curl --location --request GET 'http://[NGROK_REMOTE_URL]/hello' \
	  --header 'X-TEST-ID: helloTestId'


### Edit the kubernest Ingress rule

The script will use the yaml config file ```config/hello-ingress.yaml``` to expose the ```hello-service``` service on the ```/hello``` path
Feel free to test your new config by editing or copying the file and running:

	$ kubectl apply -n kong -f ./config/hello-ingress.yaml