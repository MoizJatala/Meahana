from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class MeetingStatus(str, Enum):
    PENDING = "pending"
    STARTED = "started"
    FAILED = "failed"
    COMPLETED = "completed"


class MeetingCreate(BaseModel):
    meeting_url: str = Field(..., description="The meeting URL to join")
    bot_name: str = Field(..., description="Name for the bot")
    join_at: Optional[datetime] = Field(None, description="Scheduled time to join the meeting")


class MeetingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    meeting_url: str
    bot_id: Optional[str] = None
    status: MeetingStatus
    meeting_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class TranscriptChunkSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    meeting_id: int
    speaker: Optional[str] = None
    text: str
    timestamp: datetime
    confidence: Optional[str] = None
    created_at: datetime


class ReportSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    meeting_id: int
    score: Dict[str, Any]
    created_at: datetime


class AttendeeWebhookPayload(BaseModel):
    """Attendee.dev webhook payload format"""
    idempotency_key: str = Field(..., description="Unique identifier for the webhook event")
    bot_id: str = Field(..., description="Bot identifier")
    trigger: str = Field(..., description="Event trigger type (bot.state_change, transcript.update, etc.)")
    data: Dict[str, Any] = Field(..., description="Event data from Attendee API")
    bot_metadata: Optional[Dict[str, Any]] = Field(None, description="Bot metadata")


class LegacyWebhookPayload(BaseModel):
    """Legacy webhook payload format for backward compatibility"""
    event: str = Field(..., description="Event type from legacy API")
    data: Dict[str, Any] = Field(..., description="Event data from legacy API")


class WebhookPayload(BaseModel):
    """Unified webhook payload that supports both Attendee and legacy formats"""
    # Attendee format fields
    idempotency_key: Optional[str] = Field(None, description="Unique identifier for the webhook event")
    bot_id: Optional[str] = Field(None, description="Bot identifier")
    trigger: Optional[str] = Field(None, description="Event trigger type")
    bot_metadata: Optional[Dict[str, Any]] = Field(None, description="Bot metadata")
    
    # Legacy format fields
    event: Optional[str] = Field(None, description="Event type from legacy API")
    
    # Common field
    data: Dict[str, Any] = Field(..., description="Event data")
    
    def get_event_type(self) -> str:
        """Get the event type, supporting both Attendee (trigger) and legacy (event) formats"""
        return self.trigger or self.event or "unknown"
    
    def get_bot_id(self) -> Optional[str]:
        """Get bot ID from either the direct field or data"""
        return self.bot_id or self.data.get("bot_id")


class MeetingWithReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    meeting_url: str
    bot_id: Optional[str] = None
    status: MeetingStatus
    meeting_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    reports: List[ReportSchema] = Field(default_factory=list)
    transcript_chunks: List[TranscriptChunkSchema] = Field(default_factory=list) 