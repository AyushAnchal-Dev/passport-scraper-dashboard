import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base, SessionLocal
from app.core.config import settings
from app.api.endpoints import router, manager
from app.services.scraper_service import ScraperService
from app.workers.celery_worker import process_and_save_posts

# Use FastAPI lifespan to manage background tasks
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize Database Tables (Auto-migrate)
    print("Database: Initializing schema tables...")
    
    # Enable vector extension in Postgres before creating models
    if not settings.DATABASE_URL.startswith("sqlite"):
        from sqlalchemy import text
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                print("Database: Enabled pgvector extension successfully.")
        except Exception as e:
            print(f"Database: Failed to enable pgvector extension: {e}")
            
    Base.metadata.create_all(bind=engine)
    
    # 2. Run initial scrape & cluster immediately so demo works on startup
    print("Startup: Running initial scraping and NLP processing pipeline...")
    db = SessionLocal()
    try:
        raw_posts = ScraperService.fetch_all()
        new_posts = process_and_save_posts(db, raw_posts)
        print(f"Startup: Successfully parsed {len(new_posts)} new posts.")
    except Exception as e:
        print(f"Startup: Initial ingestion failed: {e}")
    finally:
        db.close()
        
    # 3. Start async background scraper thread loop
    print(f"Startup: Spawning background scheduler running every {settings.SCRAPE_INTERVAL_MINUTES} mins...")
    bg_task = asyncio.create_task(background_scheduler())
    
    yield
    
    # Cancel background task on shutdown
    bg_task.cancel()

async def background_scheduler():
    """
    Helper background loop that executes scraping and runs the NLP pipeline.
    This guarantees real-time updates and clustering even without Celery running.
    """
    # Wait 30 seconds before first periodic run (since we did one on startup)
    await asyncio.sleep(30)
    
    while True:
        try:
            print("Scheduler Loop: Fetching new posts...")
            db = SessionLocal()
            raw_posts = ScraperService.fetch_all()
            new_posts = process_and_save_posts(db, raw_posts)
            
            if new_posts:
                # Send WebSocket broadcast
                await manager.broadcast({
                    "type": "NEW_POSTS",
                    "count": len(new_posts),
                    "timestamp": str(new_posts[0].scraped_at)
                })
                print(f"Scheduler Loop: Broadcasted {len(new_posts)} new posts.")
            db.close()
        except asyncio.CancelledError:
            print("Scheduler Loop: Task cancelled, shutting down.")
            break
        except Exception as e:
            print(f"Scheduler Loop Error: {e}")
            
        await asyncio.sleep(settings.SCRAPE_INTERVAL_MINUTES * 60)

app = FastAPI(
    title="Passport Social Scraper Backend",
    description="FastAPI service for scraping, translating, categorizing and clustering social media posts.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration — uses CORS_ORIGINS env var (default: "*")
cors_origins = settings.cors_origins_list if settings.cors_origins_list else ["*"]
# In production set CORS_ORIGINS=https://passport-scraper-dashboard.vercel.app
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# include routers
app.include_router(endpoints.router, prefix="/api")
@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        manager.disconnect(websocket)



@app.get("/health")
def health_check():
    return {"status": "ok"}
