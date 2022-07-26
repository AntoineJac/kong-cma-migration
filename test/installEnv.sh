echo -e "This script will install a fresh Kubernetes cluster in Minikube"
echo -e "*** Prerequesites"
echo -e "*** 1. Minikube installed"
echo -e "*** 2. kubectl cli installed on your machine"
echo -e "*** 3. ngrok cli configured"
echo -e "*** 4. docker installed"
echo -e "*** 5. kubectl"


echo "minikube starting"
minikube start


namespaceStatus=$(kubectl get ns kong -o json | jq .status.phase -r)

if [[ $namespaceStatus == "Active" ]]
then
    echo "namespace kong is present"
else
   echo "namespace kong is not present"
   kubectl create -f https://bit.ly/k4k8s
   osascript -e 'tell app "Terminal" to do script "minikube service -n kong kong-proxy --url"'
   sleep 5
   #ps -ef | grep 'ssh -o UserKnownHostsFile'
   #export PROXY_IP=$(minikube service -n kong kong-proxy --url | head -1)
   #echo $PROXY_IP
fi

echo -e "*** 5. test"

eval $(minikube docker-env)

dockerImageHelloApp=$(docker image ls k8_py_sample --format "{{json . }}" | jq .Tag -r)
if [[ $dockerImageHelloApp != "latest" ]]
then
    echo "docker build"
    docker build -t k8_py_sample .
fi

echo "docker image built"

svcHelloApp=$(kubectl get svc hello-service -n kong -o json | jq .metadata.labels.app -r)
if [[ $svcHelloApp != "helloapp" ]]
then
    echo "create deployment"
    kubectl create -f ./config/helloapp-deployment.yaml
fi

echo "deployment is created"

kubectl apply -n kong -f ./config/hello-ingress.yaml


helloServiceIp=$(kubectl get svc hello-service -n kong -o json | jq .status.loadBalancer.ingress | jq -r '.[0]'.ip)

if [[ "$helloServiceIp" == null ]]
then
	osascript -e 'tell app "Terminal" to do script "minikube tunnel"'
fi

while [[ "$helloServiceIp" == null ]]
do
	helloServiceIp=$(kubectl get svc hello-service -n kong -o json | jq .status.loadBalancer.ingress | jq -r '.[0]'.ip)
    echo "wait for Minikube Tunnel to be running test 1/2, please make sure you have entered your password"
    sleep 5
done

while [ $(curl -sL --connect-timeout 3 -w "%{http_code}\n" "http://127.0.0.1" -o /dev/null) == 000 ]
do
    echo "wait for Minikube Tunnel to be running test 2/2, please make sure you have entered your password"
    sleep 5
    ps -ef | grep 'ssh -o UserKnownHostsFile'
done

echo -e "*** 5. please go to http://$helloServiceIp/hello"
#open  http://$helloServiceIp/hello

NGROK_REMOTE_URL="$(curl http://localhost:4040/api/tunnels | jq ".tunnels[0].public_url")"

sleep 5

if test -z "${NGROK_REMOTE_URL}"
then
	osascript -e 'tell app "Terminal" to do script "ngrok http 80"'
	sleep 5
	NGROK_REMOTE_URL="$(curl http://localhost:4040/api/tunnels | jq ".tunnels[0].public_url")"
fi

echo -e "*** 5. Ngrok url is $NGROK_REMOTE_URL"

echo -e "*** 5. End of script"

