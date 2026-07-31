"""
Service — Context Builder (v3)
Assembles real-time system state into a structured LLM context object.
Enriched with zone crop metadata from DB: crop_type, season, DAP, growth stage.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, date
from backend.core.state.state_manager import state_manager
from backend.utils.logger import logger


async def build_chat_context(
    farm_id: str,
    farm_name: str,
    zone_ids: List[str],
    weather: Optional[Dict] = None,
    db: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Build the full context dict injected into the chatbot system prompt.
    Combines in-memory sensor state with DB zone metadata (crop, season, DAP).
    """
    from sqlalchemy import select

    # Load zone DB records if a db session is available
    zone_db_map: Dict[str, Any] = {}
    if db is not None:
        try:
            from backend.models.farm import Zone
            res = await db.execute(select(Zone).where(Zone.id.in_(zone_ids)))
            for zone in res.scalars().all():
                zone_db_map[str(zone.id)] = zone
        except Exception as e:
            logger.warning(f"[context_builder] Could not load zones from DB: {e}")

    zones_context = []
    for zid in zone_ids:
        state = state_manager.get_cached_zone_context(zid) or {}
        zone_obj = zone_db_map.get(zid)

        # ── Crop & Season metadata from DB ────────────────────────────────
        crop_type = (zone_obj.crop_type if zone_obj else None) or "unknown"
        season = (zone_obj.season if zone_obj else None) or "unknown"
        zone_name = (zone_obj.name if zone_obj else None) or f"Zone {zid[:6]}"
        sowing_date = zone_obj.sowing_date if zone_obj else None
        soil_type = (zone_obj.soil_type if zone_obj else None) or "unknown"

        # ── Compute DAP (days after planting) ─────────────────────────────
        dap: Optional[int] = None
        if sowing_date:
            dap = max(0, (date.today() - sowing_date).days)

        # ── Stage prediction (rule-based, no DB hit) ──────────────────────
        stage_name = state.get("current_stage") or "unknown"
        kc = state.get("kc")
        growth_progress_pct = state.get("growth_progress_pct", 0)
        stage_sensitive = state.get("stage_sensitivity", False)

        if dap is not None and crop_type != "unknown":
            try:
                from backend.plugins.ai.stage.stage_model import predict_stage
                moisture = float(state.get("current_moisture") or 50.0)
                sr = predict_stage(crop=crop_type, season=season, days_after_planting=dap, soil_moisture_avg_24h=moisture)
                stage_name = sr.get("stage", stage_name)
                kc = sr.get("kc", kc)
                stage_sensitive = sr.get("stage_sensitivity", stage_sensitive)
            except Exception as e:
                logger.warning(f"[context_builder] Stage predict failed for zone {zid}: {e}")

        # ── Anomaly / severity ─────────────────────────────────────────────
        uncertainty = state.get("uncertainty_flag")
        severity = "Normal"
        if uncertainty:
            severity = state.get("anomaly_severity") or f"Alert: {uncertainty}"

        zones_context.append({
            "zone_id": zid,
            "zone_name": zone_name,
            "crop_type": crop_type,
            "season": season,
            "soil_type": soil_type,
            "dap": dap,
            "growth_stage": stage_name,
            "growth_progress": f"{growth_progress_pct}%",
            "stage_sensitive": stage_sensitive,
            "kc": kc,

            "moisture_now": state.get("current_moisture"),
            "moisture_target": f"{state.get('target_moisture_min')}-{state.get('target_moisture_max')}%",
            "predicted_6h": state.get("predicted_moisture_6h"),
            "predicted_24h": state.get("predicted_moisture_24h"),

            "valve_state": "OPEN" if str(state.get("valve_state")).lower() == "open" else "CLOSED",
            "last_irrigation": str(state.get("last_irrigation_at", "N/A")),
            "last_irrigation_duration": state.get("last_irrigation_duration"),

            "trust_score": round(float(state.get("trust_score_avg") or 1.0), 2),
            "status": severity,
            "rolling_avg_24h": state.get("rolling_avg_24h"),
            "active_plan_task": state.get("active_plan_task"),
            "alerts": state.get("active_alerts", []),
            "ai_recommendation": state.get("ai_recommendation") or state.get("last_decision"),
        })

    last_decision = None
    if zones_context:
        first_zid = zone_ids[0]
        first_state = state_manager.get_cached_zone_context(first_zid) or {}
        last_decision = {
            "action": first_state.get("ai_recommendation") or first_state.get("last_decision"),
            "at": str(first_state.get("updated_at") or first_state.get("last_decision_at")),
            "confidence": first_state.get("model_confidence"),
        }

    return {
        "farm_name": farm_name,
        "zones": zones_context,
        "active_alerts": [a for z in zones_context for a in z.get("alerts", [])],
        "weather": weather or {},
        "last_decision": last_decision,
        "system_timestamp": datetime.now(timezone.utc).isoformat(),
    }
