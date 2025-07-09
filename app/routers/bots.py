from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
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
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create a new meeting bot"""
    try:
        # First insert the meeting in pending status
        meeting = await BotService.insert_pending_meeting(db, meeting_data)
        
        # Then call Attendee API in the background
        background_tasks.add_task(
            create_bot_async,
            meeting.id,
            meeting_data.meeting_url,
            meeting_data.bot_name,
            meeting_data.join_at
        )
        
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


async def create_bot_async(meeting_id: int, meeting_url: str, bot_name: str, join_at=None):
    """Background task to create bot via Attendee API"""
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            # Call Attendee API
            bot_id = await BotService.call_attendee_api(meeting_url, bot_name, join_at)
            
            # Update meeting with bot_id
            meeting = await db.get(Meeting, meeting_id)
            if meeting:
                await BotService.update_meeting_with_bot_id(db, meeting, bot_id)
                logger.info(f"Successfully created bot {bot_id} for meeting {meeting_id}")
            
        except Exception as e:
            logger.error(f"Failed to create bot for meeting {meeting_id}: {e}")
            # Update meeting status to failed
            meeting = await db.get(Meeting, meeting_id)
            if meeting:
                await BotService.update_meeting_status(db, meeting, "failed") 