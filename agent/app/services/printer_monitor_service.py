# agent\app\services\printer_monitor_service.py
import logging
from typing import Dict, List
from .network_scanner_service import NetworkScannerService

logger = logging.getLogger(__name__)

class PrinterMonitorService:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.scanner = NetworkScannerService()

    async def scan_and_monitor(self) -> List[Dict]:
        try:
            logger.info("Starting printer scan")
            result = await self.scanner.scan_printer()
            return [result] if result['is_printer'] else []
        except Exception as e:
            logger.error(f"Scan error: {e}")
            return []