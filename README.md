# Meeting Bot Service

A production-ready FastAPI service for managing meeting bots with **Attendee.dev** integration, real-time webhook processing, and AI-powered analysis. Features environment-aware configuration, automatic webhook tunneling, and comprehensive deployment support.

## ✨ Features

- **🤖 Bot Management**: Create and manage meeting bots via Attendee.dev API
- **🔄 Real-time Webhooks**: Process live webhook events with automatic URL configuration
- **🌐 ngrok Integration**: Automatic webhook tunneling for development with fallback mechanisms
- **📝 Transcript Processing**: Store and analyze meeting transcripts in real-time
- **🧠 AI Analysis**: Generate meeting insights using OpenAI GPT
- **🚀 Environment-Aware**: Development, staging, and production configurations
- **🔒 Security**: HMAC signature verification for production webhooks
- **⚡ Async Architecture**: Built with async SQLAlchemy and FastAPI
- **🔧 Background Tasks**: Process transcripts and analysis asynchronously
- **🐳 Docker Ready**: Complete containerization with Docker Compose

## 🏗️ Project Structure

```
├── app/
│   ├── core/             # Core configuration and database
│   ├── models/           # SQLAlchemy models (Meeting, WebhookEvent, etc.)
│   ├── schemas/          # Pydantic schemas with unified webhook support
│   ├── services/         # Business logic services
│   │   ├── bot_service.py       # Attendee.dev API integration
│   │   ├── webhook_service.py   # Webhook event processing
│   │   ├── ngrok_service.py     # Tunnel management
│   │   └── analysis_service.py  # AI analysis
│   ├── routers/          # API endpoints
│   │   ├── bots.py             # Bot management endpoints
│   │   ├── webhooks.py         # Webhook receivers
│   │   ├── ngrok.py            # ngrok management
│   │   └── reports.py          # Meeting reports
│   └── main.py           # FastAPI application with startup/shutdown
├── alembic/              # Database migrations
├── .env                  # Development environment (with ngrok)
├── .env.staging          # Staging environment  
├── .env.production       # Production environment
├── docker-compose.yml    # Container orchestration
├── Dockerfile           # Container configuration
├── DEPLOYMENT.md        # Comprehensive deployment guide
└── requirements.txt     # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Attendee.dev API key
- OpenAI API key (for analysis)
- ngrok account (for development) - Optional

### 1. Clone & Setup

```bash
git clone <repository-url>
cd meeting-bot-service
```

### 2. Environment Configuration

Choose your environment and copy the appropriate configuration:

**Development (with ngrok):**
```bash
cp .env.example .env
# or use the existing .env file
```

**Staging:**
```bash
cp .env.staging .env
```

**Production:**
```bash
cp .env.production .env
```

### 3. Configure Environment Variables

Edit your chosen `.env` file:

```env
# Required API Keys
ATTENDEE_API_KEY=your-attendee-api-key-here
OPENAI_API_KEY=your-openai-api-key-here

# Environment-specific settings
ENVIRONMENT=development  # development/staging/production
WEBHOOK_BASE_URL=https://your-domain.com  # or ngrok URL for dev

# Database (automatically configured for Docker)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/meeting_bot_db
REDIS_URL=redis://localhost:6379/0

# ngrok (Development only)
NGROK_AUTH_TOKEN=your-ngrok-token  # Optional but recommended
AUTO_START_NGROK=true
```

### 4. Start Services

**With Docker (Recommended):**
```bash
# Background mode (detached)
docker compose up -d

# Foreground mode (see logs in terminal)
docker compose up
```

**Manual Setup:**
```bash
pip install -r requirements.txt
createdb meeting_bot_db
alembic upgrade head
uvicorn app.main:app --reload
```

### 5. Verify Setup

- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **ngrok Status**: http://localhost:8000/ngrok/status

## 🌍 Environment-Based Configuration

### Development Environment
- ✅ **ngrok auto-tunneling** for webhook access
- ✅ **Local database/Redis** via Docker
- ✅ **Debug logging** enabled
- ✅ **Hot reload** for code changes

### Staging Environment  
- ✅ **Production-like setup** without ngrok
- ✅ **Staging database/Redis**
- ✅ **Manual webhook URL** configuration
- ✅ **Enhanced logging** for testing

### Production Environment
- ✅ **Direct webhook URLs** (no tunneling)
- ✅ **Production database/Redis**
- ✅ **HMAC signature verification**
- ✅ **Optimized performance** settings

## 📡 Webhook System

### Automatic Webhook URL Configuration

The service automatically determines the correct webhook URL based on your environment:

| Environment | Webhook URL Source | ngrok Usage |
|-------------|-------------------|-------------|
| **Development** | ngrok tunnel OR manual URL | ✅ Auto-enabled |
| **Staging** | `WEBHOOK_BASE_URL` | ❌ Disabled |
| **Production** | `WEBHOOK_BASE_URL` | ❌ Disabled |

### Webhook Endpoints

#### `/webhook/` - Development & Testing
- **Purpose**: Quick webhook testing without authentication
- **Security**: None
- **Use Case**: Development, internal testing, debugging

#### `/webhook/attendee` - Production Ready
- **Purpose**: Secure webhook processing with HMAC verification
- **Security**: Signature verification with `WEBHOOK_SECRET`
- **Use Case**: Production, external webhooks, security-critical applications

### Supported Webhook Events

All endpoints process these Attendee.dev webhook events:
- `bot.state_change` - Bot status updates (joining, joined, recording, etc.)
- `transcript.update` - Real-time transcript chunks
- `chat_messages.update` - Chat message events
- `participant_events.join_leave` - Participant activity

## 🤖 API Endpoints

### Bot Management

#### Create Bot
```http
POST /api/v1/bots
Content-Type: application/json

{
  "meeting_url": "https://meet.google.com/abc-def-ghi",
  "bot_name": "AI Meeting Assistant",
  "join_at": "2024-01-01T10:00:00Z"  // optional
}
```

**Response:**
```json
{
  "id": 1,
  "meeting_url": "https://meet.google.com/abc-def-ghi",
  "bot_id": "bot_abc123",
  "status": "started",
  "meeting_metadata": {
    "bot_name": "AI Meeting Assistant"
  },
  "created_at": "2024-01-01T09:00:00Z",
  "updated_at": "2024-01-01T09:00:00Z"
}
```

### Webhook Processing

#### Development Webhook
```http
POST /webhook/
Content-Type: application/json

{
  "trigger": "bot.state_change",
  "bot_id": "bot_abc123",
  "data": {"state": "joined"}
}
```

#### Production Webhook (with signature)
```http
POST /webhook/attendee
Content-Type: application/json
X-Webhook-Signature: sha256=abc123...

{
  "idempotency_key": "unique-event-id",
  "bot_id": "bot_abc123",
  "trigger": "bot.state_change",
  "data": {"state": "joined"}
}
```

### Meeting Reports

#### Get Meeting Report with AI Analysis
```http
GET /meeting/{meeting_id}/report
```

**Response:**
```json
{
  "id": 1,
  "meeting_url": "https://meet.google.com/abc-def-ghi",
  "status": "completed",
  "reports": [
    {
      "score": {
        "overall_score": 0.85,
        "sentiment": "positive",
        "key_topics": ["project planning", "budget review"],
        "action_items": ["Send budget proposal"],
        "summary": "Productive meeting about project planning"
      }
    }
  ],
  "transcript_chunks": [
    {
      "speaker": "John",
      "text": "Let's start with the budget review",
      "timestamp": "2024-01-01T10:05:00Z"
    }
  ]
}
```

### ngrok Management

#### Get ngrok Status
```http
GET /ngrok/status
```

#### Start ngrok Tunnel
```http
POST /ngrok/start
Content-Type: application/json

{
  "port": 8000,
  "subdomain": "my-app"  // optional
}
```

#### Set External ngrok URL
```http
POST /ngrok/set-external-url
Content-Type: application/json

{
  "external_url": "https://abc123.ngrok-free.app"
}
```

## 🛠️ Development

### Running with Logs

**See all logs in terminal:**
```bash
docker compose up
```

**Follow logs from running containers:**
```bash
docker compose logs -f
docker compose logs -f web  # specific service
```

### Local Development Workflow

1. **Edit code** in `app/` directory (hot reload enabled)
2. **Database changes**: Create migrations with `alembic revision --autogenerate`
3. **Test webhooks**: Use `/webhook/` endpoint for quick testing
4. **Monitor ngrok**: Check `/ngrok/status` for tunnel information

### Testing

**Create a test bot:**
```bash
curl -X POST "http://localhost:8000/api/v1/bots/" \
  -H "Content-Type: application/json" \
  -d '{
    "meeting_url": "https://meet.google.com/test-meeting",
    "bot_name": "Test Bot"
  }'
```

**Test webhook processing:**
```bash
curl -X POST "http://localhost:8000/webhook/" \
  -H "Content-Type: application/json" \
  -d '{
    "trigger": "bot.state_change",
    "bot_id": "bot_test123",
    "data": {"state": "joined"}
  }'
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🚀 Deployment

### Quick Deployment Commands

**Staging:**
```bash
cp .env.staging .env
# Update URLs in .env for your staging environment
docker compose up -d
```

**Production:**
```bash
cp .env.production .env
# Update URLs in .env for your production environment  
docker compose up -d
```

### Environment Variables Reference

| Variable | Development | Staging | Production | Description |
|----------|-------------|---------|------------|-------------|
| `ENVIRONMENT` | `development` | `staging` | `production` | Environment mode |
| `AUTO_START_NGROK` | `true` | `false` | `false` | Enable ngrok tunneling |
| `WEBHOOK_BASE_URL` | ngrok URL | staging domain | production domain | Webhook endpoint base |
| `DEBUG` | `false` | `true` | `false` | Debug logging |
| `WEBHOOK_SECRET` | optional | recommended | required | HMAC signature secret |

### Security Checklist

**Production Deployment:**
- [ ] Set strong `WEBHOOK_SECRET` for signature verification
- [ ] Use production-specific API keys
- [ ] Configure SSL/TLS certificates
- [ ] Set up firewall rules
- [ ] Use `/webhook/attendee` endpoint for external webhooks
- [ ] Monitor webhook event processing
- [ ] Set up log aggregation

### Troubleshooting

**No webhook URL found:**
- Check `WEBHOOK_BASE_URL` is set
- Verify ngrok tunnel is running (`/ngrok/status`)
- Ensure environment variables are loaded correctly

**Permission denied (ngrok in Docker):**
- This is expected and harmless
- External webhook URL will be used automatically
- Set `AUTO_START_NGROK=false` to suppress warnings

**Bot creation fails:**
- Verify `ATTENDEE_API_KEY` is correct
- Check network connectivity to Attendee.dev
- Review logs for specific error messages

## 📊 Monitoring & Observability

### Health Checks
```bash
curl http://localhost:8000/health
curl http://localhost:8000/ngrok/status
```

### Logs
```bash
# Application logs
docker compose logs -f web

# Database logs
docker compose logs -f db

# All services
docker compose logs -f
```

### Metrics Endpoints
- `/` - Service information and ngrok status
- `/health` - Health check
- `/docs` - API documentation
- `/ngrok/status` - Tunnel status

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and test thoroughly
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Submit pull request

### Development Guidelines

- Follow FastAPI best practices
- Add tests for new features
- Update documentation
- Use type hints
- Format code with `black` and `isort`

## 📚 Additional Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Comprehensive deployment guide
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs
- **[Attendee.dev Docs](https://docs.attendee.dev)** - External API reference

## 🔗 Integration Examples

### Attendee.dev Webhook Integration
```python
# Your webhook receiver will get payloads like:
{
  "idempotency_key": "evt_123",
  "bot_id": "bot_abc123",
  "trigger": "transcript.update",
  "data": {
    "speaker": "John Doe",
    "text": "Hello everyone, let's start the meeting"
  }
}
```

### Custom Analysis Pipeline
```python
# Extend the AnalysisService for custom insights
class CustomAnalysisService(AnalysisService):
    async def generate_custom_insights(self, transcript_chunks):
        # Your custom analysis logic
        pass
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**🚀 Ready to build amazing meeting experiences?** Start with `docker compose up` and check out the [deployment guide](DEPLOYMENT.md) for production setup! 