import os
import sys
import requests
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

# =====================================================================
# 1. ENVIRONMENT & ANTI-FREEZE CONFIGURATION
# =====================================================================
# CRITICAL: Disable CrewAI telemetry tracking to prevent startup hangs 
# on local network environments.
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

# Verify API token availability
if not os.environ.get("GOOGLE_API_KEY"):
    print("\n❌ CRITICAL ERROR: GOOGLE_API_KEY is missing from this session!")
    print("Please run this command first: $env:GOOGLE_API_KEY='your_key'")
    sys.exit(1)

GEMINI_MODEL = "gemini/gemini-2.5-flash"


# =====================================================================
# 2. LIGHTWEIGHT RE-MAPPED METRIC & HEALING TOOLS
# =====================================================================
@tool("Scrape Prometheus Metrics")
def check_prometheus_targets() -> str:
    """Scrapes the live Prometheus server targets list to check system health states."""
    try:
        response = requests.get("http://localhost:9090/api/v1/targets", timeout=4)
        if response.status_code == 200:
            targets = response.json().get("data", {}).get("activeTargets", [])
            health_report = []
            for t in targets:
                # Isolate the core container endpoint key name
                url = t.get("scrapeUrl", "")
                state = t.get("health", "unknown")
                health_report.append(f"Target Endpoint: {url} -> Health State: {state}")
            return "\n".join(health_report)
    except Exception as e:
        return f"Prometheus connection error: {e}"


@tool("Trigger Service Restart Remediation")
def execute_remediation(service_name: str) -> str:
    """Dispatches an immediate API reboot payload directly to the background chaos supervisor daemon."""
    try:
        # Map incoming variants smoothly to standard container names
        clean_name = service_name.replace("-service", "_service").strip()
        
        response = requests.post(
            "http://127.0.0.1:8099/inject", 
            json={"action": "restart", "service_name": clean_name},
            timeout=5
        )
        return response.json().get("message", "Restart command issued.")
    except Exception as e:
        return f"Could not bind to chaos daemon on port 8099: {e}"


# =====================================================================
# 3. AUTOMATION SWARM LAYER
# =====================================================================
monitor_agent = Agent(
    role="Infrastructure Health Analyst",
    goal="Identify down, missing, or unhealthy microservices immediately from logs.",
    backstory="An automated monitor specialized in evaluating raw Prometheus system target matrices.",
    tools=[check_prometheus_targets],
    verbose=True,
    llm=GEMINI_MODEL
)

sre_agent = Agent(
    role="Site Reliability Engineer",
    goal="Issue targeted recovery actions to bring systems back online automatically.",
    backstory="An autonomous recovery script designed to parse operational incidents and fire container restarts.",
    tools=[execute_remediation],
    verbose=True,
    llm=GEMINI_MODEL
)

scouting_task = Task(
    description="Check the live system targets. Identify if any microservice endpoints show a status of 'down'.",
    expected_output="Provide a short list identifying which service endpoints are active vs which are down.",
    agent=monitor_agent
)

recovery_task = Task(
    description=(
        "Analyze the list from the monitor agent. If any service is offline, trigger your remediation tool "
        "to 'restart' it using its correct name identifier (like 'payments_service'). If everything is healthy, do nothing."
    ),
    expected_output="An execution log verification detailing if a recovery action was triggered.",
    agent=sre_agent
)

sentinel_swarm = Crew(
    agents=[monitor_agent, sre_agent],
    tasks=[scouting_task, recovery_task],
    process=Process.sequential
)

if __name__ == "__main__":
    print("\n🤖 [SENTINELOPS CORE] Launching Multi-Agent Self-Healing Engine...")
    result = sentinel_swarm.kickoff()
    print("\n" + "="*50)
    print("SWARM ACTION RESOLUTION LOG:")
    print(result)
    print("="*50)