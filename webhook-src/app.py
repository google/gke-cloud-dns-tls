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

import base64
import copy
import http
import json
import random

import jsonpatch
from flask import Flask, jsonify, request

import traceback

app = Flask(__name__)


@app.route("/mutate", methods=["POST"])
def mutate():
  spec = request.json["request"]["object"]
  modified_spec = copy.deepcopy(spec)

  try:
    # Happens when a pod is created as a consequence of a deployment creation.
    # We don't want to modify pods that have already been modified
    # (through deployments insertions)
    if not "generateName" in spec["metadata"]:

      base_struct = {}
      if spec["kind"] == "Pod":
        base_struct = modified_spec["spec"]
      else:
        base_struct = modified_spec["spec"]["template"]["spec"]

      # Add volumes
      tls_certs = {}
      tls_certs["name"] = "tls-certs"
      tls_certs["secret"] = {}
      tls_certs["secret"]["secretName"] = spec["metadata"]["name"] + "-tls"

      tls_config = {}
      tls_config["name"] = "tls-config"
      tls_config["configMap"] = {}
      tls_config["configMap"]["name"] = "tls-config"

      if "volumes" in base_struct:
        existing_volumes = base_struct["volumes"]
        existing_volumes.extend([tls_certs, tls_config])
      else:
        base_struct["volumes"] = [tls_certs, tls_config]

      # Add sidecar container
      tls_certs = {}
      tls_certs["name"] = "tls-certs"
      tls_certs["mountPath"] = "/etc/nginx/tls-certs"
      tls_certs["readOnly"] = True

      tls_config = {}
      tls_config["name"] = "tls-config"
      tls_config["mountPath"] = "/etc/nginx"
      tls_config["readOnly"] = True

      new_container = {}
      new_container["name"] = "tls"
      new_container["image"] = "nginx"
      new_container["volumeMounts"] = [tls_certs, tls_config]

      base_struct["containers"].extend([new_container])

  except KeyError as e:
    app.logger.error(traceback.format_exc())
    modified_spec = copy.deepcopy(spec)

  patch = jsonpatch.JsonPatch.from_diff(spec, modified_spec)
  return jsonify(
    {
      "apiVersion": "admission.k8s.io/v1",
      "kind": "AdmissionReview",
      "response": {
        "allowed": True,
        "uid": request.json["request"]["uid"],
        "patch": base64.b64encode(str(patch).encode()).decode(),
        "patchType": "JSONPatch",
      }
    }
  )


@app.route("/healthz", methods=["GET"])
def health():
  return ("", http.HTTPStatus.NO_CONTENT)


if __name__ == "__main__":
  app.run(host="0.0.0.0", debug=False)
