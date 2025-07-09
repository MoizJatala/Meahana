from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import bots, webhooks, reports, ngrok
from app.services.ngrok_service import ngrok_service
import logging
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Meeting Bot Service API with ngrok integration",
    version="1.0.0",
    debug=settings.debug,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(bots.router)
app.include_router(webhooks.router)
app.include_router(reports.router)
app.include_router(ngrok.router)


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("Starting Meeting Bot Service...")
    
    # Try to detect external ngrok tunnel first
    ngrok_service.refresh_external_detection()
    
    # Auto-start ngrok tunnel if enabled and no external tunnel found
    if getattr(settings, 'auto_start_ngrok', True) and not ngrok_service.external_url:
        try:
            logger.info("Auto-starting ngrok tunnel...")
            public_url = ngrok_service.start_tunnel(port=8000)
            logger.info(f"Ngrok tunnel started: {public_url}")
            logger.info(f"Webhook URL: {ngrok_service.get_webhook_url()}")
        except Exception as e:
            logger.error(f"Failed to auto-start ngrok: {e}")
            logger.warning("Continuing without internal ngrok - checking for external tunnel...")
            
            # Try one more time to detect external tunnel
            ngrok_service.refresh_external_detection()
            if ngrok_service.external_url:
                logger.info(f"Found external ngrok tunnel: {ngrok_service.external_url}")
            else:
                logger.warning("No ngrok tunnel found - webhooks will not be received")
    elif ngrok_service.external_url:
        logger.info(f"Using external ngrok tunnel: {ngrok_service.external_url}")
        logger.info(f"Webhook URL: {ngrok_service.get_webhook_url()}")
    else:
        logger.info("Auto-start ngrok disabled - use /ngrok/set-external-url or /ngrok/start to configure")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Shutting down Meeting Bot Service...")
    
    # Stop ngrok tunnel (only if we manage it)
    try:
        if not ngrok_service.external_url:
            ngrok_service.stop_tunnel()
            logger.info("Ngrok tunnel stopped")
        else:
            logger.info("External ngrok tunnel left running")
    except Exception as e:
        logger.error(f"Error stopping ngrok tunnel: {e}")


@app.get("/")
async def root():
    """Root endpoint"""
    ngrok_info = ngrok_service.get_tunnel_info()
    
    return {
        "message": "Meeting Bot Service API",
        "version": "1.0.0",
        "ngrok": ngrok_info
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    ) 