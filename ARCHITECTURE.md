# HiveCodr Three-Agent Architecture

## Overview

HiveCodr uses a sophisticated three-agent sequential workflow to generate production-ready full-stack applications. This architecture separates concerns between **design**, **backend implementation**, and **frontend implementation**, resulting in thoughtful, well-structured, and complete applications from plain English requirements.

## Agent Workflow

```
User Requirements
       │
       ▼
┌──────────────────┐
│  ARCHITECT BEE   │  Phase 1: Design
│                  │
│  Analyzes &      │  - Analyzes requirements
│  Designs         │  - Designs database schema
│                  │  - Plans API structure
│                  │  - Defines validation rules
└────────┬─────────┘
         │
         │ Architecture Specification (JSON)
         │
         ▼
┌──────────────────┐
│  DEVELOPER BEE   │  Phase 2: Backend
│                  │
│  Implements      │  - Generates SQLAlchemy models
│  Backend         │  - Creates Pydantic schemas
│                  │  - Builds FastAPI routes
│                  │  - Assembles main.py
└────────┬─────────┘
         │
         │ Backend Code (models, schemas, routes, main)
         │
         ▼
┌──────────────────┐
│  FRONTEND BEE    │  Phase 3: Frontend
│                  │
│  Implements      │  - Generates Next.js 14 app
│  Frontend        │  - Creates TypeScript types
│                  │  - Builds React components
│                  │  - Implements API client
│                  │  - Adds Tailwind styling
└────────┬─────────┘
         │
         ▼
   Full-Stack App
   (Backend + Frontend)
```

## Phase 1: Architect Bee

**Role:** Senior Software Architect
**Goal:** Analyze requirements and design robust database schemas and API structures
**Location:** `app/agents/architect_bee.py`

### Responsibilities

1. **Requirement Analysis**
   - Interprets plain English requirements
   - Identifies entities and relationships
   - Considers scalability and maintainability

2. **Database Schema Design**
   - Defines tables with appropriate fields
   - Specifies data types (Integer, String, Text, Boolean, DateTime, etc.)
   - Establishes relationships (one-to-many, many-to-one, many-to-many)
   - Adds indexes for performance
   - Includes timestamps (created_at, updated_at)

3. **API Structure Planning**
   - Designs RESTful endpoints
   - Specifies HTTP methods (GET, POST, PUT, DELETE)
   - Defines request/response schemas
   - Plans query parameters for filtering and pagination

4. **Validation Rules**
   - Sets field constraints (required, min/max length, patterns)
   - Defines business rules
   - Plans error handling

### Output Format

The Architect Bee produces a JSON specification:

```json
{
  "database_schema": {
    "tables": [
      {
        "name": "table_name",
        "description": "What this table stores",
        "fields": [
          {
            "name": "field_name",
            "type": "SQLAlchemy type",
            "constraints": ["primary_key", "nullable", "unique", "index"],
            "description": "Field purpose",
            "max_length": 200
          }
        ],
        "relationships": [
          {
            "type": "one_to_many",
            "target_table": "related_table",
            "description": "Relationship explanation"
          }
        ]
      }
    ]
  },
  "api_endpoints": [
    {
      "method": "POST",
      "path": "/api/v1/resource",
      "description": "Endpoint purpose",
      "request_body": {
        "field_name": {
          "type": "str",
          "required": true,
          "description": "Field description"
        }
      },
      "response": {
        "status_code": 200,
        "description": "Response description"
      },
      "query_parameters": [
        {
          "name": "param_name",
          "type": "str",
          "required": false,
          "default": "default_value",
          "description": "Parameter purpose"
        }
      ]
    }
  ],
  "validation_rules": {
    "entity_name": [
      {
        "field": "field_name",
        "rules": ["min_length: 1", "max_length: 200"],
        "error_message": "Validation error message"
      }
    ]
  },
  "business_logic": [
    "Key business rule 1",
    "Key business rule 2"
  ]
}
```

## Phase 2: Developer Bee

**Role:** Senior FastAPI Developer
**Goal:** Generate production-ready FastAPI CRUD code based on architecture specification
**Location:** `app/agents/developer_bee.py`

### Responsibilities

1. **Model Implementation**
   - Converts schema design to SQLAlchemy models
   - Implements all fields with correct types
   - Adds relationships and constraints
   - Includes proper indexes

2. **Schema Creation**
   - Builds Pydantic v2 schemas
   - Implements all validation rules
   - Creates separate schemas for Create, Update, Response
   - Adds proper field descriptions

3. **Route Development**
   - Implements all API endpoints as designed
   - Adds full CRUD operations
   - Includes error handling with HTTPException
   - Implements filtering, pagination, and search
   - Uses proper HTTP status codes

4. **Application Assembly**
   - Creates main.py with FastAPI setup
   - Configures CORS middleware
   - Sets up database initialization
   - Adds health check endpoints

### Input

Takes the Architect Bee's specification and the original requirements.

### Output

Generates four Python files:

```python
{
  "models": "# SQLAlchemy models.py",
  "schemas": "# Pydantic schemas.py",
  "routes": "# FastAPI routes.py",
  "main": "# FastAPI main.py"
}
```

## Phase 3: Frontend Bee

**Role:** Senior Frontend Developer (Next.js & TypeScript Specialist)
**Goal:** Generate production-ready Next.js 14 applications with TypeScript and Tailwind CSS based on FastAPI backend
**Location:** `app/agents/frontend_bee.py`

### Responsibilities

1. **Project Setup**
   - Generates package.json with all dependencies
   - Creates TypeScript configuration (tsconfig.json)
   - Sets up Tailwind CSS with HiveCodr color palette
   - Configures Next.js 14 App Router

2. **Component Generation**
   - Creates reusable UI components (Button, Input, Card, etc.)
   - Generates entity-specific components (List, Detail, Form)
   - Builds layout components (Navigation, Footer)
   - Implements loading and error states

3. **API Integration**
   - Generates TypeScript types from backend schemas
   - Creates type-safe API client
   - Implements CRUD operations for each entity
   - Adds proper error handling and retries

4. **Form Implementation**
   - Integrates React Hook Form
   - Creates validation schemas
   - Implements field-level validation
   - Adds error messages and success notifications

5. **Styling & Responsiveness**
   - Applies HiveCodr color palette (#220901, #621708, #941B0C, #BC3908, #F6AA1C)
   - Implements mobile-first responsive design
   - Creates accessible components (ARIA labels, keyboard navigation)
   - Adds loading states and transitions

### Input

Takes the generated backend code, original requirements, and architecture specification.

### Output

Generates a complete Next.js 14 application:

```typescript
{
  // Configuration
  "package.json": "...",
  "tsconfig.json": "...",
  "tailwind.config.ts": "...",
  "next.config.js": "...",

  // App Router
  "app/layout.tsx": "...",
  "app/page.tsx": "...",
  "app/globals.css": "...",

  // Entity Pages (for each entity)
  "app/[entity]/page.tsx": "...",          // List view
  "app/[entity]/[id]/page.tsx": "...",     // Detail view
  "app/[entity]/new/page.tsx": "...",      // Create form
  "app/[entity]/[id]/edit/page.tsx": "...", // Edit form

  // Components
  "components/ui/Button.tsx": "...",
  "components/ui/Input.tsx": "...",
  "components/ui/Card.tsx": "...",
  "components/layout/Navigation.tsx": "...",
  "components/[entity]/[Entity]List.tsx": "...",
  "components/[entity]/[Entity]Form.tsx": "...",

  // API & Utilities
  "lib/api/client.ts": "...",
  "lib/api/[entity].ts": "...",
  "lib/types/[entity].ts": "...",
  "lib/validations.ts": "...",
  "lib/utils.ts": "..."
}
```

### HiveCodr Color Palette

All generated frontends use the official HiveCodr colors:

- **Primary (Dark Brown):** #220901
- **Secondary (Brown):** #621708
- **Accent (Red):** #941B0C
- **Highlight (Orange):** #BC3908
- **Gold (Yellow):** #F6AA1C

### Features

- ✅ Next.js 14 App Router (server & client components)
- ✅ TypeScript for full type safety
- ✅ Tailwind CSS with HiveCodr branding
- ✅ React Hook Form for forms
- ✅ Comprehensive error handling
- ✅ Loading states and skeletons
- ✅ Responsive mobile-first design
- ✅ Accessibility (WCAG 2.1)
- ✅ Search, filter, and pagination
- ✅ Success/error notifications

## API Endpoint: `/api/generate`

**Method:** POST
**Authentication:** Required (JWT Bearer token)
**Rate Limiting:** Configured per user

### Request

```json
{
  "requirements": "Plain English description of what to build"
}
```

### Response

```json
{
  "id": "generation_id",
  "code": {
    "backend": {
      "models": "...",
      "schemas": "...",
      "routes": "...",
      "main": "..."
    },
    "frontend": {
      "package.json": "...",
      "tsconfig.json": "...",
      "app/layout.tsx": "...",
      "app/page.tsx": "...",
      "components/ui/Button.tsx": "...",
      ... (all frontend files)
    }
  },
  "agent_log": "Combined logs from all three agents",
  "created_at": "2026-01-17T12:00:00"
}
```

### Process Flow

```python
async def generate_code(request, current_user, supabase):
    # 1. Rate limiting check
    await check_rate_limit(current_user, supabase)

    # 2. Phase 1: Architect Bee
    architecture_result = architect_bee.analyze_requirements(request.requirements)
    architecture_spec = architecture_result["specification"]

    # 3. Phase 2: Developer Bee
    backend_result = developer_bee.generate_crud_code(
        requirements=request.requirements,
        architecture_spec=architecture_spec
    )

    # 4. Phase 3: Frontend Bee
    frontend_result = frontend_bee.generate_frontend_code(
        backend_code=backend_result["code"],
        requirements=request.requirements,
        architecture_spec=architecture_spec
    )

    # 5. Store both backend and frontend in database
    # 6. Increment usage
    # 7. Return generated full-stack application
```

## Database Storage

Generated code is stored in Supabase with:

- User ID (who generated it)
- Original requirements
- Architecture specification
- Generated backend code files
- Generated frontend code files
- Agent logs (all three phases)
- Timestamps

```json
{
  "user_id": "uuid",
  "requirements": "User's input",
  "generated_code": {
    "backend": {
      "models": "...",
      "schemas": "...",
      "routes": "...",
      "main": "..."
    },
    "frontend": {
      "package.json": "...",
      "app/layout.tsx": "...",
      "components/ui/Button.tsx": "...",
      ... (all frontend files)
    }
  },
  "agent_outputs": {
    "architecture_spec": {...},
    "architect_log": "...",
    "developer_log": "...",
    "frontend_log": "...",
    "combined_log": "...",
    "backend_raw_response": "...",
    "frontend_raw_response": "..."
  },
  "created_at": "timestamp"
}
```

## Security Features

All existing security features are maintained:

1. **Authentication**
   - JWT token validation
   - Supabase integration
   - User identification

2. **Rate Limiting**
   - Per-user generation limits
   - Configurable time windows
   - Usage tracking

3. **Input Validation**
   - Bleach sanitization
   - Length constraints
   - XSS prevention

4. **Error Handling**
   - Comprehensive exception handling
   - User-friendly error messages
   - Detailed logging

## Benefits of Three-Agent Architecture

### 1. Complete Full-Stack Generation
- **Backend and frontend** generated from single prompt
- Automatic type consistency between backend and frontend
- No manual integration needed
- Production-ready full-stack applications in minutes

### 2. Separation of Concerns
- **Design** separated from **backend** separated from **frontend**
- Each agent specializes in their domain
- Clear separation between architecture, API, and UI

### 3. Better Code Quality
- Thoughtful database design before implementation
- Consistent API structure
- Type-safe frontend from backend schemas
- Proper planning of relationships and constraints

### 4. Transparency
- Users can see the architecture specification
- Design decisions are documented across all layers
- Complete visibility into backend and frontend generation
- Easier to understand the reasoning

### 5. Brand Consistency
- HiveCodr color palette applied to all frontends
- Consistent design language across generated apps
- Professional, branded user interfaces

### 6. Flexibility
- Can regenerate code from same architecture
- Can modify architecture and regenerate both backend and frontend
- Architecture spec can be version controlled
- Easy to customize generated components

### 7. Scalability
- Easy to add more specialized agents (Testing, DevOps, Mobile)
- Can introduce review/optimization agents
- Modular and maintainable
- Architecture can guide multiple frontend types (Web, Mobile, Desktop)

## Usage Example

```python
import httpx

headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}
payload = {
    "requirements": """
    Create a task management API with:
    - CRUD operations for tasks
    - Task fields: title, description, priority, status, due_date
    - Filtering by status and priority
    - Search by title and description
    - Pagination support
    """
}

response = httpx.post(
    "http://localhost:8000/api/generate",
    headers=headers,
    json=payload,
    timeout=600.0  # Two agents take longer
)

result = response.json()
print(f"Generation ID: {result['id']}")
print(f"Generated files: {result['code'].keys()}")
```

## Configuration

Both agents use the same configuration from `.env`:

```bash
ANTHROPIC_API_KEY=your_api_key
CLAUDE_MODEL=claude-sonnet-4-20250514
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_JWT_SECRET=your_jwt_secret
```

## Future Enhancements

Potential additions to the agent workflow:

1. **Reviewer Bee** - Code review and quality checks
2. **Tester Bee** - Generate unit tests
3. **Optimizer Bee** - Performance optimization suggestions
4. **Security Bee** - Security vulnerability scanning
5. **Documentation Bee** - API documentation generation

## Monitoring and Debugging

All agent interactions are logged:

- Phase 1: Architecture design process
- Phase 2: Code generation process
- Combined log with both phases
- Stored in database for analysis

Use the combined log to understand:
- How requirements were interpreted
- What design decisions were made
- How code was generated
- Any issues or edge cases encountered

## Conclusion

The two-agent architecture provides a robust, scalable, and maintainable approach to AI-powered code generation. By separating architectural design from implementation, HiveCodr produces more thoughtful, well-structured, and production-ready code.
