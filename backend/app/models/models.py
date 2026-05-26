import json
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator
from datetime import datetime
from app.database import Base, is_sqlite

# Dynamic PGVector helper
class SQLiteVector(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return None

try:
    if is_sqlite:
        VectorType = SQLiteVector
    else:
        from pgvector.sqlalchemy import Vector
        VectorType = Vector(384) # 384 dimensions for all-MiniLM-L6-v2
except ImportError:
    VectorType = SQLiteVector

class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, index=True)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to posts
    posts = relationship("Post", back_populates="cluster")

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(String, unique=True, index=True, nullable=False)  # original post unique ID
    platform = Column(String, nullable=False)                          # twitter, reddit, youtube, facebook, etc.
    author = Column(String, nullable=False)                            # username / handle
    author_avatar = Column(String, nullable=True)                      # profile picture URL
    url = Column(String, nullable=True)                                # Link to original post
    content = Column(Text, nullable=False)                             # Original content
    created_at = Column(DateTime, nullable=False)                      # When post was published
    scraped_at = Column(DateTime, default=datetime.utcnow)             # When post was scraped
    
    # Metrics
    likes = Column(Integer, default=0)
    reposts = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    views = Column(Integer, default=0)
    
    # NLP extraction
    category = Column(String, index=True, nullable=True)               # Classified category
    sentiment = Column(String, index=True, nullable=True)              # positive, neutral, negative
    summary = Column(Text, nullable=True)                              # ~30 words summary
    original_language = Column(String, default="en")                   # Detected language code
    geolocation = Column(JSON, nullable=True)                          # Found geolocations (JSON array/dict)
    
    # Vector and Clustering
    embedding = Column(VectorType, nullable=True)                      # 384-dim semantic embedding vector
    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=True)
    
    cluster = relationship("Cluster", back_populates="posts")

class TranslationCache(Base):
    __tablename__ = "translation_cache"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(String, index=True, nullable=False)
    language = Column(String, index=True, nullable=False)              # target language code (e.g. 'es', 'hi')
    translated_content = Column(Text, nullable=False)
    translated_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
