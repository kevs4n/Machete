#!/usr/bin/env python3
"""
Minimal FastAPI test for MACHETE Platform
"""

from fastapi import FastAPI
import uvicorn

# Create minimal app
app = FastAPI(title="MACHETE Test API")

@app.get("/")
async def root():
    return {"status": "MACHETE Test API is running!", "version": "test"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "MACHETE Test"}

if __name__ == "__main__":
    print("🔪 Starting MACHETE Test API...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
