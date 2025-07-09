from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.config import settings
from app.models.models import Meeting
from app.schemas.schemas import MeetingWithReport
from app.services.analysis_service import AnalysisService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meeting", tags=["reports"])


@router.get("/{meeting_id}/report", response_model=MeetingWithReport)
async def get_meeting_report(
    meeting_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get meeting report with analysis"""
    try:
        # Get meeting with reports and transcript chunks
        result = await db.execute(
            select(Meeting)
            .options(
                selectinload(Meeting.reports),
                selectinload(Meeting.transcript_chunks)
            )
            .where(Meeting.id == meeting_id)
        )
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # If no reports exist and meeting is completed, trigger analysis
        if not meeting.reports and meeting.status == "completed":
            analysis_service = AnalysisService()
            await analysis_service.enqueue_analysis(db, meeting_id)
            
            # Refresh meeting with new report
            await db.refresh(meeting)
        
        return MeetingWithReport.model_validate(meeting)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meeting report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 