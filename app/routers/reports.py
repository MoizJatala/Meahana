from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.config import settings
from app.models.models import Meeting
from app.schemas.schemas import MeetingWithReport, MeetingWithTranscripts, MeetingReportResponse
from app.services.analysis_service import AnalysisService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meeting", tags=["reports"])


@router.get("/{meeting_id}/report", response_model=MeetingReportResponse)
async def get_meeting_report(
    meeting_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get meeting report with analysis (reports only)"""
    try:
        # Get meeting with reports only
        result = await db.execute(
            select(Meeting)
            .options(selectinload(Meeting.reports))
            .where(Meeting.id == meeting_id)
        )
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Determine message based on meeting status and reports
        message = None
        if not meeting.reports:
            if meeting.status == "pending":
                message = "Meeting is pending. Report will be available after the meeting is completed."
            elif meeting.status == "started":
                message = "Meeting is in progress. Report will be available after the meeting is completed."
            elif meeting.status == "completed":
                # Trigger analysis if meeting is completed but no reports exist
                analysis_service = AnalysisService()
                await analysis_service.enqueue_analysis(db, meeting_id)
                
                # Refresh meeting to get new report
                await db.refresh(meeting)
                
                if not meeting.reports:
                    message = "Report is being generated. Please try again in a few moments."
            elif meeting.status == "failed":
                message = "Meeting failed. No report available."
            else:
                message = "No report available for this meeting."
        
        return MeetingReportResponse(
            meeting_id=meeting.id,
            meeting_url=meeting.meeting_url,
            bot_id=meeting.bot_id,
            status=meeting.status,
            reports=meeting.reports,
            message=message,
            created_at=meeting.created_at,
            updated_at=meeting.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meeting report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{meeting_id}/transcripts", response_model=MeetingWithTranscripts)
async def get_meeting_transcripts(
    meeting_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get meeting transcripts (available during and after meeting)"""
    try:
        # Get meeting with transcript chunks
        result = await db.execute(
            select(Meeting)
            .options(selectinload(Meeting.transcript_chunks))
            .where(Meeting.id == meeting_id)
        )
        meeting = result.scalar_one_or_none()
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Return transcripts regardless of meeting status
        # During meeting: real-time transcripts
        # After meeting: complete transcripts
        return MeetingWithTranscripts.model_validate(meeting)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meeting transcripts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 