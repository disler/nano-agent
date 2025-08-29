# Tech Stack

## Context

CDR (Call Detail Record) Analytics Application - Multi-service architecture for telecommunications data analysis.

## Backend
- App Framework: FastAPI (Python)
- Language: Python 3.11+
- Primary Database: PostgreSQL (partitioned CDR events)
- Graph Database: Neo4j (network analysis)
- Cache/Queue: Redis (Celery broker)
- ORM: SQLAlchemy with psycopg2
- Task Queue: Celery with Redis broker
- Analytics Library: cdr_lib (pandas, scikit-learn)
- WebSocket Support: FastAPI WebSocket for real-time updates

## Frontend
- JavaScript Framework: React 18
- Build Tool: Create React App
- Package Manager: npm
- Charting: Recharts
- HTTP Client: Axios
- File Upload: react-dropzone
- Date Handling: date-fns
- Icons: Lucide React components
- UI Style: Custom CSS with dark mode support

## Infrastructure & Deployment
- Container Platform: Podman (MacBook optimized)
- Container Orchestration: podman-compose
- Service Mesh: Nginx proxy (internal routing)
- Monitoring: Grafana
- Database Hosting: Containerized PostgreSQL with partitioning
- Graph Database: Containerized Neo4j
- Cache: Containerized Redis
- Worker Services: Celery workers (async processing)
- Port Management: Dynamic port discovery (avoid conflicts)

## Development & Testing
- Backend Testing: pytest, pytest-asyncio, httpx
- Frontend Testing: react-scripts test
- Integration Testing: Custom test scripts
- API Documentation: FastAPI auto-generated docs (/docs)
- MCP Server: Model Context Protocol for Claude integration
- Version Control: Git with main/integration branches

