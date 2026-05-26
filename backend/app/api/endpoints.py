from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc
from datetime import datetime, timedelta
from typing import List, Optional, Set
import re
import collections

from app.database import get_db
from app.models.models import Post, Cluster
from app.schemas.schemas import (
    PostResponse, ClusterResponse, TranslationRequest, TranslationResponse,
    DashboardStats, CategoryStat, PlatformStat, SentimentStat, RegionStat
)
from app.services.translation_service import TranslationService

router = APIRouter(prefix="/api")


# ─────────────────────────────────────────────────────────────────────────────
# WebSocket connection manager
# ─────────────────────────────────────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        dead = set()
        for conn in list(self.active_connections):
            try:
                await conn.send_json(message)
            except Exception:
                dead.add(conn)
        self.active_connections -= dead


manager = ConnectionManager()


# ─────────────────────────────────────────────────────────────────────────────
# WORD CLOUD STOP-WORDS
# ─────────────────────────────────────────────────────────────────────────────
# Very comprehensive list: all generic English words, pronouns, prepositions,
# conjunctions, and common filler words.  Also Hindi transliterations and
# Devanagari stop words.  Passport-specific domain words that appear in EVERY
# post (passport, india) are also excluded.
#
# IMPORTANT: Words that ARE useful keywords (tatkal, visa, renewal, appointment,
# scam, embassy, etc.) are intentionally kept OUT of this list.
# ─────────────────────────────────────────────────────────────────────────────
WORD_CLOUD_STOPWORDS = {
    # Articles / conjunctions / prepositions
    "the", "a", "an", "and", "or", "but", "to", "for", "in", "at", "on",
    "with", "by", "of", "from", "into", "through", "about", "against",
    "between", "without", "within", "during", "before", "after", "above",
    "below", "up", "down", "out", "off", "over", "under", "again",
    "further", "then", "once", "since", "until", "while",

    # Pronouns
    "i", "we", "you", "he", "she", "they", "it", "me", "us", "him",
    "her", "them", "my", "our", "your", "his", "their", "its",
    "this", "that", "these", "those", "who", "what", "which", "whom",
    "whose", "anyone", "someone", "everyone", "nobody", "everybody",

    # Common verbs (all forms)
    "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "done", "doing",
    "get", "got", "getting", "gotten", "make", "made", "making",
    "take", "took", "taken", "taking", "put", "go", "went", "gone",
    "going", "come", "came", "coming", "let", "say", "said", "saying",
    "know", "knew", "known", "think", "thought", "see", "saw", "seen",
    "want", "wanted", "need", "needed", "use", "used", "using",
    "would", "could", "should", "shall", "will", "may", "might",
    "must", "can", "try", "tried", "seem", "seems", "seemed",

    # Adjectives / Adverbs (generic)
    "not", "no", "nor", "only", "also", "even", "just", "really",
    "very", "so", "too", "yet", "still", "already", "now", "then",
    "here", "there", "when", "where", "why", "how", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such",
    "same", "own", "than", "much", "many", "little", "first", "last",
    "next", "second", "else", "quite", "rather", "well", "often",
    "never", "always", "usually", "sometimes", "today", "tomorrow",
    "yesterday", "currently", "recently", "soon", "back", "long",
    "old", "new", "big", "small", "right", "left", "good", "bad",
    "great", "able", "like", "different", "possible", "certain",

    # Common nouns (too generic for word cloud)
    "one", "two", "three", "way", "thing", "things", "time", "times",
    "day", "days", "week", "weeks", "month", "months", "year", "years",
    "place", "people", "person", "man", "woman", "question", "answer",
    "part", "case", "point", "number", "fact", "issue", "issues",
    "lot", "bit", "bit", "info", "information", "details", "note",
    "post", "comment", "thread", "update", "reddit", "anyone",

    # Passport domain words in EVERY post (excluded to avoid dominating cloud)
    "passport", "india", "indian",

    # Hindi/Hinglish stop words (Latin transliterations)
    "hai", "hain", "ke", "ka", "ki", "ko", "se", "mein", "par", "bhi",
    "hi", "ho", "hu", "hun", "tha", "thi", "toh", "aur", "ya",
    "liye", "kuch", "apne", "apni", "apna", "sath", "saath", "pe",
    "kr", "kar", "karna", "krna", "raha", "rahe", "rahi", "hoga",
    "hogi", "hoge", "rha", "rhe", "rhi", "huwa", "hua", "hue",
    "ab", "kab", "tab", "jab", "sabhi", "koi", "aise", "waisa",
    "kaisa", "jo", "kaise", "kyun", "kya", "woh", "yeh", "iske",
    "unke", "inke", "wahan", "yahan",

    # Devanagari stop words
    "है", "हैं", "के", "का", "की", "को", "से", "में", "पर", "भी",
    "ही", "तो", "और", "या", "लिए", "कुछ", "अपने", "अपनी", "अपना",
    "साथ", "कर", "करना", "रहा", "रहे", "रही", "होगा", "होगी",
    "होगे", "अब", "कब", "तब", "जब", "सभी", "कोई", "जो", "ने",

    # Common short internet words
    "lol", "haha", "ok", "okay", "yeah", "yes", "nah", "nope",
    "wow", "omg", "lmao", "imo", "iirc", "afaik", "tldr", "edit",
    "etc", "btw", "fyi", "asap", "diy", "iirc", "idk",

    # Additional common words that clutter word cloud
    "birth", "name", "card", "because", "which", "where", "their",
    "certificate", "know", "trip", "travel", "been", "with", "will",
    "they", "have", "what", "been", "there", "when", "just", "but",
    "were", "that", "from", "has", "have", "this", "very", "also",
}


# ─────────────────────────────────────────────────────────────────────────────
# PASSPORT-RELEVANT KEYWORD WHITELIST FOR WORD CLOUD
# ─────────────────────────────────────────────────────────────────────────────
# Only words in this set (or longer than 6 chars and not in stop words) appear
# in the word cloud.  This forces the cloud to show domain-relevant keywords.
PASSPORT_KEYWORDS_WHITELIST = {
    # Core passport terms
    "tatkal", "renewal", "renew", "renewed", "appointment", "appointments",
    "slot", "slots", "booking", "psk", "seva", "kendra",
    "visa", "visas", "schengen", "embassy", "consulate",
    "application", "applied", "apply", "verification", "police",
    "documents", "document", "pending", "status", "tracking",
    "renewal", "expired", "expiry", "reissue",
    "scam", "fraud", "fake", "warning", "agent", "beware",
    "lost", "stolen", "damaged", "missing", "emergency",
    "flight", "airport", "boarding", "immigration", "validity",
    "henley", "ranking", "ranked", "index", "powerful",
    "ministry", "announcement", "official", "government", "policy",
    "nri", "oci", "permit", "stamping", "transit",
    # Country/travel terms
    "canada", "london", "dubai", "singapore", "australia",
    "schengen", "europe", "thailand", "bangkok",
    # Process terms
    "dispatch", "delivered", "received", "processing", "approved",
    "rejected", "interview", "biometric", "form", "fee", "fees",
    "online", "digital", "portal", "website",
}


# ─────────────────────────────────────────────────────────────────────────────
# POSTS ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/posts")
def get_posts(
    platform: Optional[str] = None,
    category: Optional[str] = None,
    language: Optional[str] = None,
    sentiment: Optional[str] = None,
    region: Optional[str] = None,
    author: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    clustered: bool = True,
    db: Session = Depends(get_db),
):
    """
    Retrieves and filters passport posts from the last 24 hours.
    
    Filtering logic:
      - platform: exact match (case-insensitive)
      - category: exact match
      - language: exact match (case-insensitive)
      - sentiment: exact match (case-insensitive)
      - region: matches country or city in geolocation JSON
      - author: matches creator / handler handle
      - search: ILIKE on content AND category (to enable word-cloud keyword searches)
      - clustered: if True, groups duplicate posts under their primary card
    """
    time_limit = datetime.utcnow() - timedelta(hours=24)
    query = db.query(Post).filter(Post.created_at >= time_limit)

    # ── Platform filter ───────────────────────────────────────────────────────
    if platform:
        query = query.filter(func.lower(Post.platform) == platform.lower())

    # ── Category filter ───────────────────────────────────────────────────────
    if category:
        query = query.filter(Post.category == category)

    # ── Language filter ───────────────────────────────────────────────────────
    if language:
        query = query.filter(func.lower(Post.original_language) == language.lower())

    # ── Sentiment filter ──────────────────────────────────────────────────────
    if sentiment:
        query = query.filter(func.lower(Post.sentiment) == sentiment.lower())

    # ── Creator / Handler filter ──────────────────────────────────────────────
    if author:
        query = query.filter(func.lower(Post.author).like(f"%{author.lower()}%"))

    # ── Region filter ─────────────────────────────────────────────────────────
    if region:
        query = query.filter(
            or_(
                func.lower(Post.geolocation["country"].as_string()) == region.lower(),
                func.lower(Post.geolocation["city"].as_string()) == region.lower(),
            )
        )

    # ── Search / keyword filter ───────────────────────────────────────────────
    # Searches: post content, summary, category name, AND author.
    # This means clicking a word-cloud keyword that matches a category name
    # (e.g., "visa") will return posts whose content contains "visa" as well
    # as posts categorized as "Visa".
    if search:
        search_term = search.strip()
        search_pattern = f"%{search_term.lower()}%"

        # Translation cache subquery
        from app.models.models import TranslationCache
        trans_ids = db.query(TranslationCache.post_id).filter(
            or_(
                func.lower(TranslationCache.translated_content).like(search_pattern),
                func.lower(TranslationCache.translated_summary).like(search_pattern),
            )
        ).subquery()

        query = query.filter(
            or_(
                func.lower(Post.content).like(search_pattern),
                func.lower(Post.summary).like(search_pattern),
                func.lower(Post.category).like(search_pattern),
                Post.post_id.in_(trans_ids),
            )
        )

    # ── Sorting ───────────────────────────────────────────────────────────────
    if sort_by == "engagement":
        query = query.order_by(
            desc(Post.likes + Post.reposts + Post.comments)
        )
    else:
        query = query.order_by(desc(Post.created_at))

    posts = query.all()

    # ── Flat mode ─────────────────────────────────────────────────────────────
    if not clustered:
        return [PostResponse.from_orm(p).dict() for p in posts]

    # ── Clustered mode: group by cluster_id ───────────────────────────────────
    cluster_groups: dict = {}
    noise_posts: list = []

    for post in posts:
        if post.cluster_id is None:
            noise_posts.append({"post": post, "duplicates": [], "cluster_size": 1})
            continue
        c_id = post.cluster_id
        if c_id not in cluster_groups:
            cluster_groups[c_id] = {"post": post, "duplicates": [], "cluster_size": 1}
        else:
            cluster_groups[c_id]["duplicates"].append(post)
            cluster_groups[c_id]["cluster_size"] += 1

    # Combine groups + noise
    result = []
    for g in cluster_groups.values():
        result.append({
            **PostResponse.from_orm(g["post"]).dict(),
            "duplicates": [PostResponse.from_orm(p).dict() for p in g["duplicates"]],
            "cluster_size": g["cluster_size"],
        })
    for n in noise_posts:
        result.append({
            **PostResponse.from_orm(n["post"]).dict(),
            "duplicates": [],
            "cluster_size": 1,
        })

    # Re-sort after grouping
    if sort_by == "engagement":
        result.sort(
            key=lambda x: x["likes"] + x["reposts"] + x["comments"],
            reverse=True,
        )
    else:
        result.sort(key=lambda x: x["created_at"], reverse=True)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# STATS ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    """
    Aggregates platform, category, sentiment, region metrics, and generates
    a domain-relevant word cloud (no generic stop words).
    """
    time_limit = datetime.utcnow() - timedelta(hours=24)
    posts = db.query(Post).filter(Post.created_at >= time_limit).all()

    total = len(posts)

    # 1. Platform counts
    platforms = collections.Counter(p.platform for p in posts)
    platform_stats = [PlatformStat(platform=k, count=v) for k, v in platforms.most_common()]

    # 2. Category counts
    categories = collections.Counter(p.category for p in posts if p.category)
    category_stats = [CategoryStat(category=k, count=v) for k, v in categories.most_common()]

    # 3. Sentiment counts
    sentiments = collections.Counter(p.sentiment for p in posts if p.sentiment)
    sentiment_stats = [SentimentStat(sentiment=k, count=v) for k, v in sentiments.most_common()]

    # 4. Regional counts
    regions = collections.Counter(
        p.geolocation["country"]
        for p in posts
        if p.geolocation and isinstance(p.geolocation, dict) and "country" in p.geolocation
    )
    region_stats = [RegionStat(region=k, count=v) for k, v in regions.most_common()]

    # 5. Word cloud — domain-relevant keywords only
    word_counts: collections.Counter = collections.Counter()
    for post in posts:
        # Extract 3-20 character alphanumeric words (English + Devanagari)
        words = re.findall(r"\b[a-zA-Z\u0900-\u097F]{3,20}\b", post.content.lower())
        for word in words:
            # Skip if stop word
            if word in WORD_CLOUD_STOPWORDS:
                continue
            # Accept if in whitelist OR if it's ≥7 chars (likely domain-specific)
            if word in PASSPORT_KEYWORDS_WHITELIST or len(word) >= 7:
                word_counts[word] += 1

    # Take top 20, excluding "passport" and "india" since those dominate but add no signal
    filtered_cloud = {w: c for w, c in word_counts.most_common(30) if w not in {"passport", "india", "indian"}}
    top_cloud = dict(list(filtered_cloud.items())[:20])

    return DashboardStats(
        total_posts=total,
        categories=category_stats,
        platforms=platform_stats,
        sentiments=sentiment_stats,
        regions=region_stats,
        word_cloud=top_cloud,
        last_updated=datetime.utcnow(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# TRANSLATION ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/translate", response_model=TranslationResponse)
def translate_post(payload: TranslationRequest, db: Session = Depends(get_db)):
    """Translates a specific post's contents into the requested target language."""
    post = db.query(Post).filter(Post.post_id == payload.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    translation = TranslationService.translate_post(
        db=db,
        post_id=post.post_id,
        content=post.content,
        summary=post.summary,
        target_lang=payload.target_language,
    )

    return TranslationResponse(
        post_id=post.post_id,
        language=payload.target_language,
        translated_content=translation["content"],
        translated_summary=translation["summary"],
    )
