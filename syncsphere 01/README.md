# SyncSphere AI

SyncSphere AI is an enterprise-grade, multi-agent workflow orchestration platform powered by the Model Context Protocol (MCP).

## System Requirements

- Docker and Docker Compose
- Python 3.11+ (for local development outside Docker)

## Project Structure

This project is organized as a monorepo:

- `backend/`: Core platform services (FastAPI, Motor/Beanie ODM, Redis, AsyncIO).
- `frontend/`: React SPA with TypeScript, TailwindCSS, and React Flow.
- `connectors/`: Pluggable MCP connectors.
- `infrastructure/`: Deployment and orchestration files.

## Running Locally

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Start the infrastructure and services using Docker Compose:
   ```bash
   docker-compose up -d --build
   ```

3. Access the API documentation at:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

4. Run tests:
   ```bash
   make test
   ```
