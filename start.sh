#!/bin/bash
set -e

APP_MODE=${APP_MODE:-"streamlit"}

echo "Starting FoodLens AI in mode: $APP_MODE..."

if [ "$APP_MODE" = "api" ]; then
    echo "Running FastAPI server on port 8000..."
    exec uvicorn api.main:app --host 0.0.0.0 --port 8000
elif [ "$APP_MODE" = "both" ]; then
    echo "Running FastAPI in background on port 8000..."
    uvicorn api.main:app --host 0.0.0.0 --port 8000 &
    echo "Running Streamlit on port 8501..."
    exec streamlit run app/Home.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
else
    echo "Running Streamlit on port 8501..."
    exec streamlit run app/Home.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
fi
