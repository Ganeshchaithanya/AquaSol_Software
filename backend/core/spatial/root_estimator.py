"""
Core Spatial — Root-Zone Estimator
Calculates estimated root moisture based on surface soil measurements,
temperature constraints, and depth mismatches.
"""
import math
from typing import Dict, Any

def detect_depth_mismatch(sensor_depth_cm: int, root_depth_cm: int) -> bool:
    """Flags if the sensor is too shallow to assess the primary root zone."""
    if root_depth_cm <= 0:
        return False
    return sensor_depth_cm < (0.3 * root_depth_cm)


def estimate_root_moisture(
    surface_moisture: float, 
    soil_type: str, 
    temp_celsius: float,
    humidity_pct: float
) -> float:
    """
    Transforms surface reading into root-zone estimation.
    Applies Vapor Pressure Deficit (VPD) evaporative decay and dynamic soil infiltration limits.
    """
    soil_key = soil_type.lower().replace(" ", "_")
    
    # Dynamic Soil Attenuation
    # Clay traps water on top, giving falsely high surface reads when dry below.
    # Attenuation is harsher when surface is very wet (pooling).
    if "clay" in soil_key:
        attenuation = 0.55 if surface_moisture > 80 else 0.75
    else:
        attenuation = 0.90
        
    # VPD-Driven Evaporative Penalty
    from backend.plugins.meta.bio_engine import compute_vpd
    vpd = compute_vpd(temp_celsius, humidity_pct)
    
    # If VPD is 0 (saturated air), factor is 1.0 (no evaporative loss). 
    # If VPD is high, factor drops, reducing estimated root moisture.
    vpd_factor = max(0.4, 1.0 - (vpd * 0.15)) 
    
    estimated_root = surface_moisture * attenuation * vpd_factor
    return round(float(estimated_root), 2)
