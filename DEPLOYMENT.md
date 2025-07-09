# Deployment Guide

## Environment Files

This project uses different environment files for different deployment scenarios:

### 📁 Available Environment Files

| File | Purpose | ngrok | Webhook URL |
|------|---------|-------|-------------|
| `.env` | Development | ✅ Enabled | ngrok tunnel |
| `.env.staging` | Staging | ❌ Disabled | `https://staging.yourdomain.com` |
| `.env.production` | Production | ❌ Disabled | `https://api.yourdomain.com` |

### 🚀 How to Deploy

#### Development (Local)
```bash
# Already configured - just run:
docker-compose up -d
```

#### Staging Deployment
```bash
# Copy staging environment file
cp .env.staging .env

# Update with your staging URLs:
# - WEBHOOK_BASE_URL=https://your-staging-domain.com
# - DATABASE_URL=your-staging-database-url
# - REDIS_URL=your-staging-redis-url

# Deploy
docker-compose up -d
```

#### Production Deployment
```bash
# Copy production environment file
cp .env.production .env

# Update with your production URLs:
# - WEBHOOK_BASE_URL=https://your-production-domain.com
# - DATABASE_URL=your-production-database-url
# - REDIS_URL=your-production-redis-url

# Deploy
docker-compose up -d
```

### 🔧 Environment Configuration Details

#### Key Environment Variables

| Variable | Development | Staging | Production |
|----------|-------------|---------|------------|
| `ENVIRONMENT` | `development` | `staging` | `production` |
| `AUTO_START_NGROK` | `true` | `false` | `false` |
| `WEBHOOK_BASE_URL` | ngrok URL | staging domain | production domain |
| `DEBUG` | `false` | `true` | `false` |

#### Webhook URL Logic

The system automatically determines the webhook URL based on environment:

1. **Production/Staging**: Uses `WEBHOOK_BASE_URL` + `/webhook`
2. **Development**: Uses ngrok tunnel URL (automatic)
3. **Fallback**: Manual `WEBHOOK_BASE_URL` + `/webhook`

### 📋 Pre-Deployment Checklist

#### For Staging/Production:
- [ ] Update `WEBHOOK_BASE_URL` to your server domain
- [ ] Update database connection strings
- [ ] Update Redis connection strings
- [ ] Set production API keys
- [ ] Configure webhook secrets
- [ ] Set up SSL certificates
- [ ] Configure firewall rules
- [ ] Set up monitoring/logging

#### Database Migration:
```bash
# Run migrations after deployment
docker-compose exec app alembic upgrade head
```

### 🔍 Testing Different Environments

#### Test Development Configuration:
```bash
export ENVIRONMENT=development
export AUTO_START_NGROK=true
python -c "
from app.core.config import settings
from app.services.webhook_service import WebhookService
print('Webhook URL:', WebhookService.get_webhook_url())
"
```

#### Test Production Configuration:
```bash
export ENVIRONMENT=production
export WEBHOOK_BASE_URL=https://api.yourdomain.com
python -c "
from app.core.config import settings
from app.services.webhook_service import WebhookService
print('Webhook URL:', WebhookService.get_webhook_url())
"
```

### 🛠️ Troubleshooting

#### Common Issues:

1. **No webhook URL in production**: Set `WEBHOOK_BASE_URL` environment variable
2. **ngrok not working**: Check `NGROK_AUTH_TOKEN` and `AUTO_START_NGROK=true`
3. **Database connection failed**: Verify database URL and credentials
4. **Webhook not received**: Check webhook URL format and firewall rules

#### Logs:
```bash
# View application logs
docker-compose logs -f app

# View ngrok logs (development only)
docker-compose logs -f app | grep ngrok
```

### 🔒 Security Considerations

- Use different API keys for each environment
- Set strong `WEBHOOK_SECRET` for production
- Use environment-specific database credentials
- Enable SSL/TLS for production webhooks
- Configure CORS origins appropriately

### 🌐 DNS and SSL Setup

For production deployment, ensure:
1. Domain points to your server IP
2. SSL certificate is configured
3. Webhook endpoint is accessible: `https://yourdomain.com/webhook`
4. Health check endpoint works: `https://yourdomain.com/health` 