previous_value = None
incident_active = False

def detect_incident(metrics):
    global previous_value, incident_active

    current = metrics.get("error_count", 0)

    # First run
    if previous_value is None:
        previous_value = current
        return None

    trend = current - previous_value
    previous_value = current

    # Detect only if rising and not already active
    if current > 5 and trend > 1 and not incident_active:
        incident_active = True
        return {
            "type": "MEMORY_LEAK",
            "severity": "HIGH",
            "current_value": current,
            "trend": trend
        }

    return None