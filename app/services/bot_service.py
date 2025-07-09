import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Meeting, MeetingStatus
from app.schemas.schemas import MeetingCreate
from app.core.config import settings
from app.services.ngrok_service import ngrok_service
from typing import Optional
from datetime import datetime
import logging
import asyncio
import socket
import json
from app.services.webhook_service import WebhookService

logger = logging.getLogger(__name__)


class BotService:
    @staticmethod
    async def insert_pending_meeting(db: AsyncSession, meeting_data: MeetingCreate) -> Meeting:
        """Insert a new meeting with pending status"""
        meeting = Meeting(
            meeting_url=meeting_data.meeting_url,
            status="pending",
            meeting_metadata={
                "bot_name": meeting_data.bot_name,
                "join_at": meeting_data.join_at.isoformat() if meeting_data.join_at else None,
            }
        )
        
        db.add(meeting)
        await db.commit()
        await db.refresh(meeting)
        return meeting

    @staticmethod
    async def call_attendee_api(
        meeting_url: str, 
        bot_name: str, 
        join_at: Optional[datetime] = None
    ) -> str:
        """Call the Attendee API to create a bot and return bot_id"""
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Test DNS resolution first and get IP address
                try:
                    ip = socket.gethostbyname("app.attendee.dev")
                    logger.info(f"DNS resolution successful: app.attendee.dev -> {ip}")
                    
                    # Use IP address directly with Host header
                    api_url = f"https://{ip}/api/v1/bots"
                    host_header = "app.attendee.dev"
                    
                except Exception as dns_error:
                    logger.error(f"DNS resolution failed on attempt {attempt + 1}: {dns_error}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(base_delay * (2 ** attempt))
                        continue
                    else:
                        raise
                
                async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                    payload = {
                        "meeting_url": meeting_url,
                        "bot_name": bot_name,
                        "recording_config": {
                            "transcript": True,
                            "video": True,
                            "audio": True
                        }
                    }
                    
                    # Add webhook configuration based on environment
                    webhook_url = WebhookService.get_webhook_url()
                    if webhook_url:
                        payload["webhooks"] = [
                            {
                                "url": webhook_url,
                                "triggers": [
                                    "bot.state_change",
                                    "transcript.update",
                                    "chat_messages.update",
                                    "participant_events.join_leave"
                                ]
                            }
                        ]
                        logger.info(f"✅ Adding bot-level webhook to payload: {webhook_url}")
                        logger.info(f"📋 Webhook triggers: bot.state_change, transcript.update, chat_messages.update, participant_events.join_leave")
                    else:
                        logger.warning("❌ No webhook URL available - webhooks will not be received")
                    
                    if join_at:
                        payload["join_at"] = join_at.isoformat()
                    
                    # Log the complete payload being sent
                    logger.info(f"📤 Sending payload to Attendee API: {json.dumps(payload, indent=2)}")
                    
                    headers = {
                        "Authorization": f"Token {settings.attendee_api_key}",
                        "Content-Type": "application/json",
                        "Host": host_header,
                    }
                    
                    logger.info(f"🔗 Attempting to call Attendee API at {api_url} (attempt {attempt + 1})")
                    
                    response = await client.post(
                        api_url,
                        json=payload,
                        headers=headers,
                        timeout=30.0
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    logger.info(f"📥 Received response from Attendee API: {json.dumps(data, indent=2)}")
                    
                    bot_id = data.get("bot_id") or data.get("id")
                    
                    if not bot_id:
                        raise ValueError("Bot ID not found in response")
                    
                    logger.info(f"🤖 Successfully created bot with ID: {bot_id}")
                    
                    # Log webhook URL confirmation
                    if webhook_url:
                        logger.info(f"✅ Bot created with bot-level webhook URL: {webhook_url}")
                        logger.info(f"📬 Attendee will send webhook events to: {webhook_url}")
                        logger.info(f"🎯 Expected webhook events: bot.state_change, transcript.update, chat_messages.update, participant_events.join_leave")
                    
                    return bot_id
                    
            except (httpx.HTTPError, socket.gaierror) as e:
                logger.error(f"HTTP/DNS error calling Attendee API (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    raise
            except Exception as e:
                logger.error(f"Unexpected error calling Attendee API (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    raise

    @staticmethod
    async def update_meeting_with_bot_id(
        db: AsyncSession, 
        meeting: Meeting, 
        bot_id: str
    ) -> Meeting:
        """Update meeting with bot_id and change status to started"""
        meeting.bot_id = bot_id
        meeting.status = "started"
        meeting.meeting_metadata = {**meeting.meeting_metadata, "bot_id": bot_id}
        
        await db.commit()
        await db.refresh(meeting)
        return meeting

    @staticmethod
    async def get_meeting_by_bot_id(db: AsyncSession, bot_id: str) -> Optional[Meeting]:
        """Get meeting by bot_id"""
        result = await db.execute(
            select(Meeting).where(Meeting.bot_id == bot_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_meeting_status(
        db: AsyncSession, 
        meeting: Meeting, 
        status: str
    ) -> Meeting:
        """Update meeting status"""
        meeting.status = status
        await db.commit()
        await db.refresh(meeting)
        return meeting 