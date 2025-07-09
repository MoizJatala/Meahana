import asyncio
import threading
import time
from typing import Optional, Dict, Any
from pyngrok import ngrok, conf
from pyngrok.exception import PyngrokNgrokError
import logging
import os
import requests

logger = logging.getLogger(__name__)


class NgrokService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(NgrokService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, 'initialized'):
            return
        
        self.initialized = True
        self.tunnel = None
        self.public_url = None
        self.webhook_url = None
        self.is_running = False
        self.external_url = None  # For externally managed ngrok
        
        # Configure ngrok
        self._configure_ngrok()
        
        # Try to detect existing external ngrok tunnel
        self._detect_external_tunnel()
    
    def _configure_ngrok(self):
        """Configure ngrok settings"""
        try:
            # Set ngrok auth token if provided
            auth_token = os.getenv('NGROK_AUTH_TOKEN')
            if auth_token:
                ngrok.set_auth_token(auth_token)
                logger.info("Ngrok auth token set")
            else:
                logger.warning("No NGROK_AUTH_TOKEN found. Using free ngrok (limited features)")
                
        except Exception as e:
            logger.error(f"Error configuring ngrok: {e}")
    
    def _detect_external_tunnel(self):
        """Detect externally running ngrok tunnel"""
        try:
            # Try to access ngrok's local API (usually on port 4040)
            response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
            if response.status_code == 200:
                tunnels = response.json().get('tunnels', [])
                
                # Look for HTTP tunnel pointing to port 8000
                for tunnel in tunnels:
                    if (tunnel.get('proto') == 'https' and 
                        tunnel.get('config', {}).get('addr') == 'http://localhost:8000'):
                        
                        self.external_url = tunnel.get('public_url')
                        self.public_url = self.external_url
                        self.webhook_url = f"{self.external_url}/webhook/"
                        self.is_running = True
                        
                        logger.info(f"Detected external ngrok tunnel: {self.external_url}")
                        logger.info(f"External webhook URL: {self.webhook_url}")
                        return
                        
        except Exception as e:
            logger.debug(f"Could not detect external ngrok tunnel: {e}")
    
    def set_external_url(self, external_url: str):
        """Manually set external ngrok URL"""
        if external_url:
            self.external_url = external_url.rstrip('/')
            self.public_url = self.external_url
            self.webhook_url = f"{self.external_url}/webhook/"
            self.is_running = True
            
            logger.info(f"Set external ngrok URL: {self.external_url}")
            logger.info(f"Webhook URL: {self.webhook_url}")
    
    def start_tunnel(self, port: int = 8000, subdomain: Optional[str] = None) -> str:
        """Start ngrok tunnel"""
        try:
            # If external tunnel is already detected, return that
            if self.external_url:
                logger.info(f"Using existing external ngrok tunnel: {self.external_url}")
                return self.external_url
            
            if self.is_running and self.tunnel:
                logger.info("Ngrok tunnel already running")
                return self.public_url
            
            logger.info(f"Starting ngrok tunnel on port {port}")
            
            # Create tunnel options
            options = {
                "addr": port,
                "proto": "http",
                "bind_tls": True
            }
            
            # Add subdomain if provided and auth token is available
            if subdomain and os.getenv('NGROK_AUTH_TOKEN'):
                options["subdomain"] = subdomain
            
            # Start tunnel
            self.tunnel = ngrok.connect(**options)
            self.public_url = self.tunnel.public_url
            self.webhook_url = f"{self.public_url}/webhook/"
            self.is_running = True
            
            logger.info(f"Ngrok tunnel started: {self.public_url}")
            logger.info(f"Webhook URL: {self.webhook_url}")
            
            return self.public_url
            
        except PyngrokNgrokError as e:
            logger.error(f"Ngrok error: {e}")
            # Try to detect external tunnel as fallback
            self._detect_external_tunnel()
            if self.external_url:
                return self.external_url
            raise
        except Exception as e:
            logger.error(f"Error starting ngrok tunnel: {e}")
            # Try to detect external tunnel as fallback
            self._detect_external_tunnel()
            if self.external_url:
                return self.external_url
            raise
    
    def stop_tunnel(self):
        """Stop ngrok tunnel"""
        try:
            if self.external_url:
                logger.info("Cannot stop external ngrok tunnel - managed externally")
                return
                
            if self.tunnel:
                ngrok.disconnect(self.tunnel.public_url)
                self.tunnel = None
                self.public_url = None
                self.webhook_url = None
                self.is_running = False
                logger.info("Ngrok tunnel stopped")
            else:
                logger.info("No ngrok tunnel to stop")
                
        except Exception as e:
            logger.error(f"Error stopping ngrok tunnel: {e}")
    
    def get_webhook_url(self) -> Optional[str]:
        """Get the current webhook URL"""
        # Refresh external tunnel detection
        if not self.webhook_url:
            self._detect_external_tunnel()
        return self.webhook_url
    
    def get_public_url(self) -> Optional[str]:
        """Get the current public URL"""
        # Refresh external tunnel detection
        if not self.public_url:
            self._detect_external_tunnel()
        return self.public_url
    
    def get_tunnel_info(self) -> Dict[str, Any]:
        """Get tunnel information"""
        return {
            "is_running": self.is_running,
            "public_url": self.public_url,
            "webhook_url": self.webhook_url,
            "tunnel_name": self.tunnel.name if self.tunnel else None,
            "external_url": self.external_url,
            "managed_externally": bool(self.external_url)
        }
    
    def restart_tunnel(self, port: int = 8000, subdomain: Optional[str] = None) -> str:
        """Restart ngrok tunnel"""
        if self.external_url:
            logger.info("Cannot restart external ngrok tunnel - managed externally")
            return self.external_url
            
        logger.info("Restarting ngrok tunnel")
        self.stop_tunnel()
        time.sleep(1)  # Give ngrok time to clean up
        return self.start_tunnel(port, subdomain)
    
    def is_tunnel_active(self) -> bool:
        """Check if tunnel is active"""
        # Refresh external tunnel detection
        if not self.is_running:
            self._detect_external_tunnel()
        return self.is_running
    
    def get_tunnels_info(self) -> list:
        """Get all active tunnels"""
        try:
            # Try to get from external ngrok API first
            try:
                response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
                if response.status_code == 200:
                    external_tunnels = response.json().get('tunnels', [])
                    return [
                        {
                            "name": tunnel.get('name'),
                            "public_url": tunnel.get('public_url'),
                            "config": tunnel.get('config'),
                            "external": True
                        }
                        for tunnel in external_tunnels
                    ]
            except Exception:
                pass
            
            # Fallback to pyngrok
            tunnels = ngrok.get_tunnels()
            return [
                {
                    "name": tunnel.name,
                    "public_url": tunnel.public_url,
                    "config": tunnel.config,
                    "external": False
                }
                for tunnel in tunnels
            ]
        except Exception as e:
            logger.error(f"Error getting tunnels info: {e}")
            return []
    
    def refresh_external_detection(self):
        """Manually refresh external tunnel detection"""
        self._detect_external_tunnel()
        return self.get_tunnel_info()
    
    def __del__(self):
        """Cleanup on destruction"""
        if not self.external_url:  # Only stop if we manage the tunnel
            self.stop_tunnel()


# Global instance
ngrok_service = NgrokService() 