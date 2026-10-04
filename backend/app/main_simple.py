"""
AI Real-Time Coding Screener - Simplified Main Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create the FastAPI application
app = FastAPI(
    title="AI Real-Time Coding Screener",
    description="Real-time code analysis with progressive mentoring hints",
    version="1.0.0",
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI Real-Time Coding Screener API", "version": "1.0.0"}


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Real-Time Coding Screener",
        "version": "1.0.0",
    }


@app.post("/api/v1/analyze")
async def analyze_code(request_data: dict):
    """Basic code analysis endpoint"""
    code = request_data.get("code", "")
    session_token = request_data.get("session_token", "demo")

    # Simple analysis
    analysis = {
        "cached": False,
        "analysis_id": 1,
        "findings": {
            "syntax_errors": [],
            "diagnostics": [
                {
                    "line": 1,
                    "column": 1,
                    "message": "Code analysis working! Your AI Real-Time Coding Screener is running.",
                    "severity": "info",
                    "source": "demo_analyzer",
                    "category": "demo",
                }
            ],
            "execution_result": {"success": True, "output": "Demo mode active"},
            "code_quality": {"lines_of_code": len(code.splitlines())},
        },
        "severity": "info",
        "is_blocking": False,
    }

    return analysis


@app.post("/api/v1/hints/request")
async def request_hint(request_data: dict):
    """AI hint generation endpoint with multi-provider support"""
    session_token = request_data.get("session_token", "demo")
    hint_level = request_data.get("hint_level", 1)
    provider = request_data.get("provider")

    # Demo hints for each level
    demo_hints = {
        1: "H1 General Hint: Consider the basic structure and logic flow of your code.",
        2: "H2 Specific Hint: Look at your variable names and function definitions more closely.",
        3: "H3 Detailed Hint: Check your loop conditions and return statements for correctness.",
        4: "H4 Solution Hint: Here's a complete working implementation you can study and learn from.",
    }

    hint = {
        "cached": False,
        "hint_id": hint_level,
        "hint_text": demo_hints.get(hint_level, "Demo hint for your code!"),
        "hint_level": hint_level,
        "provider": provider or "demo",
        "model": "demo-model",
        "generation_time_ms": 150,
        "available_providers": ["groq", "openrouter", "nvidia_nim", "google", "local"],
    }

    return hint


@app.get("/api/v1/providers")
async def get_providers():
    """Get available AI providers"""
    return {
        "available": ["groq", "openrouter", "nvidia_nim", "google", "local"],
        "current": {
            "provider": "groq",
            "model": "llama3-8b-8192",
            "max_tokens": 2048,
            "temperature": 0.7,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
