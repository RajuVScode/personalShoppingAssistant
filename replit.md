# AI Shopping Experience

## Overview

This is an AI-powered personalized shopping assistant built with a multi-agent architecture. The system combines a React frontend with a Python FastAPI backend that orchestrates multiple specialized AI agents to provide intelligent product recommendations based on user intent, customer profile, and environmental context (weather, events, trends).

The application supports travel planning use cases where users can get clothing and product recommendations based on their destination, travel dates, activities, and weather conditions.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: React with TypeScript using Vite as the build tool
- **Routing**: Wouter for lightweight client-side routing
- **State Management**: TanStack React Query for server state and data fetching
- **UI Components**: shadcn/ui component library with Radix UI primitives
- **Styling**: Tailwind CSS v4 with CSS variables for theming

### Backend Architecture
- **Primary Backend**: Python FastAPI server running on port 8000
- **Proxy Layer**: Express.js server that proxies `/api` requests to the Python backend
- **Agent Orchestration**: LangGraph-based multi-agent system with the following agents:
  - **Shopping Orchestrator**: Coordinates all agents and manages conversation flow
  - **Clarifier Agent**: Captures and normalizes user intent through conversational clarification
  - **Intent Processor**: Extracts structured shopping intent from natural language
  - **Customer 360 Agent**: Fetches customer profile, preferences, and purchase history
  - **Context Aggregator**: Combines intent, customer context, and environmental data
  - **Product Recommender Agent**: RAG-based product recommendations using vector search

### Data Storage
- **Primary Database**: PostgreSQL via Drizzle ORM (shared schema in `shared/schema.ts`)
- **Python ORM**: SQLAlchemy for backend database operations
- **Vector Store**: Custom in-memory vector store with deterministic embeddings for product similarity search
- **Session Storage**: In-memory storage for user sessions (can be extended to PostgreSQL)

### AI/LLM Integration
- **LLM Provider**: Azure OpenAI with gpt-4o-mini model
- **Framework**: LangChain for LLM interactions, LangGraph for agent orchestration
- **RAG Pipeline**: Product catalog indexed with semantic embeddings for retrieval-augmented generation

### Authentication
- Simple customer ID + password authentication
- Customer data stored in PostgreSQL with login endpoint at `/api/login`

## External Dependencies

### AI Services
- **Azure OpenAI**: Primary LLM provider for all agent interactions
  - Requires `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`

### Weather & Context APIs
- **Open-Meteo API**: Free weather data API (no key required)
- **OpenWeather API**: Optional weather service (`OPENWEATHER_API_KEY`)

### Database
- **PostgreSQL**: Primary data store
  - Requires `DATABASE_URL` environment variable
  - Schema managed via Drizzle Kit migrations

### Build & Development
- **Vite**: Frontend build tool with HMR
- **esbuild**: Server-side bundling for production
- **tsx**: TypeScript execution for development server

### Key NPM Dependencies
- React 18, TanStack Query, Wouter
- shadcn/ui, Radix UI, Tailwind CSS
- Drizzle ORM with PostgreSQL driver

### Key Python Dependencies
- FastAPI, Uvicorn
- LangChain, LangGraph
- SQLAlchemy, psycopg2
- Pydantic for schema validation