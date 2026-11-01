import time
import os
import requests
from datetime import datetime


filepath = "data/metrics.csv"



API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")


BASELINE_SECONDS = 30
RAMP_UP_SECONDS = 15
HIGH_LOAD_SECONDS = 30
RAMP_DOWN_SECONDS = 15
RECOVERY_SECONDS = 30


LOW_CPU = 8.0
LOW_MEMORY = 10.0
LOW_NETWORK = 0.2


HIGH_CPU = 95.0
HIGH_MEMORY = 95.0
HIGH_NETWORK = 35.0




if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
    with open(filepath, "w") as f:
        f.write("timestamp,cpu,memory,network_traffic\n")


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def smooth_step(current, target, rate=0.20):
    return current + (target - current) * rate


def send_metrics(timestamp, cpu, memory, network):
    try:
        response = requests.post(
            f"{API_URL}/metrics",
            json={
                "timestamp": timestamp,
                "cpu": round(cpu, 2),
                "memory": round(memory, 2),
                "network_traffic": round(network, 4)
            },
            timeout=5
        )

        response.raise_for_status()

        
        result = response.json()

        print(
            f"  → predicted_memory={result.get('predicted_memory')}% "
            f"| predicted_cpu={result.get('predicted_cpu')}% "
            f"| scale_up={result.get('scale_up')} "
            f"| scale_down={result.get('scale_down')}"
        )

    except requests.RequestException as e:
        print(f"API error: {e}")


def save_metrics(timestamp, cpu, memory, network):
    with open(filepath, "a") as f:
        f.write(
            f"{timestamp},{cpu:.2f},{memory:.2f},{network:.4f}\n"
        )




cpu = LOW_CPU
memory = LOW_MEMORY
network = LOW_NETWORK


print("=" * 70)
print("CONTROLLED SYNTHETIC WORKLOAD GENERATOR")
print("=" * 70)
print(f"API: {API_URL}")
print()
print("Experiment cycle:")
print("  1. BASELINE    → low load")
print("  2. RAMP UP     → gradually increasing load")
print("  3. HIGH LOAD   → sustained high load")
print("  4. RAMP DOWN   → gradually decreasing load")
print("  5. RECOVERY    → low load")
print("=" * 70)


phase_start = time.time()
phase = "BASELINE"


while True:

    now = time.time()
    elapsed = now - phase_start

  

    if phase == "BASELINE" and elapsed >= BASELINE_SECONDS:

        phase = "RAMP_UP"
        phase_start = now

        print("\n>>> PHASE: RAMP UP <<<")

    elif phase == "RAMP_UP" and elapsed >= RAMP_UP_SECONDS:

        phase = "HIGH_LOAD"
        phase_start = now

        print("\n>>> PHASE: HIGH LOAD <<<")

    elif phase == "HIGH_LOAD" and elapsed >= HIGH_LOAD_SECONDS:

        phase = "RAMP_DOWN"
        phase_start = now

        print("\n>>> PHASE: RAMP DOWN <<<")

    elif phase == "RAMP_DOWN" and elapsed >= RAMP_DOWN_SECONDS:

        phase = "RECOVERY"
        phase_start = now

        print("\n>>> PHASE: RECOVERY <<<")

    elif phase == "RECOVERY" and elapsed >= RECOVERY_SECONDS:

        phase = "BASELINE"
        phase_start = now

        print("\n>>> PHASE: BASELINE <<<")



    if phase == "BASELINE":

        # Keep workload very low.
        cpu = smooth_step(cpu, LOW_CPU, 0.30)
        memory = smooth_step(memory, LOW_MEMORY, 0.30)
        network = smooth_step(network, LOW_NETWORK, 0.30)


    elif phase == "RAMP_UP":

        progress = elapsed / RAMP_UP_SECONDS
        progress = clamp(progress, 0.0, 1.0)

        target_cpu = LOW_CPU + (
            HIGH_CPU - LOW_CPU
        ) * progress

        target_memory = LOW_MEMORY + (
            HIGH_MEMORY - LOW_MEMORY
        ) * progress

        target_network = LOW_NETWORK + (
            HIGH_NETWORK - LOW_NETWORK
        ) * progress

        cpu = smooth_step(cpu, target_cpu, 0.35)
        memory = smooth_step(memory, target_memory, 0.35)
        network = smooth_step(network, target_network, 0.35)


    elif phase == "HIGH_LOAD":

      
        cpu = smooth_step(cpu, HIGH_CPU, 0.35)
        memory = smooth_step(memory, HIGH_MEMORY, 0.35)
        network = smooth_step(network, HIGH_NETWORK, 0.35)


    elif phase == "RAMP_DOWN":

        progress = elapsed / RAMP_DOWN_SECONDS
        progress = clamp(progress, 0.0, 1.0)

        target_cpu = HIGH_CPU - (
            HIGH_CPU - LOW_CPU
        ) * progress

        target_memory = HIGH_MEMORY - (
            HIGH_MEMORY - LOW_MEMORY
        ) * progress

        target_network = HIGH_NETWORK - (
            HIGH_NETWORK - LOW_NETWORK
        ) * progress

        cpu = smooth_step(cpu, target_cpu, 0.35)
        memory = smooth_step(memory, target_memory, 0.35)
        network = smooth_step(network, target_network, 0.35)


    elif phase == "RECOVERY":

        
        cpu = smooth_step(cpu, LOW_CPU, 0.30)
        memory = smooth_step(memory, LOW_MEMORY, 0.30)
        network = smooth_step(network, LOW_NETWORK, 0.30)


    import random

    cpu += random.uniform(-0.5, 0.5)
    memory += random.uniform(-0.5, 0.5)
    network += random.uniform(-0.03, 0.03)


    cpu = clamp(cpu, 0.0, 100.0)
    memory = clamp(memory, 0.0, 100.0)
    network = max(0.0, network)

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cpu_r = round(cpu, 2)
    memory_r = round(memory, 2)
    network_r = round(network, 4)


    print(
        f"[{timestamp}] "
        f"{phase:<10} | "
        f"CPU={cpu_r:6.2f}% | "
        f"MEM={memory_r:6.2f}% | "
        f"NET={network_r:7.4f} MB"
    )


  

    save_metrics(
        timestamp,
        cpu_r,
        memory_r,
        network_r
    )

    send_metrics(
        timestamp,
        cpu_r,
        memory_r,
        network_r
    )


    time.sleep(1)