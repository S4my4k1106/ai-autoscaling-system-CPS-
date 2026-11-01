import { useState, useEffect, useRef } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, AreaChart, Area
} from "recharts";
import axios from "axios";

const API = "http://localhost:8000";
const WS_URL = "ws://127.0.0.1:8000/ws";

const colors = {
  bg: "#f8fafc",
  card: "#ffffff",
  border: "#e2e8f0",
  text: "#0f172a",
  muted: "#94a3b8",
  blue: "#3b82f6",
  purple: "#8b5cf6",
  green: "#10b981",
  orange: "#f59e0b",
  red: "#ef4444",
};

export default function App() {
  const [predictions, setPredictions] = useState([]);
  const [dashboardData, setDashboardData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [scalingEvents, setScalingEvents] = useState([]);
  const [connected, setConnected] = useState(false);
  const ws = useRef(null);

 const fetchAll = () => {
  axios.get(`${API}/predictions`)
    .then(res => setPredictions(res.data.predictions.slice(-20)));

  axios.get(`${API}/dashboard-data`)
    .then(res => {
      setDashboardData(prev => ({
        ...res.data,
        latest_metrics: prev?.latest_metrics ?? res.data.latest_metrics,
        latest_prediction: prev?.latest_prediction ?? res.data.latest_prediction
      }));
    });

  axios.get(`${API}/alerts`)
    .then(res => setAlerts(res.data.alerts.slice(-5)));

  axios.get(`${API}/scaling-events`)
    .then(res => setScalingEvents(res.data.scaling_events.slice(-5)));
};
  useEffect(() => { fetchAll(); }, []);
  useEffect(() => {
    const interval = setInterval(fetchAll, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    try {
      ws.current = new WebSocket(WS_URL);
      ws.current.onopen = () => setConnected(true);
      ws.current.onclose = () => setConnected(false);
      ws.current.onerror = () => setConnected(false);
      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setPredictions(prev => [...prev.slice(-19), data]);
        setDashboardData(prev => prev ? {
          ...prev,
          latest_prediction: data,
          latest_metrics: { cpu: data.cpu, memory: data.memory }
        } : null);
      };
    } catch(e) { console.error(e); }
    return () => ws.current?.close();
  }, []);

  const cpu = dashboardData?.latest_metrics?.cpu ?? 0;
  const memory = dashboardData?.latest_metrics?.memory ?? 0;
  const predMemory = dashboardData?.latest_prediction?.predicted_memory ?? 0;
  const predCpu = dashboardData?.latest_prediction?.predicted_cpu ?? 0;
  const scaleUp = dashboardData?.latest_prediction?.scale_up;
  const scaleDown = dashboardData?.latest_prediction?.scale_down;

  return (
    <div style={{ backgroundColor: colors.bg, minHeight: "100vh", fontFamily: "'Inter', 'Segoe UI', sans-serif" }}>

      {/* Navbar */}
      <div style={{ backgroundColor: colors.card, borderBottom: `1px solid ${colors.border}`, padding: "0 32px", display: "flex", alignItems: "center", justifyContent: "space-between", height: "64px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ width: "32px", height: "32px", backgroundColor: colors.blue, borderRadius: "8px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "16px" }}></div>
          <div>
            <div style={{ fontWeight: "700", fontSize: "15px", color: colors.text }}>AI Autoscaling System</div>
            <div style={{ fontSize: "11px", color: colors.muted }}>CPS Cloud Framework</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: connected ? colors.green : colors.orange }} />
          <span style={{ fontSize: "13px", color: colors.muted }}>{connected ? "Live" : "Polling"}</span>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ padding: "32px", maxWidth: "1400px", margin: "0 auto" }}>

        {/* Page Title */}
        <div style={{ marginBottom: "32px" }}>
          <h1 style={{ fontSize: "24px", fontWeight: "700", color: colors.text, margin: 0 }}>Dashboard</h1>
          <p style={{ color: colors.muted, fontSize: "14px", marginTop: "4px" }}>Real-time resource monitoring and predictive autoscaling</p>
        </div>

        {/* Metric Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "20px", marginBottom: "28px" }}>
          <MetricCard title="Current CPU" value={`${cpu}%`} sub="Live usage" color={colors.blue} bar={cpu} />
          <MetricCard title="Current Memory" value={`${memory}%`} sub="Live usage" color={colors.purple} bar={memory} />
          <MetricCard title="Predicted Memory" value={`${predMemory}%`} sub="ML forecast" color={colors.green} bar={predMemory} />
          <MetricCard title="Predicted CPU" value={`${predCpu}%`} sub="ML forecast" color={colors.orange} bar={predCpu} />
        </div>

        {/* Scaling Decision Banner */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "20px", marginBottom: "28px" }}>
          <ScaleCard label="Scale Up" active={scaleUp} icon="⬆️" activeColor={colors.green} />
          <ScaleCard label="Scale Down" active={scaleDown} icon="⬇️" activeColor={colors.blue} />
        </div>

        {/* Charts */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", marginBottom: "28px" }}>
          <ChartCard title="Memory Usage" subtitle="Actual vs Predicted">
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={predictions}>
                <defs>
                  <linearGradient id="memActual" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={colors.purple} stopOpacity={0.15} />
                    <stop offset="95%" stopColor={colors.purple} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="memPred" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={colors.green} stopOpacity={0.15} />
                    <stop offset="95%" stopColor={colors.green} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                <XAxis dataKey="timestamp" tick={{ fontSize: 10, fill: colors.muted }} tickFormatter={(v) => v.slice(11, 19)} />
                <YAxis tick={{ fontSize: 10, fill: colors.muted }} domain={[0, 100]} />
                <Tooltip contentStyle={{ backgroundColor: colors.card, border: `1px solid ${colors.border}`, borderRadius: "8px", fontSize: "12px" }} />
                <Legend iconSize={10} wrapperStyle={{ fontSize: "12px" }} />
                <Area type="monotone" dataKey="memory" stroke={colors.purple} fill="url(#memActual)" name="Actual" strokeWidth={2} dot={false} />
                <Area type="monotone" dataKey="predicted_memory" stroke={colors.green} fill="url(#memPred)" name="Predicted" strokeWidth={2} dot={false} strokeDasharray="5 5" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="CPU Usage" subtitle="Actual vs Predicted">
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={predictions}>
                <defs>
                  <linearGradient id="cpuActual" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={colors.blue} stopOpacity={0.15} />
                    <stop offset="95%" stopColor={colors.blue} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="cpuPred" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={colors.orange} stopOpacity={0.15} />
                    <stop offset="95%" stopColor={colors.orange} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                <XAxis dataKey="timestamp" tick={{ fontSize: 10, fill: colors.muted }} tickFormatter={(v) => v.slice(11, 19)} />
                <YAxis tick={{ fontSize: 10, fill: colors.muted }} domain={[0, 100]} />
                <Tooltip contentStyle={{ backgroundColor: colors.card, border: `1px solid ${colors.border}`, borderRadius: "8px", fontSize: "12px" }} />
                <Legend iconSize={10} wrapperStyle={{ fontSize: "12px" }} />
                <Area type="monotone" dataKey="cpu" stroke={colors.blue} fill="url(#cpuActual)" name="Actual" strokeWidth={2} dot={false} />
                <Area type="monotone" dataKey="predicted_cpu" stroke={colors.orange} fill="url(#cpuPred)" name="Predicted" strokeWidth={2} dot={false} strokeDasharray="5 5" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Bottom Row */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "20px" }}>

          {/* Scaling Events */}
          <ChartCard title="Scaling Events" subtitle="Recent autoscaling actions">
            {scalingEvents.length === 0 ?
              <Empty text="No scaling events yet" /> :
              scalingEvents.map((e, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 0", borderBottom: `1px solid ${colors.border}` }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span>{e.action === "scale_up" ? "⬆️" : "⬇️"}</span>
                    <span style={{ fontSize: "13px", fontWeight: "600", color: e.action === "scale_up" ? colors.green : colors.blue }}>{e.action}</span>
                  </div>
                  <span style={{ fontSize: "11px", color: colors.muted }}>{e.timestamp?.slice(11, 19)}</span>
                </div>
              ))
            }
          </ChartCard>

          {/* Alerts */}
          <ChartCard title="Alerts" subtitle="Anomaly detections">
            {alerts.length === 0 ?
              <Empty text="No alerts" /> :
              alerts.map((a, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 0", borderBottom: `1px solid ${colors.border}` }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span>🚨</span>
                    <span style={{ fontSize: "13px", fontWeight: "600", color: colors.red }}>{a.type}</span>
                  </div>
                  <span style={{ fontSize: "12px", color: colors.orange, fontWeight: "600" }}>{a.value}%</span>
                </div>
              ))
            }
          </ChartCard>

          {/* Summary */}
          <ChartCard title="Summary" subtitle="System overview">
            <SummaryRow label="Total Scaling Events" value={dashboardData?.total_scaling_events ?? 0} color={colors.blue} />
            <SummaryRow label="Total Alerts" value={dashboardData?.total_alerts ?? 0} color={colors.red} />
            <SummaryRow label="Sensor Readings" value={dashboardData?.total_sensor_readings ?? 0} color={colors.green} />
            <SummaryRow label="Memory Model R²" value="0.90" color={colors.purple} />
            <SummaryRow label="CPU Model R²" value="0.62" color={colors.orange} />
          </ChartCard>

        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, sub, color, bar }) {
  return (
    <div style={{ backgroundColor: colors.card, border: `1px solid ${colors.border}`, borderRadius: "12px", padding: "20px" }}>
      <div style={{ fontSize: "12px", color: colors.muted, marginBottom: "8px", fontWeight: "500" }}>{title}</div>
      <div style={{ fontSize: "32px", fontWeight: "700", color: colors.text, marginBottom: "4px" }}>{value}</div>
      <div style={{ fontSize: "11px", color: colors.muted, marginBottom: "12px" }}>{sub}</div>
      <div style={{ height: "4px", backgroundColor: colors.border, borderRadius: "2px" }}>
        <div style={{ height: "4px", backgroundColor: color, borderRadius: "2px", width: `${Math.min(bar, 100)}%`, transition: "width 0.5s ease" }} />
      </div>
    </div>
  );
}

function ScaleCard({ label, active, icon, activeColor }) {
  return (
    <div style={{
      backgroundColor: active ? `${activeColor}10` : colors.card,
      border: `1px solid ${active ? activeColor : colors.border}`,
      borderRadius: "12px", padding: "20px",
      display: "flex", alignItems: "center", justifyContent: "space-between",
      transition: "all 0.3s ease"
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <span style={{ fontSize: "24px" }}>{icon}</span>
        <div>
          <div style={{ fontSize: "13px", color: colors.muted }}>Autoscaling Decision</div>
          <div style={{ fontSize: "18px", fontWeight: "700", color: colors.text }}>{label}</div>
        </div>
      </div>
      <div style={{
        padding: "6px 16px", borderRadius: "20px", fontSize: "13px", fontWeight: "600",
        backgroundColor: active ? activeColor : colors.border,
        color: active ? "white" : colors.muted
      }}>
        {active ? "ACTIVE" : "IDLE"}
      </div>
    </div>
  );
}

function ChartCard({ title, subtitle, children }) {
  return (
    <div style={{ backgroundColor: colors.card, border: `1px solid ${colors.border}`, borderRadius: "12px", padding: "20px" }}>
      <div style={{ marginBottom: "16px" }}>
        <div style={{ fontSize: "14px", fontWeight: "600", color: colors.text }}>{title}</div>
        <div style={{ fontSize: "12px", color: colors.muted }}>{subtitle}</div>
      </div>
      {children}
    </div>
  );
}

function SummaryRow({ label, value, color }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: `1px solid ${colors.border}` }}>
      <span style={{ fontSize: "13px", color: colors.muted }}>{label}</span>
      <span style={{ fontSize: "14px", fontWeight: "700", color }}>{value}</span>
    </div>
  );
}

function Empty({ text }) {
  return <p style={{ color: colors.muted, fontSize: "13px", textAlign: "center", padding: "20px 0" }}>{text}</p>;
}