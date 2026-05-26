import os
from celery import Celery
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database import SessionLocal
from app.models.models import Post
from app.services.scraper_service import ScraperService
from app.services.nlp_service import NlpService
from app.services.clustering_service import ClusteringService
import numpy as np

# Initialize Celery app
celery_app = Celery("scraper_worker", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)

# Configure periodic scheduler
celery_app.conf.beat_schedule = {
    "periodic-scrape-and-nlp-run": {
        "task": "app.workers.celery_worker.scrape_and_process_task",
        "schedule": float(settings.SCRAPE_INTERVAL_MINUTES * 60),
    }
}

def process_and_save_posts(db: Session, raw_posts: list) -> list:
    """
    NLP Pipeline: Filters gibberish, summarizes, classifies, and runs geolocation NER.
    """
    # 0. Delete posts older than 24 hours to keep a strict rolling window
    from datetime import datetime, timedelta
    time_limit = datetime.utcnow() - timedelta(hours=24)
    db.query(Post).filter(Post.created_at < time_limit).delete()
    
    # 0b. If mock mode is False, clean up any old simulated posts from the DB
    if not settings.MOCK_SCRAPER_MODE:
        db.query(Post).filter(Post.post_id.like("sim_%")).delete()
        
    db.commit()

    saved_posts = []
    
    # 1. Fetch category embeddings for zero-shot classification
    cat_embeddings = ClusteringService.get_category_embeddings()
    
    for raw in raw_posts:
        # Check if already processed
        existing = db.query(Post).filter(Post.post_id == raw["post_id"]).first()
        if existing:
            continue

        # Stage 1: Gibberish Filter
        if NlpService.is_gibberish(raw["content"]):
            print(f"Skipping gibberish post: {raw['post_id']}")
            continue

        # Stage 2: Summary
        summary = NlpService.generate_summary(raw["content"])

        # Stage 3: Sentiment
        sentiment = NlpService.analyze_sentiment(raw["content"])

        # Stage 4: Geolocation
        geo = raw.get("location") or NlpService.extract_geolocation(raw["content"])

        # Stage 5: Category (Zero-Shot via Sentence Embeddings)
        # First compute content embedding
        try:
            emb = ClusteringService.encode_text(raw["content"])
            category = NlpService.classify_category_semantic(
                content=raw["content"],
                embedding=np.array(emb),
                category_embeddings=cat_embeddings
            )
        except Exception as e:
            print(f"Failed embedding extraction: {e}")
            emb = None
            category = "General"

        # Create Database Record
        post = Post(
            post_id=raw["post_id"],
            platform=raw["platform"],
            author=raw["author"],
            author_avatar=raw["author_avatar"],
            url=raw["url"],
            content=raw["content"],
            created_at=raw["created_at"],
            likes=raw["likes"],
            reposts=raw["reposts"],
            comments=raw["comments"],
            views=raw["views"],
            category=category,
            sentiment=sentiment,
            summary=summary,
            geolocation=geo,
            embedding=emb,
            original_language="hi" if any(ord(c) > 2300 and ord(c) < 2430 for c in raw["content"]) else "en" # Basic Hindi indicator
        )
        
        db.add(post)
        saved_posts.append(post)

    db.commit()

    # Stage 6: Semantic Clustering (DBSCAN)
    if saved_posts:
        try:
            clusters_count = ClusteringService.run_clustering(db)
            print(f"Clustering complete. Created {clusters_count} threads.")
        except Exception as e:
            print(f"Clustering failed: {e}")

    return saved_posts

@celery_app.task
def scrape_and_process_task():
    """
    Celery task wrapper for periodic runs.
    """
    db = SessionLocal()
    try:
        print("Celery Scraper Worker: Starting periodic fetch...")
        raw_posts = ScraperService.fetch_all()
        processed = process_and_save_posts(db, raw_posts)
        print(f"Celery Scraper Worker: Finished processing {len(processed)} new posts.")
        return len(processed)
    except Exception as e:
        print(f"Celery task execution failed: {e}")
    finally:
        db.close()
