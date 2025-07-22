from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from app.schemas.schemas import MeetingCreate, MeetingResponse
from app.services.bot_service import BotService
from app.models.models import Meeting
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bots", tags=["bots"])


@router.post("/", response_model=MeetingResponse)
async def create_bot(
    meeting_data: MeetingCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new meeting bot and wait for bot_id from Attendee API"""
    try:
        # First insert the meeting in pending status
        meeting = await BotService.insert_pending_meeting(db, meeting_data)
        
        # Call Attendee API and wait for bot_id
        bot_id = await BotService.call_attendee_api(
            meeting_data.meeting_url,
            meeting_data.bot_name,
            meeting_data.join_at
        )
        
        # Update meeting with bot_id and status
        meeting = await BotService.update_meeting_with_bot_id(db, meeting, bot_id)
        
        return MeetingResponse(
            id=meeting.id,
            meeting_url=meeting.meeting_url,
            bot_id=meeting.bot_id,
            status=meeting.status,
            meeting_metadata=meeting.meeting_metadata,
            created_at=meeting.created_at,
            updated_at=meeting.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error creating bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to create bot")

 