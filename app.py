import streamlit as st
import requests
import json
import time

# =====================================================================
# 1. PAGE SETUP & THEME CONSTRAINTS
# =====================================================================
st.set_page_config(
    page_title="SentinelOps | Autonomous SRE Control",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom injection for a clean corporate dark theme
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div.stButton > button:first-child {
        background-color: #ff4b4b; color: white; border-radius: 6px; width: 100%;
    }
    .status-card {
        padding: 15px; border-radius: 8px; margin-bottom: 10px; font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ SentinelOps Control Center")
st.subheader("Autonomous Multi-Agent Infrastructure Self-Healing Dashboard")
st.markdown("---")

# =====================================================================
# 2. TELEMETRY FETCHERS (CONNECTING TO YOUR BACKEND)
# =====================================================================
def get_service_status():
    """Pings Prometheus API to parse target states natively."""
    try:
        response = requests.get("http://localhost:9090/api/v1/targets", timeout=2)
        if response.status_code == 200:
            targets = response.json().get("data", {}).get("activeTargets", [])
            states = {}
            for t in targets:
                labels = t.get("labels", {})
                # Extract clean instance or job names
                name = labels.get("job", "unknown")
                if "service" in name or "infra" in name:
                    states[name] = t.get("health", "unknown").upper()
            return states
    except:
        return {"auth_service": "UNKNOWN", "orders_service": "UNKNOWN", "payments_service": "UNKNOWN"}

# =====================================================================
# 3. GRAPHICAL USER INTERFACE LAYOUT
# =====================================================================
col1, col2 = st.columns([1, 2])

# --- COLUMN 1: LIVE METRICS & CHAOS INJECTION ---
with col1:
    st.header("🌐 System Telemetry")
    statuses = get_service_status()
    
    # Display individual status cards dynamically
    for service, state in statuses.items():
        color = "#155724" if state == "UP" else "#721c24" if state == "DOWN" else "#383d41"
        text_color = "#d4edda" if state == "UP" else "#f8d7da" if state == "DOWN" else "#e2e3e5"
        
        st.markdown(
            f'<div class="status-card" style="background-color: {color}; color: {text_color};">'
            f'{service.upper()} ──> Status: {state}'
            f'</div>', 
            unsafe_allow_html=True
        )
        
    st.markdown("---")
    st.header("💥 Chaos Controller")
    st.caption("Inject structural errors into the active cluster to force agent engagement.")
    
    target_to_kill = st.selectbox("Select Target Microservice", ["payments_service", "orders_service", "auth_service"])
    
    if st.button(f"🔥 Terminate {target_to_kill.upper()}"):
        with st.spinner("Injecting fault..."):
            try:
                res = requests.post(
                    "http://127.0.0.1:8099/inject", 
                    json={"action": "kill", "service_name": target_to_kill}
                )
                st.error(f"Chaos Incident Triggered: {res.json().get('message')}")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to communicate with Chaos Server: {e}")

# --- COLUMN 2: AUTONOMOUS AGENT OBSERVABILITY ---
with col2:
    st.header("🤖 Autonomous Swarm Console")
    st.caption("Real-time monitoring trace loops and self-healing action results.")
    
    log_container = st.empty()
    
    # Create an active button loop to trigger an automated optimization cycle
    if st.button("⚡ Dispatch Sentinel Swarm Audit Loop", type="primary"):
        st.info("Swarm deploying onto target infrastructure...")
        
        # Diverts standard terminal output into Streamlit code boxes
        with st.status("Agents Analyzing Logs...", expanded=True) as status_box:
            try:
                # Runs the exact core swarm loop via your script
                import subprocess
                process = subprocess.Popen(
                    ["python", "agent_swarm.py"], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    text=True
                )
                
                output_accumulator = ""
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    output_accumulator += line
                    log_container.code(output_accumulator, language="bash")
                
                status_box.update(label="Self-Healing Operation Concluded!", state="complete")
                st.success("Infrastructure Audit Completed Successfully.")
                time.sleep(1.5)
                st.rerun()
                
            except Exception as e:
                st.error(f"Swarm execution failed: {e}")