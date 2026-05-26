from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any

class PostBase(BaseModel):
    post_id: str
    platform: str
    author: str
    author_avatar: Optional[str] = None
    url: Optional[str] = None
    content: str
    created_at: datetime
    likes: int = 0
    reposts: int = 0
    comments: int = 0
    views: int = 0
    category: Optional[str] = None
    sentiment: Optional[str] = None
    summary: Optional[str] = None
    original_language: str = "en"
    geolocation: Optional[Any] = None
    cluster_id: Optional[int] = None

class PostResponse(PostBase):
    id: int
    scraped_at: datetime

    class Config:
        from_attributes = True

class ClusterResponse(BaseModel):
    id: int
    summary: str
    created_at: datetime
    posts: List[PostResponse] = []

    class Config:
        from_attributes = True

class TranslationRequest(BaseModel):
    post_id: str
    target_language: str

class TranslationResponse(BaseModel):
    post_id: str
    language: str
    translated_content: str
    translated_summary: Optional[str] = None

class CategoryStat(BaseModel):
    category: str
    count: int

class PlatformStat(BaseModel):
    platform: str
    count: int

class SentimentStat(BaseModel):
    sentiment: str
    count: int

class RegionStat(BaseModel):
    region: str
    count: int

class DashboardStats(BaseModel):
    total_posts: int
    categories: List[CategoryStat]
    platforms: List[PlatformStat]
    sentiments: List[SentimentStat]
    regions: List[RegionStat]
    word_cloud: Dict[str, int]
    last_updated: datetime
