import pickle
import os
import numpy as np
from kubernetes import client, config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

with open(os.path.join(BASE_DIR, "ml/model_memory.pkl"), "rb") as f:
    memory_model = pickle.load(f)

with open(os.path.join(BASE_DIR, "ml/model_cpu.pkl"), "rb") as f:
    cpu_model = pickle.load(f)

WINDOW = 5
cpu_window = []
memory_window = []

# Load Kubernetes config
try:
    config.load_incluster_config()
    apps_v1 = client.AppsV1Api()
    k8s_available = True
except:
    try:
        config.load_kube_config()
        apps_v1 = client.AppsV1Api()
        k8s_available = True
    except:
        k8s_available = False

def scale_deployment(replicas: int):
    if not k8s_available:
        return
    try:
        apps_v1.patch_namespaced_deployment_scale(
            name="autoscaling-api",
            namespace="default",
            body={"spec": {"replicas": replicas}}
        )
        print(f"Scaled autoscaling-api to {replicas} replicas")
    except Exception as e:
        print(f"Scaling error: {e}")

def predict(cpu, network_traffic, actual_memory):
    # Memory prediction using sliding window
    memory_window.append(actual_memory)
    if len(memory_window) > 3:
        memory_window.pop(0)

    if len(memory_window) == 3:
        features = [
            memory_window[-1],
            memory_window[-2],
            memory_window[-3],
            cpu,
            network_traffic
        ]
        predicted_memory = float(memory_model.predict([features])[0])
        predicted_memory = round(predicted_memory, 2)
    else:
        predicted_memory = actual_memory

    # CPU sliding window prediction
    cpu_window.append(cpu)
    if len(cpu_window) > WINDOW:
        cpu_window.pop(0)

    if len(cpu_window) == WINDOW:
        predicted_cpu = float(cpu_model.predict([cpu_window])[0])
        predicted_cpu = round(predicted_cpu, 2)
    else:
        predicted_cpu = cpu

    # Hybrid scaling decisions
    scale_up = bool(predicted_memory > 80 or predicted_cpu > 80 or actual_memory > 95)
    scale_down = bool(predicted_memory < 20 and predicted_cpu < 20)

    # Execute Kubernetes scaling
    if scale_up:
        scale_deployment(3)
    elif scale_down:
        scale_deployment(1)

    return predicted_memory, predicted_cpu, scale_up, scale_down