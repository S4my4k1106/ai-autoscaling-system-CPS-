import requests
import threading
import time

API = "http://localhost:8000"

def hammer_api():
    while True:
        try:
            requests.post(f"{API}/metrics", json={
                "timestamp": "2026-08-30 10:00:00",
                "cpu": 85.0,
                "memory": 96.0,
                "network_traffic": 50.0
            })
        except:
            pass

def cpu_stress():
    while True:
        x = 0
        for i in range(10000000):
            x += i

print("Stress test running... Press Ctrl+C to stop")

threads = []
for i in range(20):
    t = threading.Thread(target=hammer_api)
    t.daemon = True
    threads.append(t)

cpu_thread = threading.Thread(target=cpu_stress)
cpu_thread.daemon = True
threads.append(cpu_thread)

for t in threads:
    t.start()

time.sleep(120)
print("Done!")