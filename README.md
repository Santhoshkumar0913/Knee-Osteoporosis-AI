# Knee Osteoporosis AI

AI-assisted screening using knee X-ray images and patient clinical information.

## Project Overview

This is a local-first web application that uses trained ML models to analyze knee X-ray images and predict osteoporosis conditions along with T-score and Z-score estimates.

## Technology Stack

- **Frontend**: React + TypeScript + Vite
- **Backend**: FastAPI + Python
- **Database**: PostgreSQL (via Docker)
- **Admin Interface**: pgAdmin (via Docker)
- **ML Models**: PyTorch (DINOv2), scikit-learn (Random Forest, Gradient Boosting)
- **Storage**: Local file system

## Prerequisites

- Docker Desktop (installed and running)
- Python 3.13+
- Node.js + npm
- Git

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Santhoshkumar0913/Knee-Osteoporosis-AI.git
cd Knee-Osteoporosis-AI
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your preferred credentials (default values are provided for local development).

### 3. Start PostgreSQL and pgAdmin

```bash
docker-compose up -d
```

This will start:
- PostgreSQL on `localhost:5432`
- pgAdmin on `localhost:5050`

### 4. Install Backend Dependencies

```bash
cd backend
python -m pip install -r requirements.txt
```

**Note**: If you encounter build errors with pydantic-core on Windows, you may need to install Visual Studio Build Tools with C++ support, or use pre-built wheels.

### 5. Install ML Models

**IMPORTANT**: You must manually copy the trained model files to the backend/models directory:

1. Copy these 4 files from your Google Colab training:
   - `dinov2_experiment2_best.pth`
   - `t_score_random_forest.joblib`
   - `z_score_gradient_boosting.joblib`
   - `model_metadata.json`

2. Place them in: `backend/models/`

3. Verify the files are present:
   ```bash
   ls backend/models/
   ```

See `backend/models/README.md` for detailed instructions.

### 6. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 7. Start the Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`

### 8. Start the Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Application Workflow

1. **Home Page**: Start with the landing page
2. **Patients**: Create or select a patient
3. **New Analysis**: Upload X-ray and enter clinical information
4. **Results**: View ML predictions and bone score estimates
5. **History**: Track patient analysis history

## Database Access

### pgAdmin

- URL: `http://localhost:5050`
- Email: (from .env, default: admin@example.com)
- Password: (from .env, default: admin)

### Direct PostgreSQL Connection

- Host: `localhost`
- Port: `5432`
- Database: `osteoporosis_ai`
- User: `postgres`
- Password: (from .env)

## Project Structure

```
Knee-Osteoporosis-AI/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── api/                 # API endpoints
│   │   ├── core/                # Configuration
│   │   ├── db/                  # Database models
│   │   ├── schemas/             # Pydantic schemas
│   │   └── services/            # Business logic (ML, storage)
│   ├── models/                  # ML model files (user-provided)
│   ├── requirements.txt         # Python dependencies
│   └── tests/                   # Backend tests
├── frontend/
│   ├── src/
│   │   ├── pages/               # React pages
│   │   ├── components/          # React components
│   │   ├── services/            # API client
│   │   └── types/               # TypeScript types
│   └── package.json             # Node dependencies
├── storage/
│   └── uploads/                 # Local image storage
├── docker-compose.yml           # PostgreSQL + pgAdmin
├── .env.example                 # Environment template
└── .gitignore                   # Git ignore rules
```

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/patients` - Create patient
- `GET /api/patients` - List all patients
- `GET /api/patients/{id}` - Get patient details
- `DELETE /api/patients/{id}` - Delete patient
- `POST /api/analyses` - Create analysis (with image upload)
- `GET /api/analyses/patient/{patient_id}` - Get patient analyses
- `GET /api/analyses/{id}` - Get analysis details
- `DELETE /api/analyses/{id}` - Delete analysis

## Testing

### Manual Testing

1. Start all services (Docker, backend, frontend)
2. Open `http://localhost:5173` in your browser
3. Create a patient
4. Upload a knee X-ray image
5. Enter clinical information
6. Run analysis and view results
7. Check patient history

### Database Verification

```bash
# Connect to PostgreSQL
docker exec -it osteoporosis_postgres psql -U postgres -d osteoporosis_ai

# Check tables
\dt
SELECT * FROM patients;
SELECT * FROM analyses;
```

## Stopping the Application

```bash
# Stop Docker containers
docker-compose down

# Stop backend (Ctrl+C in terminal)
# Stop frontend (Ctrl+C in terminal)
```

## Troubleshooting

### Backend fails to start
- Verify ML model files are in `backend/models/`
- Check Python dependencies are installed
- Verify database connection in `.env`

### Frontend fails to start
- Verify Node.js and npm are installed
- Check dependencies are installed with `npm install`

### Database connection issues
- Verify Docker containers are running: `docker ps`
- Check database credentials in `.env`
- Verify PostgreSQL is healthy: `docker-compose ps`

### ML model loading errors
- Verify all 4 model files are present
- Check file names match exactly
- Review backend logs for specific errors

## Important Notes

- **ML Models**: Do not retrain models - use the provided trained files
- **Image Storage**: Images are stored locally in `storage/uploads/`
- **Database**: PostgreSQL data persists in Docker volumes
- **Security**: This is a local development application - not for production use
- **Medical Disclaimer**: This is an AI-assisted screening tool, not a clinical diagnostic system

## Future Enhancements

The application is structured to support future additions:
- RAG (Retrieval-Augmented Generation) for medical knowledge
- LLM integration for clinical report generation
- XAI (Explainable AI) with Grad-CAM visualizations
- Authentication and user management
- Cloud deployment options

## License

This project is part of the Knee Osteoporosis AI research initiative.

## Support

For issues or questions, please refer to the project documentation or contact the development team.
