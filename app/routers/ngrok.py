from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.services.ngrok_service import ngrok_service
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ngrok", tags=["ngrok"])


class NgrokStartRequest(BaseModel):
    port: int = 8000
    subdomain: Optional[str] = None


class NgrokExternalUrlRequest(BaseModel):
    external_url: str


class NgrokResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


@router.post("/set-external-url", response_model=NgrokResponse)
async def set_external_url(request: NgrokExternalUrlRequest):
    """Set external ngrok URL manually"""
    try:
        ngrok_service.set_external_url(request.external_url)
        
        return NgrokResponse(
            success=True,
            message="External ngrok URL set successfully",
            data={
                "external_url": request.external_url,
                "webhook_url": ngrok_service.get_webhook_url(),
                "managed_externally": True
            }
        )
        
    except Exception as e:
        logger.error(f"Error setting external URL: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set external URL: {str(e)}"
        )


@router.post("/refresh-detection", response_model=NgrokResponse)
async def refresh_detection():
    """Refresh external ngrok tunnel detection"""
    try:
        tunnel_info = ngrok_service.refresh_external_detection()
        
        return NgrokResponse(
            success=True,
            message="External tunnel detection refreshed",
            data=tunnel_info
        )
        
    except Exception as e:
        logger.error(f"Error refreshing detection: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh detection: {str(e)}"
        )


@router.post("/start", response_model=NgrokResponse)
async def start_ngrok_tunnel(request: NgrokStartRequest):
    """Start ngrok tunnel"""
    try:
        public_url = ngrok_service.start_tunnel(
            port=request.port,
            subdomain=request.subdomain
        )
        
        return NgrokResponse(
            success=True,
            message="Ngrok tunnel started successfully",
            data={
                "public_url": public_url,
                "webhook_url": ngrok_service.get_webhook_url(),
                "port": request.port,
                "subdomain": request.subdomain
            }
        )
        
    except Exception as e:
        logger.error(f"Error starting ngrok tunnel: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start ngrok tunnel: {str(e)}"
        )


@router.post("/stop", response_model=NgrokResponse)
async def stop_ngrok_tunnel():
    """Stop ngrok tunnel"""
    try:
        ngrok_service.stop_tunnel()
        
        return NgrokResponse(
            success=True,
            message="Ngrok tunnel stopped successfully"
        )
        
    except Exception as e:
        logger.error(f"Error stopping ngrok tunnel: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop ngrok tunnel: {str(e)}"
        )


@router.post("/restart", response_model=NgrokResponse)
async def restart_ngrok_tunnel(request: NgrokStartRequest):
    """Restart ngrok tunnel"""
    try:
        public_url = ngrok_service.restart_tunnel(
            port=request.port,
            subdomain=request.subdomain
        )
        
        return NgrokResponse(
            success=True,
            message="Ngrok tunnel restarted successfully",
            data={
                "public_url": public_url,
                "webhook_url": ngrok_service.get_webhook_url(),
                "port": request.port,
                "subdomain": request.subdomain
            }
        )
        
    except Exception as e:
        logger.error(f"Error restarting ngrok tunnel: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart ngrok tunnel: {str(e)}"
        )


@router.get("/status", response_model=NgrokResponse)
async def get_ngrok_status():
    """Get ngrok tunnel status"""
    try:
        tunnel_info = ngrok_service.get_tunnel_info()
        
        return NgrokResponse(
            success=True,
            message="Ngrok status retrieved successfully",
            data=tunnel_info
        )
        
    except Exception as e:
        logger.error(f"Error getting ngrok status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ngrok status: {str(e)}"
        )


@router.get("/tunnels", response_model=NgrokResponse)
async def get_all_tunnels():
    """Get all active ngrok tunnels"""
    try:
        tunnels = ngrok_service.get_tunnels_info()
        
        return NgrokResponse(
            success=True,
            message="Tunnels retrieved successfully",
            data={
                "tunnels": tunnels,
                "count": len(tunnels)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting tunnels: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tunnels: {str(e)}"
        )


@router.get("/webhook-url")
async def get_webhook_url():
    """Get current webhook URL"""
    try:
        webhook_url = ngrok_service.get_webhook_url()
        
        if not webhook_url:
            raise HTTPException(
                status_code=404,
                detail="No active ngrok tunnel found"
            )
        
        return {
            "webhook_url": webhook_url,
            "public_url": ngrok_service.get_public_url(),
            "is_active": ngrok_service.is_tunnel_active(),
            "managed_externally": bool(ngrok_service.external_url)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting webhook URL: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get webhook URL: {str(e)}"
        )


@router.post("/auto-start", response_model=NgrokResponse)
async def auto_start_ngrok(background_tasks: BackgroundTasks):
    """Auto-start ngrok tunnel in background"""
    try:
        def start_tunnel_background():
            try:
                ngrok_service.start_tunnel(port=8000)
                logger.info("Ngrok tunnel auto-started successfully")
            except Exception as e:
                logger.error(f"Error auto-starting ngrok tunnel: {e}")
        
        background_tasks.add_task(start_tunnel_background)
        
        return NgrokResponse(
            success=True,
            message="Ngrok tunnel auto-start initiated"
        )
        
    except Exception as e:
        logger.error(f"Error initiating auto-start: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate auto-start: {str(e)}"
        ) 