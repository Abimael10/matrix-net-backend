# Matrix-Net Backend

*** Still under development ***

## Overview

Social media application backend built with FastAPI. It implements an event-driven architecture with a service layer that follows command/handler/message bus patterns. The application uses SQLAlchemy for database operations with support for both SQLite (development) and PostgreSQL (production) databases.

### Technologies

- **Framework**: FastAPI
- **Database**: SQLAlchemy with support for SQLite and PostgreSQL
- **Authentication**: JWT tokens with access/refresh token system
- **Architecture**: Event-driven service layer with commands, handlers, and message bus
- **File Storage**: Backblaze B2 integration **Not integrated yet**
- **Monitoring**: Sentry for error tracking **totally optional and personally I do not like it**

### Architecture Pattern

- **Domain Layer**: Contains business entities, commands, and events
- **Service Layer**: Implements command handlers and business logic
- **Adapters**: Handles persistence
- **Entrypoints**: API endpoints and request/response schemas
- **Bootstrap**: Initializes the message bus and dependency injection

## Structure

```
src/
├── adapters/          # Persistence, notifications, and storage adapters
├── domain/            # Business entities, commands, and events
├── entrypoints/       # API routers and request/response schemas
├── service_layer/     # Command handlers and business logic
├── views/             # Database query helpers
├── bootstrap.py       # Application initialization and message bus setup
├── config.py          # Configuration management
├── db.py              # Database models and connection setup
├── main.py            # FastAPI application and middleware
└── security.py        # Authentication and authorization logic
```

## Building and Running

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Setup
1. Create and activate a virtual environment:
   ```bash
   python -m venv venv && source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt -r dev-requirements.txt
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Set appropriate values for your environment (ENV, DATABASE_URI, SECRET_KEY, etc.)

### Running the Application
- **Development**: `ENV=dev DEV_DATABASE_URI=sqlite:///./local.db DEV_SECRET_KEY=dev-secret uvicorn src.main:app --reload`
- **Production**: Configure appropriate environment variables and run with a production WSGI server

### Testing
- Run tests: `pytest`

## Development Conventions

### Architecture Patterns
- Commands represent user intentions (actions to be performed)
- Events represent things that have happened (state changes)
- Handlers process commands and emit events
- Aggregates maintain business invariants
- Repositories provide persistence abstraction

### Error Handling
- Custom domain exceptions for business logic errors
- HTTP exceptions for API endpoints
- Logging for debugging and monitoring

### Security
- Passwords are hashed using bcrypt
- JWT tokens for authentication with configurable expiration
- Input validation using Pydantic schemas
- SQL injection protection through SQLAlchemy ORM

## Environment Configuration

The application supports three environments:
- **Development** (`ENV=dev`): Uses DEV_ prefixed environment variables
- **Production** (`ENV=prod`): Uses PROD_ prefixed environment variables or standard names
- **Test** (`ENV=test`): Uses TEST_ prefixed environment variables with defaults

Key configuration variables:
- `DATABASE_URI`: Database connection string
- `SECRET_KEY`: Secret key for JWT token signing
- `B2_KEY_ID`, `B2_APPLICATION_KEY`, `B2_BUCKET_NAME`: Backblaze B2 storage configuration
- `SENTRY_DSN`: Sentry error tracking configuration

## API Endpoints

The API is organized into the following routers:
- `/api/register` - User registration
- `/api/token` - Authentication token generation
- `/api/token/refresh/` - Token refresh
- `/api/user/me/` - Current user profile
- `/api/user/` - User settings (password change, account deletion)
- `/api/posts/` - Post management (including delete functionality)
- `/api/comments/` - Comment management (including delete functionality)
- `/api/likes/` - Like functionality
- `/api/upload/` - File upload endpoints --pending--

New endpoints added:
- `DELETE /api/posts/{post_id}` - Delete a post (user must be the owner)
- `DELETE /api/comments/{comment_id}` - Delete a comment (user must be the owner)

## Testing Strategy

The application includes:
- Unit tests for business logic
- Integration tests for API endpoints
- Test fixtures for database management
- Mocking capabilities for external dependencies