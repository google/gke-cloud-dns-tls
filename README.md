# Integrate GKE with Cloud DNS and expose workloads using TLS

Instructions in this repository help you [integrating](https://cloud.google.com/kubernetes-engine/docs/how-to/cloud-dns) [GKE](https://cloud.google.com/kubernetes-engine/docs) with [Cloud DNS](https://cloud.google.com/dns/docs) and (optionally) exposing workloads using TLS.

For TLS, sample code and instructions make use of [cert-manager](https://cert-manager.io) and of a custom mutating webhook. This way, TLS certificates are associated to new pods and deployments.

## What you can do with this repository

* Bring up a sample [GKE cluster](https://cloud.google.com/kubernetes-engine/docs)
* Install [cert-manager](https://cert-manager.io)
* Configure [cert-manager](https://cert-manager.io) with a [self-signed CA](https://cert-manager.io/docs/configuration/selfsigned/) and a [ClusterIssuer](https://cert-manager.io/docs/concepts/issuer/)
* Request a [self-signed certificate](https://cert-manager.io/docs/configuration/selfsigned/) for a sample application from the CA just created
* Build and deploy a [custom mutating webhook](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#mutatingadmissionwebhook) to automatically expose TLS certificates through an [Nginx sidecar container](https://www.nginx.com/)
* Deploy a sample application ([app1](app1.yaml)) to demonstrate the functionality

## Quick HowTo

For requirements, jump to the [section below](#requirements).

```shell
export PROJECT=YOUR_PROJECT_ID

# Enable APIs
gcloud services enable container.googleapis.com
gcloud services enable dns.googleapis.com

# Deploy a sample GKE cluster
gcloud beta container clusters create gke-dns-test \
  --cluster-dns clouddns \
  --cluster-dns-scope vpc \
  --cluster-dns-domain gke-dns.test \
  --num-nodes 1 \
  --machine-type n2-standard-4 \
  --enable-ip-alias \
  --max-pods-per-node 110 \
  --network svc-net \
  --subnetwork svc-sub-ew1 \
  --zone europe-west1-b \
  --project ${PROJECT}

# Download the cluster credentials
gcloud container clusters get-credentials gke-dns-test \
	--zone europe-west1-b \
	--project ${PROJECT}
```

You can already deploy the sample application. This is exposed through a headless service, so that the service name is registered in Cloud DNS and reachable from your VPC and other resources connected to it

```shell
kubectl apply -f app1.yaml
```

The application is exposed with NO TLS certificates, unless those get exposed by the application itself.
The next steps are used to integrate [cert-manager](https://cert-manager.io) and automatically expose certificates.

```shell
# Deploy cert-manager
helm repo add jetstack https://charts.jetstack.io

helm repo update

helm install \
  cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.8.0 \
  --set installCRDs=true

# Create a self-signed cluster issuer, a CA and a CA cluster issuer
kubectl apply -f cert-manager.yaml

# Build and push the webhook container
export DOCKER_REPO=MY_DOCKER_REPO
cd webhook-src
docker build -t ${DOCKER_REPO}/webhook-gke-dns-test .
docker push ${DOCKER_REPO}/webhook-gke-dns-test
cd ..

# Request the webhook certificate
kubectl apply -f webhook-certificate.yaml

# Set the value of clientConfig.caBundle in
# webhook-configuration.yaml with the CA certificate base64.
# You can get the value with the following command:
kubectl get secret webhook-tls \
  --output="jsonpath={.data.ca\.crt}"

# Deploy the configmap with the Nginx sidecar containers config
kubectl apply -f webhook-nginx-configmap.yaml

# Make DOCKER_REPO match in webhook-pod.yaml with
# your Docker repository and deploy the webhook
kubectl apply -f webhook-pod.yaml

# Deploy the webhook configuration
kubectl apply -f webhook-configuration.yaml

# Label the default namespace so that the webhook
# automatically injects sidecar containers
kubectl label namespace default tls-injection=true

# Request a sample application certificate
kubectl apply -f app1-certificate.yaml

# Remove (if created before) and deploy the sample app
kubectl apply -f app1.yaml
```

## Requirements

The instructions assume you have:

* A GCP project setup, where you have high privileges (i.e. owner or the minimum permissions to perform the actions in this readme)
* The following tools installed on your machine: [docker](https://docs.docker.com/get-docker/), [gcloud](https://cloud.google.com/sdk/docs/install), [helm](https://helm.sh/docs/intro/install/) and [kubectl](https://kubernetes.io/docs/tasks/tools/)

## Use cases

This is especially useful if you want to expose your GKE services and you don't want/need to configure a [Kubernetes ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/), and neither expose an [Internal Load Balancer](https://cloud.google.com/kubernetes-engine/docs/how-to/internal-load-balancing) for each of the services exposed.

A possible, relevant use case is when you need to expose [GKE](https://cloud.google.com/kubernetes-engine/docs) backends behind [Apigee](https://cloud.google.com/apigee/docs).
[Apigee](https://cloud.google.com/apigee/docs) can take care of L7 routing decisions, while GKE only exposes the services, optionally with end-to-end TLS.

## The Mutating Admission Webhook Configuration

The mutating webhook actually deploys the sidecar in namespaces labeled with `tls-injection=true`. You can modify the default behavior, editing [webhook-configuration.yaml](webhook-configuration.yaml)

## Known Limitations

* When integrating GKE, Cloud DNS uses a default TTL of 10 seconds. If a pod goes down clients may still have the DNS entry in cache and try to connect to the dead pod
* When integrating GKE with Cloud DNS, the number of queries may increase and additional costs may apply

## What's Next

As always, contributions are welcome! Here are few topics that you may be interested in:

* We'll discuss this with the GKE/Cloud DNS/Apigee teams to see if this PoC makes sense and can have follow ups.

* Verify/automate the integration with Apigee

* Integrate alternative sidecar containers reverse proxies (for example [Envoy](https://www.envoyproxy.io/), [Apache HTTPD](https://httpd.apache.org/))

* The [mutating admission webhook](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#mutatingadmissionwebhook) can be modified or extended, thus making it more reliable and augmenting its functions.

* Is there a way to better automate all this?

* Testing (Python unit tests, Terraform, GitHub actions for continuous testing)

## Useful Links

* [GKE and Cloud DNS](https://cloud.google.com/kubernetes-engine/docs/how-to/cloud-dns)
