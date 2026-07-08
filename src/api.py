import os
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine.cube_integration import CubeIntegrationPipeline

load_dotenv()

app = FastAPI(title="AI Query Agent API")

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = CubeIntegrationPipeline(debug=True)

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        print(f"\n[API] Received query: {req.message}")
        response = pipeline.run(req.message)
        return {"response": response}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"response": "I cannot retrieve this information because the data is not sufficient."}

# Resolve frontend directory
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'frontend'))

# Mount static files (JS, CSS, images) if they exist
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
async def read_index():
    index_path = os.path.join(frontend_dir, 'index.html')
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend index.html not found in src/frontend/"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
