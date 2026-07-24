import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import select

from backend.db.session import engine
from backend.models.device import Device
from backend.models.farm import NodeSlot
from backend.services.alerts import create_alert
from backend.utils.logger import logger

AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession)

async def check_device_health():
    """Background task to monitor device heartbeats (Master + Nodes) and trigger offline alerts."""
    while True:
        try:
            async with AsyncSessionLocal() as db:
                # Find all claimed devices (outer join NodeSlot so Master gateways are included)
                result = await db.execute(
                    select(Device, NodeSlot.zone_id)
                    .join(NodeSlot, Device.node_slot_id == NodeSlot.id, isouter=True)
                    .where(Device.is_claimed == True)
                )
                devices = result.all()
                
                now = datetime.now(timezone.utc)
                for device, zone_id in devices:
                    last_time = device.last_seen_at or device.bound_at
                    if not last_time:
                        continue

                    # Ensure timezone awareness for comparison
                    if last_time.tzinfo is None:
                        last_time = last_time.replace(tzinfo=timezone.utc)

                    delta_sec = (now - last_time).total_seconds()
                    
                    if delta_sec > 300 and device.status != "failed":
                        logger.warning(f"[scheduler] Device {device.node_label or device.mac_address} ({device.role}) went OFFLINE (last seen {int(delta_sec)}s ago).")
                        device.status = "failed"
                        device.trust_score = 0.0
                        
                        device_type = "Master Gateway" if device.is_master else "Node"
                        await create_alert(
                            farm_id=str(device.farm_id) if device.farm_id else None,
                            zone_id=str(zone_id) if zone_id else None,
                            alert_type="node_failure",
                            title=f"📡 {device_type} Offline Alert",
                            description=f"{device_type} {device.node_label or device.mac_address} stopped communicating over 5 minutes ago.",
                            db=db
                        )
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"[scheduler] Error in health check loop: {e}")
            
        await asyncio.sleep(15) # Check every 15 seconds

def start_scheduler():
    asyncio.create_task(check_device_health())
