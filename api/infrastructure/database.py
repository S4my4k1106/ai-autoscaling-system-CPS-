import os

import psycopg2
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


def save_metrics(data):
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO server_metrics
            (timestamp, cpu, memory, network_traffic)
            VALUES (%s, %s, %s, %s)
        """, (
            data.timestamp,
            data.cpu,
            data.memory,
            data.network_traffic
        ))

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"DB error: {e}")


def save_prediction(data, predicted_memory, predicted_cpu, scale_up, scale_down):
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO predictions
            (
                timestamp,
                cpu,
                memory,
                predicted_memory,
                predicted_cpu,
                scale_up,
                scale_down
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data.timestamp,
            data.cpu,
            data.memory,
            predicted_memory,
            predicted_cpu,
            scale_up,
            scale_down
        ))

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"DB error: {e}")


def save_scaling_event(timestamp, action, reason):
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO scaling_events
            (timestamp, action, reason)
            VALUES (%s, %s, %s)
        """, (
            timestamp,
            action,
            reason
        ))

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"DB error: {e}")


def save_alert(timestamp, alert_type, value):
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO alerts
            (timestamp, type, value)
            VALUES (%s, %s, %s)
        """, (
            timestamp,
            alert_type,
            value
        ))

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"DB error: {e}")


def save_sensor_reading(data):
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO sensor_readings
            (
                device_id,
                timestamp,
                temperature,
                humidity,
                co2,
                pm25,
                pm10,
                tvoc,
                co,
                light,
                motion,
                occupancy
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.device_id,
            data.timestamp,
            data.temperature,
            data.humidity,
            data.co2,
            data.pm25,
            data.pm10,
            data.tvoc,
            data.co,
            data.light,
            data.motion,
            data.occupancy
        ))

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"DB error: {e}")



def get_predictions(limit=50):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            timestamp,
            cpu,
            memory,
            predicted_memory,
            predicted_cpu,
            scale_up,
            scale_down
        FROM predictions
        ORDER BY timestamp DESC
        LIMIT %s
    """, (limit,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    rows.reverse()

    return [
        {
            "timestamp": row[0].isoformat()
            if hasattr(row[0], "isoformat")
            else str(row[0]),
            "cpu": float(row[1]),
            "memory": float(row[2]),
            "predicted_memory": float(row[3]),
            "predicted_cpu": float(row[4])
            if row[4] is not None else 0,
            "scale_up": bool(row[5]),
            "scale_down": bool(row[6])
        }
        for row in rows
    ]


def get_scaling_events(limit=50):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            timestamp,
            action,
            reason
        FROM scaling_events
        ORDER BY timestamp DESC
        LIMIT %s
    """, (limit,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    rows.reverse()

    return [
        {
            "timestamp": row[0].isoformat()
            if hasattr(row[0], "isoformat")
            else str(row[0]),
            "action": row[1],
            "reason": row[2]
        }
        for row in rows
    ]


def get_alerts(limit=50):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            timestamp,
            type,
            value
        FROM alerts
        ORDER BY timestamp DESC
        LIMIT %s
    """, (limit,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    rows.reverse()

    return [
        {
            "timestamp": row[0].isoformat()
            if hasattr(row[0], "isoformat")
            else str(row[0]),
            "type": row[1],
            "value": float(row[2])
        }
        for row in rows
    ]


def get_dashboard_data():
    conn = get_db()
    cur = conn.cursor()

    # Latest metrics
    cur.execute("""
        SELECT
            timestamp,
            cpu,
            memory,
            network_traffic
        FROM server_metrics
        ORDER BY id DESC
        LIMIT 1
    """)

    metric = cur.fetchone()

    # Latest prediction
    cur.execute("""
        SELECT
            timestamp,
            cpu,
            memory,
            predicted_memory,
            predicted_cpu,
            scale_up,
            scale_down
        FROM predictions
        ORDER BY id DESC
        LIMIT 1
    """)

    prediction = cur.fetchone()

    # Counts
    cur.execute("SELECT COUNT(*) FROM scaling_events")
    total_scaling_events = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM alerts")
    total_alerts = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM sensor_readings")
    total_sensor_readings = cur.fetchone()[0]

    cur.close()
    conn.close()

    latest_metrics = None

    if metric:
        latest_metrics = {
            "timestamp": metric[0].isoformat()
            if hasattr(metric[0], "isoformat")
            else str(metric[0]),
            "cpu": float(metric[1]),
            "memory": float(metric[2]),
            "network_traffic": float(metric[3])
        }

    latest_prediction = None

    if prediction:
        latest_prediction = {
            "timestamp": prediction[0].isoformat()
            if hasattr(prediction[0], "isoformat")
            else str(prediction[0]),
            "cpu": float(prediction[1]),
            "memory": float(prediction[2]),
            "predicted_memory": float(prediction[3]),
            "predicted_cpu": float(prediction[4])
            if prediction[4] is not None else 0,
            "scale_up": bool(prediction[5]),
            "scale_down": bool(prediction[6])
        }

    return {
        "latest_metrics": latest_metrics,
        "latest_prediction": latest_prediction,
        "total_scaling_events": total_scaling_events,
        "total_alerts": total_alerts,
        "total_sensor_readings": total_sensor_readings
    }