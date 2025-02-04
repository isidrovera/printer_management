#agent\app\services\printer_monitor_service.py
import asyncio
import logging
import aiohttp
import aiosnmp
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
            printer_info = await self.scanner.scan_printer()
            return [printer_info] if printer_info['is_printer'] else []
        except Exception as e:
            logger.error(f"Scan error: {e}")
            return []