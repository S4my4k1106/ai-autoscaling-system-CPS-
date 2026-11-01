from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

from entities.models import SensorData, ServerMetrics
from use_cases.prediction import predict

from infrastructure.database import (
    save_metrics,
    save_prediction,
    save_scaling_event,
    save_alert,
    save_sensor_reading,
    get_predictions as db_get_predictions,
    get_scaling_events as db_get_scaling_events,
    get_alerts as db_get_alerts,
    get_dashboard_data as db_get_dashboard_data,
)

from kubernetes import client, config


# ============================================================
# KUBERNETES CONNECTION
# ============================================================

try:
    config.load_incluster_config()
    apps_api = client.AppsV1Api()
except Exception:
    apps_api = None


def scale_api(replicas: int):
    """
    Scale the Kubernetes autoscaling-api deployment.
    """
    if apps_api is None:
        return

    body = {
        "spec": {
            "replicas": replicas
        }
    }

    apps_api.patch_namespaced_deployment_scale(
        name="autoscaling-api",
        namespace="default",
        body=body
    )


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# TEMPORARY IN-MEMORY DATA
# ============================================================
# These are kept for the existing WebSocket/scaling flow.
# Persistent dashboard/history data comes from PostgreSQL.

sensor_readings = []
server_metrics = []
predictions = []
scaling_events = []
alerts = []


# ============================================================
# WEBSOCKET CONNECTION MANAGER
# ============================================================

class ConnectionManager:

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


# ============================================================
# ROOT
# ============================================================

@router.get("/")
def root():
    return {
        "status": "AI Autoscaling API is running"
    }


# ============================================================
# SENSOR INGESTION
# ============================================================

@router.post("/ingest")
def ingest(data: SensorData):

    sensor_readings.append(data.dict())

    save_sensor_reading(data)

    return {
        "status": "received",
        "device_id": data.device_id
    }


# ============================================================
# METRICS + ML + AUTOSCALING
# ============================================================

@router.post("/metrics")
async def receive_metrics(data: ServerMetrics):

    # Store incoming metrics
    server_metrics.append(data.dict())

    save_metrics(data)

    # --------------------------------------------------------
    # ML PREDICTION
    # --------------------------------------------------------

    predicted_memory, predicted_cpu, scale_up, scale_down = predict(
        data.cpu,
        data.network_traffic,
        data.memory
    )

    prediction = {
        "timestamp": data.timestamp,
        "cpu": data.cpu,
        "memory": data.memory,
        "predicted_memory": predicted_memory,
        "predicted_cpu": predicted_cpu,
        "scale_up": scale_up,
        "scale_down": scale_down
    }

    predictions.append(prediction)

    save_prediction(
        data,
        predicted_memory,
        predicted_cpu,
        scale_up,
        scale_down
    )

    # --------------------------------------------------------
    # SCALE UP
    # --------------------------------------------------------

    if scale_up:

        reason = (
            f"predicted_memory={predicted_memory}% "
            f"predicted_cpu={predicted_cpu}%"
        )

        # Tell Kubernetes to run 3 API replicas
        scale_api(3)

        save_scaling_event(
            data.timestamp,
            "scale_up",
            reason
        )

        scaling_events.append({
            "timestamp": data.timestamp,
            "action": "scale_up",
            "reason": reason
        })

    # --------------------------------------------------------
    # SCALE DOWN
    # --------------------------------------------------------

    if scale_down:

        reason = (
            f"predicted_memory={predicted_memory}% "
            f"predicted_cpu={predicted_cpu}%"
        )

        # Tell Kubernetes to run 1 API replica
        scale_api(1)

        save_scaling_event(
            data.timestamp,
            "scale_down",
            reason
        )

        scaling_events.append({
            "timestamp": data.timestamp,
            "action": "scale_down",
            "reason": reason
        })

    # --------------------------------------------------------
    # HIGH CPU ALERT
    # --------------------------------------------------------

    if data.cpu > 90:

        save_alert(
            data.timestamp,
            "HIGH_CPU",
            data.cpu
        )

        alerts.append({
            "timestamp": data.timestamp,
            "type": "HIGH_CPU",
            "value": data.cpu
        })

    # --------------------------------------------------------
    # HIGH MEMORY ALERT
    # --------------------------------------------------------

    if data.memory > 90:

        save_alert(
            data.timestamp,
            "HIGH_MEMORY",
            data.memory
        )

        alerts.append({
            "timestamp": data.timestamp,
            "type": "HIGH_MEMORY",
            "value": data.memory
        })

    # --------------------------------------------------------
    # REAL-TIME WEBSOCKET UPDATE
    # --------------------------------------------------------

    await manager.broadcast(prediction)

    return prediction


# ============================================================
# PREDICTIONS
# ============================================================

@router.get("/predictions")
def predictions_endpoint():

    return {
        "predictions": db_get_predictions(50)
    }


# ============================================================
# SCALING EVENTS
# ============================================================

@router.get("/scaling-events")
def scaling_events_endpoint():

    return {
        "scaling_events": db_get_scaling_events(50)
    }


# ============================================================
# ALERTS
# ============================================================

@router.get("/alerts")
def alerts_endpoint():

    return {
        "alerts": db_get_alerts(50)
    }


# ============================================================
# SENSOR READINGS
# ============================================================

@router.get("/sensor-readings")
def sensor_readings_endpoint():

    return {
        "sensor_readings": sensor_readings[-50:]
    }


# ============================================================
# DASHBOARD DATA
# ============================================================

@router.get("/dashboard-data")
def dashboard_data_endpoint():

    return db_get_dashboard_data()


# ============================================================
# WEBSOCKET
# ============================================================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await manager.connect(websocket)

    try:

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:

        manager.disconnect(websocket)