from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Import your main app
from main import app

# Configure CORS for Vercel deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this with your frontend domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vercel requires the app to be named 'app' or 'handler'
handler = app
