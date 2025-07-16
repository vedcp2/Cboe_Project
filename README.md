# Cboe Intelligence Hub

A full-stack generative AI application for data analysis and insights, built with FastAPI backend and React frontend.

## 🐳 Docker Setup

### Prerequisites

- Docker and Docker Compose installed
- `.env` file with required environment variables (see Configuration section)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/vedcp2/cboe-intelligence-hub.git               
   cd cboe-intelligence-hub
   ```

2. **Create your `.env` file**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/

### Manual Docker Commands

**Build the backend image:**
```bash
docker build -t cboe-intelligence-hub-backend .
```

**Build the frontend image:**
```bash
docker build -t cboe-intelligence-hub-frontend ./frontend
```

**Run the backend container:**
```bash
docker run -p 8000:8000 --env-file .env cboe-intelligence-hub-backend
```

**Run the frontend container:**
```bash
docker run -p 3000:3000 cboe-intelligence-hub-frontend
```

**Run with environment variables:**
```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key_here \
  -e SNOWFLAKE_USER=your_user \
  -e SNOWFLAKE_PASSWORD=your_password \
  cboe-intelligence-hub
```

## 🔧 Configuration

### Required Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Snowflake Configuration
SNOWFLAKE_USER=your_snowflake_username
SNOWFLAKE_PASSWORD=your_snowflake_password
SNOWFLAKE_ACCOUNT=your_snowflake_account
SNOWFLAKE_WAREHOUSE=your_warehouse_name
SNOWFLAKE_DATABASE=your_database_name
SNOWFLAKE_SCHEMA=your_schema_name
SNOWFLAKE_ROLE=SYSADMIN

# Optional: Application Configuration
LOG_LEVEL=INFO
```

### Security Notes

- **Never commit your `.env` file** - it's already in `.gitignore`
- Use strong passwords and rotate API keys regularly
- Consider using Docker secrets for production deployments

## 🚀 Development

### Development with Docker Compose

For development with hot-reload:

```bash
# Start development environment
docker-compose up

# Rebuild after dependency changes
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Local Development (without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Run the application
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🏗️ Production Deployment

### Production Docker Build

```bash
# Build production image
docker build -t cboe-intelligence-hub:production .

# Run production container
docker run -d \
  --name cboe-app \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  cboe-intelligence-hub:production
```

### Health Checks

The application includes built-in health checks:

- **Docker Health Check**: Automatically checks application health
- **Manual Health Check**: `curl http://localhost:8000/`
- **API Status**: `curl http://localhost:8000/docs`

### Monitoring

Monitor your application:

```bash
# View container logs
docker logs cboe-app -f

# Check container status
docker ps

# View resource usage
docker stats cboe-app
```

## 📚 API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔍 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Find process using port 8000
   lsof -i :8000
   # Kill the process or use a different port
   docker run -p 8001:8000 --env-file .env cboe-intelligence-hub
   ```

2. **Environment variables not loading**
   ```bash
   # Check if .env file exists
   ls -la .env
   # Verify environment variables in container
   docker exec cboe-app env | grep OPENAI
   ```

3. **Build failures**
   ```bash
   # Clean build (no cache)
   docker build --no-cache -t cboe-intelligence-hub .
   # Remove old images
   docker system prune -a
   ```

4. **Database connection issues**
   - Verify Snowflake credentials in `.env`
   - Check network connectivity
   - Ensure firewall allows outbound connections

### Logs and Debugging

```bash
# View application logs
docker-compose logs backend
docker-compose logs frontend

# View all logs
docker-compose logs

# Interactive debugging
docker exec -it cboe-intelligence-hub-backend-1 /bin/bash
docker exec -it cboe-intelligence-hub-frontend-1 /bin/sh

# Check environments
docker exec cboe-intelligence-hub-backend-1 python --version
docker exec cboe-intelligence-hub-frontend-1 node --version
```

## 🛠️ Architecture

- **Frontend**: React with TypeScript, served via Node.js
- **Backend**: FastAPI with Python 3.12
- **Database**: Snowflake integration
- **AI**: OpenAI GPT integration with LangChain
- **Containerization**: Docker with multi-stage builds
- **Security**: Non-root users, minimal base images
- **Ports**: Frontend (3000), Backend (8000)

