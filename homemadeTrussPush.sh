#!/bin/bash
set -e

# 1. Generate the Dockerfile context using Truss
echo "🔨 Generating Docker Context with Truss..."
truss image build --target-directory ./model --build 



# ALTERNATIVE: The "Pure Docker" way (Safest for my  Interview Demo)
# truss build --output-directory build_dir
# docker build build_dir -t llava-model:local

# Retag whatever truss built (usually 'baseten/model:latest' or similar)

docker build model -t llava-model:local

echo "Loading Image into Kind..."
kind load docker-image llava-model:local --name baseten-local

echo "Deploying Knative Service..."
kubectl apply -f infra/service.yaml

echo "Waiting for service to become ready..."
kubectl wait --for=condition=Ready ksvc/llava-model --timeout=90s
