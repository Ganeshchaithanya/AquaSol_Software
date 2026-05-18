"""
AquaSol API Entry Point
Run with: uvicorn main:app --reload
"""
import uvicorn
import socket
from backend.app.main import create_app
from backend.config.settings import get_settings
from backend.utils.logger import logger

app = create_app()
settings = get_settings()

if __name__ == "__main__":
    # Log active LAN IPs dynamically for easy access
    try:
        hostname = socket.gethostname()
        local_ips = socket.gethostbyname_ex(hostname)[2]
        active_ips = [ip for ip in local_ips if not ip.startswith("127.")]
        logger.info("==================================================")
        logger.info(" AquaSol API — Reachable Local Access URLs:")
        logger.info("  • Localhost: http://127.0.0.1:8000")
        for ip in active_ips:
            logger.info(f"  • LAN IP:    http://{ip}:8000")
        logger.info("==================================================")
    except Exception as e:
        logger.warning(f"Could not resolve local network IPs: {e}")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )

