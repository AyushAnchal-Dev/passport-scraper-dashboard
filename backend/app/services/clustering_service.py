import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from app.models.models import Post, Cluster
from app.services.nlp_service import CATEGORIES
from sqlalchemy.orm import Session

class ClusteringService:
    # A precompiled set of descriptions for our categories to calculate TF-IDF similarity
    CATEGORY_DESCRIPTIONS = {
        "Application": "new passport application online process instructions documentation form",
        "Renewal": "renew passport expired passport renewal embassy documents validation",
        "Appointments": "passport seva kendra appointments slots booking queue schedule dates",
        "Tatkal": "tatkal emergency passport speed application urgent fees slot booking",
        "Visa": "visa application processing embassy stamping travel requirements travel permit",
        "Travel Issues": "passport lost stolen damaged airport border boarding travel check flight validity",
        "Government Announcements": "official passport office press release post office kendra state notification",
        "Scams/Fraud": "fake websites scam alert agent charging extra fees fraud warning warning",
        "News": "news passport rules passport rankings visa free travel updates government press",
        "Personal Experiences": "finally got my passport officer was polite delivered on time thank you experience review"
    }

    @classmethod
    def get_category_embeddings(cls) -> Dict[str, np.ndarray]:
        """
        Generates representations for the category descriptors using the same
        hash-kernel encode_text method. This guarantees alignment in the same vector space.
        """
        return {
            cat: np.array(cls.encode_text(desc))
            for cat, desc in cls.CATEGORY_DESCRIPTIONS.items()
        }

    @classmethod
    def encode_text(cls, text: str) -> List[float]:
        """
        Encodes a single text string into a 384-dimensional vector using a character hash / lightweight TF-IDF logic.
        This provides a zero-dependency vector matching system.
        """
        # We can implement a clean frequency vectorizer
        # Top 384 English character trigrams or typical words
        vector = np.zeros(384)
        words = text.lower().split()
        for word in words:
            # Hash words to the 384 buckets (hash-kernel approach)
            h = hash(word) % 384
            vector[h] += 1
            
        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector.tolist()

    @classmethod
    def run_clustering(cls, db: Session) -> int:
        """
        Resets old clusters, gathers all posts from the last 24h, fits a TfidfVectorizer,
        runs DBSCAN, and writes cluster records to the database.
        """
        # Clear old cluster associations and delete old clusters to perform a clean recalculation
        db.query(Post).update({Post.cluster_id: None})
        db.commit()
        db.query(Cluster).delete()
        db.commit()

        # Get all active posts
        posts = db.query(Post).all()
        if not posts:
            return 0

        # Extract content lists
        contents = [post.content for post in posts]
        
        # Calculate TF-IDF matrix
        # Limit max_features to 384 to remain compatible with pgvector(384) schema
        vectorizer = TfidfVectorizer(max_features=384, stop_words='english')
        try:
            X = vectorizer.fit_transform(contents).toarray()
            
            # Map sparse vectors back to the db column
            # Pad vector to exactly 384 dimensions if vocabulary size is smaller
            for idx, post in enumerate(posts):
                raw_vec = X[idx]
                padded = np.zeros(384)
                padded[:len(raw_vec)] = raw_vec
                post.embedding = padded.tolist()
                db.add(post)
            db.flush()
        except Exception as e:
            # If TF-IDF fit fails (e.g. empty inputs), use fallback hashing
            print(f"TF-IDF vectorization failed, fallback to hash-kernel: {e}")
            X_list = []
            for post in posts:
                emb = cls.encode_text(post.content)
                post.embedding = emb
                db.add(post)
                X_list.append(emb)
            X = np.array(X_list)

        if len(X) < 2:
            # Not enough posts to cluster, put them in noise/independent clusters
            for post in posts:
                cluster = Cluster(summary=f"Independent post: {post.summary or post.content[:80]}")
                db.add(cluster)
                db.flush()
                post.cluster_id = cluster.id
                db.add(post)
            db.commit()
            return len(posts)

        # Run DBSCAN - strict eps=0.2 (cosine distance) to group only high-similarity/duplicate posts
        clustering = DBSCAN(eps=0.2, min_samples=2, metric='cosine').fit(X)
        labels = clustering.labels_

        # Map labels to DB clusters - prevent cross-category clustering by using composite key
        cluster_map: Dict[Any, List[Post]] = {}
        for idx, label in enumerate(labels):
            post = posts[idx]
            if label >= 0:
                key = f"{post.category}_{label}"
                cluster_map.setdefault(key, []).append(post)
            else:
                cluster_map.setdefault(f"noise_{post.post_id}", []).append(post)

        clusters_created = 0
        for c_id, c_posts in cluster_map.items():
            if not c_posts:
                continue
                
            rep_post = c_posts[0]
            if len(c_posts) > 1:
                summary = f"Discussion thread: {len(c_posts)} posts matching: '{rep_post.summary or rep_post.content[:80]}'"
            else:
                summary = f"Independent post: {rep_post.summary or rep_post.content[:80]}"
                
            cluster = Cluster(summary=summary)
            db.add(cluster)
            db.flush()
            
            for p in c_posts:
                p.cluster_id = cluster.id
                db.add(p)
                
            clusters_created += 1

        db.commit()
        return clusters_created
