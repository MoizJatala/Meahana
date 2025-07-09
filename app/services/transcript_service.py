import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Meeting, TranscriptChunk
from app.core.config import settings
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TranscriptService:
    async def fetch_full_transcript(
        self, 
        db: AsyncSession, 
        bot_id: str
    ) -> List[Dict[str, Any]]:
        """Fetch full transcript from Attendee API"""
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Token {settings.attendee_api_key}",
                "Content-Type": "application/json",
            }
            
            try:
                response = await client.get(
                    f"{settings.attendee_api_base_url}/api/v1/bots/{bot_id}/transcript",
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                transcript_chunks = data.get("transcript", [])
                
                # Process and store transcript chunks
                await self._process_transcript_chunks(db, bot_id, transcript_chunks)
                
                logger.info(f"Successfully fetched transcript for bot {bot_id}")
                return transcript_chunks
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching transcript: {e}")
                raise
            except Exception as e:
                logger.error(f"Error fetching transcript: {e}")
                raise

    async def _process_transcript_chunks(
        self,
        db: AsyncSession,
        bot_id: str,
        transcript_chunks: List[Dict[str, Any]]
    ):
        """Process and store transcript chunks"""
        # Get meeting by bot_id
        from app.services.bot_service import BotService
        meeting = await BotService.get_meeting_by_bot_id(db, bot_id)
        
        if not meeting:
            logger.error(f"Meeting not found for bot_id: {bot_id}")
            return
        
        for chunk_data in transcript_chunks:
            try:
                speaker = chunk_data.get("speaker")
                text = chunk_data.get("text")
                timestamp_str = chunk_data.get("timestamp")
                
                if not text or not timestamp_str:
                    continue
                
                # Parse timestamp
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                
                # Check if chunk already exists
                result = await db.execute(
                    select(TranscriptChunk).where(
                        TranscriptChunk.meeting_id == meeting.id,
                        TranscriptChunk.timestamp == timestamp,
                        TranscriptChunk.speaker == speaker
                    )
                )
                existing_chunk = result.scalar_one_or_none()
                
                if not existing_chunk:
                    # Create new chunk
                    chunk = TranscriptChunk(
                        meeting_id=meeting.id,
                        speaker=speaker,
                        text=text,
                        timestamp=timestamp
                    )
                    db.add(chunk)
                
            except Exception as e:
                logger.error(f"Error processing transcript chunk: {e}")
                continue
        
        await db.commit()
        logger.info(f"Processed {len(transcript_chunks)} transcript chunks")

    async def get_transcript_chunks(
        self, 
        db: AsyncSession, 
        meeting_id: int
    ) -> List[TranscriptChunk]:
        """Get transcript chunks for a meeting"""
        result = await db.execute(
            select(TranscriptChunk)
            .where(TranscriptChunk.meeting_id == meeting_id)
            .order_by(TranscriptChunk.timestamp)
        )
        return result.scalars().all() 