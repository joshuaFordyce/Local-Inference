LOCAL BASETEN INFERENCE STACK
- A local reproduction of a serverless ML inference platform using Kind, Knative, and Truss.

 MOTIVATION
 - I built this to reverse-engineer the Baseten stack locally. 

GOALS
- Debug "Cold Starts": 
  - Simulate scale-to-zero latency mechanics using Knative to better understand customer pain points.

- Optimize Constraints: 
  - Experiment with 4-bit quantization to fit Vision-Language Models (VLMs) on constrained hardware.

- Test Concurrency: 
  - Validate ThreadPoolExecutor patterns to prevent the Python GIL from blocking health checks during heavy inference.

ARCHIRECTURE
- Infrastructure: 
  - Kubernetes (Kind) + Knative Serving (KPA).

- Model: 
  - HuggingFaceTB/SmolVLM-256M-Instruct (packaged via Truss).

- Optimization: 
  - NF4 Quantization + bfloat16 compute.
