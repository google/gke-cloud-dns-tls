#!/usr/bin/env bash

# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Script to quickly re-build, re-deploy and test the webhook

echo "Building new webhook image and pushing it to Dockerhub."
cd webhook-src &&
docker build -t DOCKER_REPO/webhook-gke-dns . &&
docker push DOCKER_REPO/webhook-gke-dns
cd ..

echo "Cleanup the previous environment."
kubectl delete -f app1.yaml
kubectl delete -f webhook-configuration.yaml
kubectl delete -f webhook-pod.yaml

echo "Applying the new configuration."

kubectl apply -f webhook-pod.yaml
kubectl apply -f webhook-configuration.yaml
