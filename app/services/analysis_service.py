import openai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Meeting, TranscriptChunk, Report
from app.core.config import settings
from typing import Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)

# Configure OpenAI
client = openai.AsyncOpenAI(api_key=settings.openai_api_key)


class AnalysisService:
    async def enqueue_analysis(self, db: AsyncSession, meeting_id: int):
        """Enqueue analysis for a meeting"""
        try:
            # Get meeting
            result = await db.execute(
                select(Meeting).where(Meeting.id == meeting_id)
            )
            meeting = result.scalar_one_or_none()
            
            if not meeting:
                logger.error(f"Meeting not found: {meeting_id}")
                return
            
            # Get transcript chunks
            transcript_result = await db.execute(
                select(TranscriptChunk)
                .where(TranscriptChunk.meeting_id == meeting_id)
                .order_by(TranscriptChunk.timestamp)
            )
            transcript_chunks = transcript_result.scalars().all()
            
            if not transcript_chunks:
                logger.warning(f"No transcript chunks found for meeting {meeting_id}")
                return
            
            # Analyze transcript
            analysis_result = await self._analyze_transcript(transcript_chunks)
            
            # Upsert report
            await self._upsert_report(db, meeting_id, analysis_result)
            
            logger.info(f"Analysis completed for meeting {meeting_id}")
            
        except Exception as e:
            logger.error(f"Error analyzing meeting {meeting_id}: {e}")

    async def _analyze_transcript(self, transcript_chunks: List[TranscriptChunk]) -> Dict[str, Any]:
        """Analyze transcript using OpenAI"""
        # Build transcript text
        transcript_text = ""
        for chunk in transcript_chunks:
            speaker = chunk.speaker or "Unknown"
            transcript_text += f"{speaker}: {chunk.text}\n"
        
        # Create analysis prompt
        prompt = f"""
        Please analyze the following meeting transcript and provide a comprehensive analysis in JSON format.
        
        Transcript:
        {transcript_text}
        
        Please provide the analysis in the following JSON format:
        {{
            "overall_score": 0.85,
            "sentiment": "positive",
            "key_topics": ["topic1", "topic2"],
            "action_items": ["action1", "action2"],
            "participants": ["participant1", "participant2"],
            "engagement_score": 0.8,
            "meeting_effectiveness": 0.9,
            "summary": "Brief summary of the meeting",
            "insights": ["insight1", "insight2"],
            "recommendations": ["recommendation1", "recommendation2"]
        }}
        
        Only return the JSON object, no additional text.
        """
        
        try:
            # Use OpenAI ChatCompletion API
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a meeting analysis expert. Analyze meeting transcripts and provide structured insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            # Parse response
            analysis_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            try:
                analysis_result = json.loads(analysis_text)
                return analysis_result
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response: {analysis_text}")
                return self._get_default_analysis()
                
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return self._get_default_analysis()

    def _get_default_analysis(self) -> Dict[str, Any]:
        """Get default analysis when OpenAI fails"""
        return {
            "overall_score": 0.5,
            "sentiment": "neutral",
            "key_topics": [],
            "action_items": [],
            "participants": [],
            "engagement_score": 0.5,
            "meeting_effectiveness": 0.5,
            "summary": "Analysis could not be completed",
            "insights": [],
            "recommendations": []
        }

    async def _upsert_report(
        self,
        db: AsyncSession,
        meeting_id: int,
        analysis_result: Dict[str, Any]
    ):
        """Upsert analysis report"""
        # Check if report already exists
        result = await db.execute(
            select(Report).where(Report.meeting_id == meeting_id)
        )
        existing_report = result.scalar_one_or_none()
        
        if existing_report:
            # Update existing report
            existing_report.score = analysis_result
            await db.commit()
            logger.info(f"Updated report for meeting {meeting_id}")
        else:
            # Create new report
            report = Report(
                meeting_id=meeting_id,
                score=analysis_result
            )
            db.add(report)
            await db.commit()
            logger.info(f"Created new report for meeting {meeting_id}")

    async def get_report(self, db: AsyncSession, meeting_id: int) -> Report:
        """Get analysis report for a meeting"""
        result = await db.execute(
            select(Report).where(Report.meeting_id == meeting_id)
        )
        return result.scalar_one_or_none() 