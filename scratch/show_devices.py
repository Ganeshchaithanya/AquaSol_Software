import asyncio
from backend.db.session import AsyncSessionLocal
from sqlalchemy import text

async def show_devices():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT mac_address, node_label, is_master, status, node_slot_id, farm_id, pairing_code FROM devices"))
        print("\n--- Current Devices in Database ---")
        for r in res.all():
            node_type = "Master Gateway" if r.is_master else "Irrigation Node"
            slot_info = f" (Slot: {r.node_slot_id})" if r.node_slot_id else " (Unassigned Slot)"
            farm_info = f" (Farm: {r.farm_id})" if r.farm_id else " (No Farm)"
            code_info = f" (Code: {r.pairing_code})" if r.pairing_code else " (No Code)"
            print(f"[{node_type}] MAC: {r.mac_address} | Label: {r.node_label} | Status: {r.status}{slot_info}{farm_info}{code_info}")

if __name__ == "__main__":
    asyncio.run(show_devices())
