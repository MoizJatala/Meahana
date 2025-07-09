# 🚀 ngrok Integration for Real-Time Webhook Testing

This document explains how to use the built-in ngrok integration for testing webhooks in real-time during meetings.

## 📋 **Overview**

The ngrok integration automatically:
- ✅ Starts ngrok tunnel on application startup
- ✅ Provides webhook URLs to Attendee API automatically
- ✅ Manages tunnel lifecycle (start/stop/restart)
- ✅ Handles webhook events in real-time
- ✅ Stores all webhook events in database

## 🔧 **Configuration**

### **Environment Variables**

Add these to your `.env` file:

```bash
# Required for your bot service
ATTENDEE_API_KEY=your_attendee_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional ngrok configuration
NGROK_AUTH_TOKEN=your_ngrok_auth_token_here    # Optional but recommended
AUTO_START_NGROK=true                          # Auto-start on startup
NGROK_SUBDOMAIN=your-custom-subdomain          # Requires auth token
NGROK_PORT=8000                               # Default port
```

### **Getting ngrok Auth Token** (Optional but Recommended)

1. Go to [ngrok.com](https://ngrok.com) and create a free account
2. Get your auth token from the dashboard
3. Add it to your `.env` file as `NGROK_AUTH_TOKEN`

**Benefits of auth token:**
- Stable subdomain (if configured)
- Longer session duration
- Better performance

## 🚀 **Quick Start**

### **1. Start the Application**

```bash
# Build and start with Docker
docker-compose up --build

# Or start without Docker
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

**Expected output:**
```
INFO - Starting Meeting Bot Service...
INFO - Auto-starting ngrok tunnel...
INFO - Ngrok tunnel started: https://abc123.ngrok.io
INFO - Webhook URL: https://abc123.ngrok.io/webhook/
```

### **2. Test the Integration**

```bash
# Run comprehensive test suite
python test_ngrok_integration.py
```

### **3. Create a Meeting**

```bash
curl -X POST http://localhost:8000/bots/create \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_url": "https://meet.google.com/your-meeting-id",
    "bot_name": "My Test Bot"
  }'
```

The bot will automatically be created with your ngrok webhook URL!

## 🔗 **API Endpoints**

### **ngrok Management**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/ngrok/status` | Get current tunnel status |
| `POST` | `/ngrok/start` | Start ngrok tunnel |
| `POST` | `/ngrok/stop` | Stop ngrok tunnel |
| `POST` | `/ngrok/restart` | Restart ngrok tunnel |
| `GET` | `/ngrok/tunnels` | List all active tunnels |
| `GET` | `/ngrok/webhook-url` | Get current webhook URL |

### **Example Usage**

```bash
# Check ngrok status
curl http://localhost:8000/ngrok/status

# Start ngrok tunnel
curl -X POST http://localhost:8000/ngrok/start \
  -H "Content-Type: application/json" \
  -d '{"port": 8000, "subdomain": "my-bot"}'

# Get webhook URL
curl http://localhost:8000/ngrok/webhook-url
```

## 📊 **Webhook Events**

### **Event Types Handled**

| Event | Description | Action |
|-------|-------------|--------|
| `bot.join_requested` | Bot requested to join | Update meeting status |
| `bot.joining` | Bot is joining | Update meeting status |
| `bot.joined` | Bot joined successfully | Update meeting status |
| `bot.recording` | Bot started recording | Update meeting status |
| `bot.left` | Bot left meeting | Update meeting status to completed |
| `bot.completed` | Meeting completed | Fetch transcript + trigger analysis |
| `bot.failed` | Bot failed | Update meeting status to failed |
| `transcript.chunk` | Real-time transcript | Store transcript chunk |
| `transcript.completed` | Transcript ready | Fetch full transcript |

### **Event Storage**

All webhook events are automatically stored in the `webhook_events` table:

```sql
SELECT id, event_type, bot_id, processed, created_at 
FROM webhook_events 
ORDER BY created_at DESC;
```

## 🧪 **Testing Scenarios**

### **1. Test Basic Webhook**

```bash
curl -X POST https://your-ngrok-url.ngrok.io/webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "event": "bot.joined",
    "data": {
      "bot_id": "test_bot_123",
      "meeting_url": "https://meet.google.com/test",
      "state": "joined"
    }
  }'
```

### **2. Test Transcript Chunk**

```bash
curl -X POST https://your-ngrok-url.ngrok.io/webhook/ \
  -H "Content-Type: application/json" \
  -d '{
    "event": "transcript.chunk",
    "data": {
      "bot_id": "test_bot_123",
      "speaker": "John Doe",
      "text": "Hello everyone!",
      "timestamp": "2024-01-01T12:00:00Z",
      "confidence": "high"
    }
  }'
```

### **3. Test Meeting Creation**

```bash
curl -X POST http://localhost:8000/bots/create \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_url": "https://meet.google.com/real-meeting",
    "bot_name": "Real Meeting Bot"
  }'
```

## 🔍 **Monitoring & Debugging**

### **Check Logs**

```bash
# Docker logs
docker-compose logs web --follow

# Look for ngrok-related logs
docker-compose logs web | grep -i ngrok
```

### **Common Log Messages**

```
✅ Success:
INFO - Ngrok tunnel started: https://abc123.ngrok.io
INFO - Using ngrok webhook URL: https://abc123.ngrok.io/webhook/
INFO - Stored webhook event bot.joined with ID 1

❌ Issues:
ERROR - Failed to auto-start ngrok: [Errno -2] Name or service not known
WARNING - No ngrok webhook URL available - webhooks will not be received
```

### **Health Check**

```bash
# Check service health
curl http://localhost:8000/health

# Check ngrok status
curl http://localhost:8000/ngrok/status

# Check main endpoint (includes ngrok info)
curl http://localhost:8000/
```

## 🎯 **Real Meeting Testing**

### **1. Start Your Application**

```bash
docker-compose up --build
```

### **2. Note Your Webhook URL**

```bash
curl http://localhost:8000/ngrok/webhook-url
```

**Example response:**
```json
{
  "webhook_url": "https://abc123.ngrok.io/webhook/",
  "public_url": "https://abc123.ngrok.io",
  "is_active": true
}
```

### **3. Create a Real Meeting**

```bash
curl -X POST http://localhost:8000/bots/create \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_url": "https://meet.google.com/YOUR_ACTUAL_MEETING_ID",
    "bot_name": "Real Test Bot"
  }'
```

### **4. Join the Meeting**

1. Join the Google Meet using the URL you provided
2. The bot will automatically join
3. Start talking to generate transcripts
4. Watch the logs for real-time webhook events

### **5. Monitor Events**

```bash
# Watch logs
docker-compose logs web --follow

# Check stored events
curl http://localhost:8000/ngrok/status
```

## 📝 **Event Flow Example**

```
1. You create meeting → API stores meeting with status "pending"
2. Bot joins meeting → Webhook: bot.joined → Status: "started"
3. Bot starts recording → Webhook: bot.recording → Status: "started"
4. People talk → Webhook: transcript.chunk → Chunks stored
5. Meeting ends → Webhook: bot.completed → Status: "completed"
6. System fetches full transcript → Analysis triggered
```

## 🔧 **Troubleshooting**

### **ngrok Not Starting**

```bash
# Check if ngrok is installed
docker-compose exec web which ngrok

# Check ngrok logs
docker-compose logs web | grep -i ngrok

# Manually start ngrok
curl -X POST http://localhost:8000/ngrok/start
```

### **Webhooks Not Received**

1. **Check ngrok tunnel is running:**
   ```bash
   curl http://localhost:8000/ngrok/status
   ```

2. **Test webhook manually:**
   ```bash
   curl -X POST https://your-ngrok-url.ngrok.io/webhook/ \
     -H "Content-Type: application/json" \
     -d '{"event": "test", "data": {}}'
   ```

3. **Check webhook URL in bot creation:**
   - Look for log: `"Using ngrok webhook URL: https://..."`
   - If missing, ngrok tunnel isn't running

### **Bot Not Joining Meeting**

1. **Check Attendee API key:**
   ```bash
   echo $ATTENDEE_API_KEY
   ```

2. **Check meeting URL format:**
   - Must be valid Google Meet URL
   - Format: `https://meet.google.com/xxx-xxx-xxx`

3. **Check bot creation response:**
   ```bash
   # Should return bot_id
   curl -X POST http://localhost:8000/bots/create \
     -H "Content-Type: application/json" \
     -d '{"meeting_url": "...", "bot_name": "Test"}'
   ```

## 🎉 **Success Indicators**

You know everything is working when you see:

1. **✅ ngrok tunnel started:** `https://abc123.ngrok.io`
2. **✅ Webhook URL available:** `https://abc123.ngrok.io/webhook/`
3. **✅ Meeting creation successful:** Returns `bot_id`
4. **✅ Webhook events received:** See events in logs
5. **✅ Events stored in database:** Check `webhook_events` table

## 🚀 **Ready to Test!**

Your ngrok integration is now ready for real-time webhook testing! You can:

- Create meetings that automatically get webhook URLs
- Receive real-time webhook events during meetings
- Store and process all webhook events
- Monitor everything through the API endpoints

Happy testing! 🎉 