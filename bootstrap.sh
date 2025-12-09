#!/bin/bash
set -e

echo " Creating Kind Cluster..."
kind create cluster --config infra/kind-config.yaml --name baseten-local || true

echo " Installing Knative Serving CRDs & Core..."
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.10.0/serving-crds.yaml
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.10.0/serving-core.yaml

echo " Installing Kourier (Ingress)..."
kubectl apply -f https://github.com/knative/net-kourier/releases/download/knative-v1.10.0/kourier.yaml

echo "Configuring Ingress & Domains..."
kubectl patch configmap/config-network \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'

kubectl patch configmap/config-domain \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"nip.io":""}}'

echo " Cluster Ready!"