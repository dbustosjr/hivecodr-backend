# HiveCodr Backend

AI-powered full-stack application generator using specialized agent swarms (Architect, Developer, Frontend, and QA bees).

## Features

- **5-Bee Architecture**: Architect, Developer, Frontend, and QA bees working in harmony
- **Comprehensive Testing**: Backend, frontend, E2E, security, and contract tests (Phase 5.5)
- **Production-Ready**: Full-stack applications with 80%+ test coverage
- **FastAPI Backend**: High-performance async API with SQLAlchemy
- **Next.js 14 Frontend**: Modern React applications with TypeScript and Tailwind CSS
- **Supabase Authentication**: JWT-based auth on all endpoints
- **Rate Limiting**: 10 generations per hour per user

## Tech Stack

- **Framework**: FastAPI 0.115.0
- **Agent Framework**: CrewAI 0.86.0
- **AI Model**: Claude Sonnet 4 (claude-sonnet-4-20250514)
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase JWT
- **Deployment**: Railway

## Quick Start

1. Copy `.env.example` to `.env` and add your API keys
2. Install dependencies: `pip install -r requirements.txt`
3. Run server: `uvicorn main:app --reload`
4. Visit `http://localhost:8000/docs` for API documentation

## API Documentation

- Swagger UI: `/docs` - Interactive API documentation
- Health Check: `/health` - Returns `{"status":"healthy"}`

## Architecture

- **Architect Bee**: Designs database schema and API architecture
- **Developer Bee**: Generates FastAPI backend code (models, schemas, routes)
- **Frontend Bee**: Creates Next.js frontend applications
- **QA Bee (Phase 5.5)**: Generates comprehensive test suites (backend, frontend, E2E, security, contracts)

## API Endpoints

### Health Check
```
GET /health
```
Returns API health status (no authentication required)

### Generate Code
```
POST /api/generate
Authorization: Bearer <supabase_jwt_token>
Content-Type: application/json

{
  "requirements": "Create a blog post API with title, content, and author"
}
```

Returns generated FastAPI CRUD code (models, schemas, routes, main.py)

### Get Past Generations
```
GET /api/generations
Authorization: Bearer <supabase_jwt_token>
```

Returns all past code generations for the authenticated user

## Security Features

### Authentication
- All endpoints (except `/health`) require Supabase JWT token
- Token validation happens in `app/core/auth.py`
- Invalid or expired tokens return 401 Unauthorized

### Rate Limiting
- 10 generations per hour per user
- Tracked in `user_usage` table
- Returns 429 Too Many Requests when exceeded

### Input Validation
- Max 5000 characters for requirements
- HTML tags stripped with `bleach`
- Pydantic validation on all inputs

### Cost Protection
- Daily cost cap: $100 (configurable)
- No code execution on server
- All generated code is returned as text

### Row Level Security (RLS)
- Users can only access their own data
- Enforced at database level via Supabase

## Developer Bee Agent

The Developer Bee agent uses CrewAI and Claude API to generate complete FastAPI CRUD applications.

### Agent Capabilities
- Generates SQLAlchemy models
- Creates Pydantic schemas
- Writes FastAPI routes with full CRUD operations
- Produces main.py with proper configuration

### Example Input
```
"Create a blog API with posts that have title, content, author, and published_at"
```

### Example Output
```json
{
  "code": {
    "models": "# SQLAlchemy models code...",
    "schemas": "# Pydantic schemas code...",
    "routes": "# FastAPI routes code...",
    "main": "# Main application code..."
  },
  "agent_log": "Agent execution log...",
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Deployment (Railway)

### 1. Install Railway CLI
```bash
npm i -g @railway/cli
```

### 2. Initialize Railway Project
```bash
railway login
railway init
```

### 3. Set Environment Variables
```bash
railway variables set ANTHROPIC_API_KEY=your_key
railway variables set SUPABASE_URL=your_url
railway variables set SUPABASE_KEY=your_key
railway variables set SUPABASE_JWT_SECRET=your_secret
railway variables set ENVIRONMENT=production
```

### 4. Deploy
```bash
railway up
```

## Testing

### Test Authentication
```bash
# Get a JWT token from your Supabase project
curl -X POST http://localhost:8000/api/generate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"requirements": "Create a simple user API"}'
```

### Test Health Check
```bash
curl http://localhost:8000/health
```

## Cost Monitoring

Monitor API usage to stay within budget:
- Track requests in Supabase dashboard
- Monitor Anthropic API usage
- Daily cost cap enforced in code

## Troubleshooting

### "Invalid authentication token"
- Verify `SUPABASE_JWT_SECRET` matches your Supabase project
- Check token hasn't expired (default: 1 hour)
- Ensure token is from the correct Supabase project

### "Rate limit exceeded"
- Wait for rate limit window to reset (1 hour)
- Check `user_usage` table for current counts
- Adjust `RATE_LIMIT_GENERATIONS` if needed

### "Code generation failed"
- Verify `ANTHROPIC_API_KEY` is valid
- Check API quota and billing
- Review agent logs for specific errors

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

MIT License - see LICENSE file for details
