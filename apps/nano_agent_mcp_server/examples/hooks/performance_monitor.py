#!/usr/bin/env python3
"""
Example hook: Performance monitoring

This hook monitors performance of agent executions:
- Tracks execution times
- Monitors token usage
- Alerts on slow operations
- Generates performance reports
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Read JSON input from stdin
input_data = json.loads(sys.stdin.read())

# Extract event details
event = input_data.get("event", "")
execution_time = input_data.get("execution_time")
token_usage = input_data.get("token_usage", {})
model = input_data.get("model", "")
provider = input_data.get("provider", "")

# Performance thresholds
SLOW_EXECUTION_THRESHOLD = 30.0  # seconds
HIGH_TOKEN_THRESHOLD = 10000

# Create metrics directory
metrics_dir = Path.home() / ".nano-cli" / "metrics"
metrics_dir.mkdir(parents=True, exist_ok=True)

def log_performance_metrics():
    """Log performance metrics to file."""
    metrics_file = metrics_dir / "performance.jsonl"
    
    metric = {
        "timestamp": input_data.get("timestamp"),
        "event": event,
        "model": model,
        "provider": provider,
        "execution_time": execution_time,
        "token_usage": token_usage
    }
    
    with open(metrics_file, "a") as f:
        f.write(json.dumps(metric) + "\n")

def check_performance_issues():
    """Check for performance issues and alert if needed."""
    alerts = []
    
    # Check execution time
    if execution_time and execution_time > SLOW_EXECUTION_THRESHOLD:
        alerts.append(f"SLOW: Execution took {execution_time:.2f}s (threshold: {SLOW_EXECUTION_THRESHOLD}s)")
    
    # Check token usage
    total_tokens = token_usage.get("total_tokens", 0)
    if total_tokens > HIGH_TOKEN_THRESHOLD:
        alerts.append(f"HIGH_TOKENS: Used {total_tokens} tokens (threshold: {HIGH_TOKEN_THRESHOLD})")
    
    # Log alerts
    if alerts:
        alert_file = metrics_dir / "alerts.log"
        with open(alert_file, "a") as f:
            timestamp = input_data.get("timestamp", datetime.now().isoformat())
            for alert in alerts:
                f.write(f"[{timestamp}] {alert}\n")
                print(f"PERFORMANCE ALERT: {alert}", file=sys.stderr)

# Handle different events
if event == "post_agent_complete":
    log_performance_metrics()
    check_performance_issues()
    
    # Generate daily summary if needed
    today = datetime.now().date()
    summary_file = metrics_dir / f"summary_{today}.json"
    
    if not summary_file.exists():
        # Create daily summary
        summary = {
            "date": str(today),
            "total_executions": 0,
            "total_time": 0.0,
            "total_tokens": 0,
            "models_used": set()
        }
        
        # Read all metrics for today
        metrics_file = metrics_dir / "performance.jsonl"
        if metrics_file.exists():
            with open(metrics_file, "r") as f:
                for line in f:
                    try:
                        metric = json.loads(line)
                        metric_date = metric.get("timestamp", "").split("T")[0]
                        if metric_date == str(today):
                            summary["total_executions"] += 1
                            summary["total_time"] += metric.get("execution_time", 0)
                            summary["total_tokens"] += metric.get("token_usage", {}).get("total_tokens", 0)
                            if metric.get("model"):
                                summary["models_used"].add(metric["model"])
                    except:
                        pass
        
        # Convert set to list for JSON serialization
        summary["models_used"] = list(summary["models_used"])
        
        # Save summary
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

elif event == "agent_error":
    # Log errors for analysis
    error_file = metrics_dir / "errors.log"
    with open(error_file, "a") as f:
        timestamp = input_data.get("timestamp", datetime.now().isoformat())
        error = input_data.get("error", "Unknown error")
        f.write(f"[{timestamp}] {model}/{provider}: {error}\n")

# Always exit 0 to not block execution
sys.exit(0)