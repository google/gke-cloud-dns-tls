# Sample Kubernetes Mutating Admission Webhook

The sample webhook is used to automatically add to pods and deployments an Nginx sidecar container that mounts 

To build and push the Docker image

```shell
export DOCKER_REPO=MY_DOCKER_REPO

docker build -t ${DOCKER_REPO}/gke-dns-test .
docker push ${DOCKER_REPO}/gke-dns-test
```

If you need to run a local dev environment and install dependencies

```shell
python3 -m venv ~/gke-dns-test
source ~/gke-dns-test/bin/activate

pip install -r requirements.txt
```

In the root folder, you'll find a [redeploy.sh file](../redeploy.sh) that you can use to quickly re-deploy and test against your GKE cluster the webhook.
