"""
Control — Closed-Loop Control Module
Evaluates telemetry *during* an active irrigation cycle.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from backend.utils.logger import logger
from backend.config.settings import get_settings

settings = get_settings()

def evaluate_mid_cycle(
    zone_state: Dict[str, Any],
    current_moisture: float,
    soil_type: str = "loam",
    grace_period_minutes: int = 15
) -> Dict[str, Any]:
    """
    Evaluates telemetry received while a valve is actively open.
    Returns dictates on whether to 'stop' early or abort due to physical failure.
    """
    target_moisture = float(zone_state.get("target_moisture_max") or 80.0)
    
    # 1. EARLY STOP LOGIC (Goal Reached)
    if current_moisture >= target_moisture:
        logger.info(f"[control_loop] Target moisture reached ({current_moisture}% >= {target_moisture}%). Triggering early stop.")
        return {
            "action": "early_stop",
            "reason": "target_reached",
            "confidence": 1.0
        }
    
    valve_start_time = zone_state.get("last_irrigation_at")
    baseline_moisture = zone_state.get("moisture_at_irrigation_start")
    
    if not valve_start_time or baseline_moisture is None:
        return {"action": "continue", "confidence": 1.0}

    # Ensure timezone awareness for elapsed calculation
    now = datetime.now(timezone.utc)
    if hasattr(valve_start_time, "tzinfo") and valve_start_time.tzinfo is None:
        valve_start_time = valve_start_time.replace(tzinfo=timezone.utc)
        
    elapsed_minutes = (now - valve_start_time).total_seconds() / 60.0

    # 2. FLOW ANOMALY DETECTION (Delivery Rate)
    if elapsed_minutes < grace_period_minutes:
        return {"action": "continue", "confidence": 1.0, "reason": "grace_period"}

    actual_gain = current_moisture - float(baseline_moisture)
    expected_minimum_gain = (elapsed_minutes / 15.0) * 0.5

    if actual_gain < expected_minimum_gain:
        confidence = max(0.1, 1.0 - (expected_minimum_gain - max(0.0, actual_gain)))
        
        # If it's critically failing (e.g. 0 gain after 30 mins) -> abort
        if elapsed_minutes > 30 and actual_gain <= 0:
            logger.error(f"[control_loop] FLOW FAILURE: Valve open {elapsed_minutes:.1f}m but gain is {actual_gain}%. Aborting.")
            return {
                "action": "abort_flow_failure",
                "reason": "mid_cycle_flow_issue",
                "confidence": 0.1
            }
        
        return {"action": "continue", "confidence": round(confidence, 2), "reason": "low_flow_rate"}

    return {"action": "continue", "confidence": 1.0, "reason": "flow_optimal"}
