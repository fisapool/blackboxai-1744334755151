from typing import Optional, Dict, Any
import logging
import json
import asyncio
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class MultimodalIntegration:
    """
    Handles integration of multiple data sources including webcam and HID systems
    """
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path or 'config.json')
        self.is_running = False
        self.tasks = []

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Config file not found at {config_path}, using defaults")
                return self._default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}", exc_info=True)
            return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            "webcam": {
                "enabled": False,
                "capture_interval": 30,
                "resolution": [640, 480]
            },
            "hid": {
                "enabled": True,
                "sampling_rate": 1000,
                "buffer_size": 1024
            },
            "storage": {
                "path": "data/captures",
                "retention_days": 30
            }
        }

    async def start(self):
        """Start the integration services"""
        if self.is_running:
            logger.warning("Integration already running")
            return

        try:
            logger.info("Starting multimodal integration...")
            
            if self.config["webcam"]["enabled"]:
                self.tasks.append(
                    asyncio.create_task(self._run_webcam_integration())
                )
                logger.info("Webcam integration started")

            if self.config["hid"]["enabled"]:
                self.tasks.append(
                    asyncio.create_task(self._run_hid_integration())
                )
                logger.info("HID integration started")

            self.is_running = True
            logger.info("Multimodal integration started successfully")

        except Exception as e:
            logger.error(f"Error starting integration: {e}", exc_info=True)
            await self.stop()
            raise

    async def stop(self):
        """Stop all integration services"""
        if not self.is_running:
            return

        try:
            logger.info("Stopping multimodal integration...")
            
            for task in self.tasks:
                task.cancel()
            
            if self.tasks:
                await asyncio.gather(*self.tasks, return_exceptions=True)
            
            self.tasks.clear()
            self.is_running = False
            logger.info("Multimodal integration stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping integration: {e}", exc_info=True)
            raise

    async def _run_webcam_integration(self):
        """Run webcam integration service"""
        try:
            while True:
                # TODO: Implement actual webcam capture logic
                await asyncio.sleep(self.config["webcam"]["capture_interval"])
                logger.debug("Webcam capture completed")
        except asyncio.CancelledError:
            logger.info("Webcam integration cancelled")
        except Exception as e:
            logger.error(f"Error in webcam integration: {e}", exc_info=True)
            raise

    async def _run_hid_integration(self):
        """Run HID system integration service"""
        try:
            while True:
                # TODO: Implement actual HID monitoring logic
                await asyncio.sleep(1)
                logger.debug("HID data captured")
        except asyncio.CancelledError:
            logger.info("HID integration cancelled")
        except Exception as e:
            logger.error(f"Error in HID integration: {e}", exc_info=True)
            raise

    async def get_status(self) -> Dict[str, Any]:
        """Get current status of all integrations"""
        return {
            "is_running": self.is_running,
            "active_tasks": len(self.tasks),
            "webcam_enabled": self.config["webcam"]["enabled"],
            "hid_enabled": self.config["hid"]["enabled"],
            "last_check": datetime.utcnow().isoformat()
        }
