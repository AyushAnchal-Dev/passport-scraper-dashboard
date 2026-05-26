"""
nlp_service.py — Deterministic, rule-first NLP pipeline for passport-related posts.

Classification strategy (in priority order):
  1. HIGH-SPECIFICITY KEYWORD MATCH  — exact word-boundary matches for rare/specific terms
  2. SCORED KEYWORD MATCH            — weighted multi-keyword scoring per category
  3. SEMANTIC EMBEDDING FALLBACK     — cosine similarity against category embeddings

This layered approach guarantees that specific triggers (tatkal, scam, ministry, henley…)
always win over generic overlap, while the semantic fallback handles edge-cases.
"""

import re
import math
import collections
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# CATEGORY DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────
CATEGORIES = [
    "Application",
    "Renewal",
    "Appointments",
    "Tatkal",
    "Visa",
    "Travel Issues",
    "Government Announcements",
    "Scams/Fraud",
    "News",
    "Personal Experiences",
]

# ── TIER-1: EXCLUSIVE HIGH-SPECIFICITY TRIGGERS ──────────────────────────────
# If ANY of these terms appear, the category is assigned immediately (no scoring).
# Ordered from most-specific to least-specific within each category.
EXCLUSIVE_TRIGGERS: Dict[str, List[str]] = {
    "Tatkal": [
        "tatkal", "tatkaal", "तत्काल",
        "emergency passport", "emergency certificate",
        "expedited passport", "urgent passport",
    ],
    "Scams/Fraud": [
        "scam alert", "scam busters", "fake website", "fraud alert",
        "passport fraud", "passport scam", "fake agent", "fake slot",
        "cybercrime", "illegal agent", "paid agent", "guaranteed slot",
        "beware of", "money stolen", "cheated by agent",
    ],
    "Government Announcements": [
        "ministry of external affairs", "mea india", "government launches",
        "officially launches", "announced by ministry", "new passport office",
        "government announces", "new passport rule", "official notification",
        "press release", "policy change", "government policy", "mea gov",
        "passport seva kendra opens", "new psk",
        "digital india passport", "₹ crore",
    ],
    "News": [
        "henley passport index", "passport index", "passport ranking",
        "passport power", "visa-free rank", "visa free rank",
        "most powerful passport", "breaking news", "passport news 2025",
        "global passport index", "immigration report",
    ],
}

# ── TIER-2: WEIGHTED KEYWORD SCORING ─────────────────────────────────────────
# Each keyword has a weight.  The category with the highest total score wins.
# Categories with very specific vocabulary get higher weights per keyword.
KEYWORD_WEIGHTS: Dict[str, Dict[str, float]] = {
    "Tatkal": {
        "tatkal": 50, "tatkaal": 50, "urgent": 5, "emergency": 8,
        "expedited": 10, "fast track": 8, "same day": 6,
        "तत्काल": 50, "faster appointment": 6,
    },
    "Scams/Fraud": {
        "scam": 20, "fraud": 20, "fake": 12, "scammer": 20,
        "beware": 10, "warning": 6, "report this": 8,
        "extortion": 15, "otp": 8, "phishing": 15,
        "cybercrime": 12, "fraud website": 20, "illegal": 8,
        "agent charging": 15, "charging extra": 12,
    },
    "Government Announcements": {
        "ministry": 15, "mea": 15, "official": 8, "government": 6,
        "announced": 6, "launched": 6, "policy": 6, "press": 5,
        "notification": 8, "digitally": 4, "digital india": 8,
        "inauguration": 8, "crore": 6, "budget": 5,
    },
    "News": {
        "news": 6, "ranking": 8, "ranked": 8, "index": 6,
        "report": 5, "henley": 20, "global": 4, "worldwide": 4,
        "study shows": 8, "according to": 5, "survey": 6,
        "statistics": 6, "data shows": 8,
    },
    "Appointments": {
        "appointment": 15, "slot": 12, "slots": 12, "book": 8,
        "booking": 12, "psk": 10, "seva kendra": 12,
        "schedule": 8, "reschedule": 10, "available date": 10,
        "no slots": 15, "all slots full": 15,
    },
    "Renewal": {
        "renew": 15, "renewal": 15, "renewing": 15, "re-issue": 12,
        "reissue": 12, "expired": 10, "expiry": 10, "expiring": 10,
        "expire soon": 12, "expires next": 10, "10 year passport": 8,
        "रिन्यू": 15,
    },
    "Application": {
        "apply": 8, "applied": 8, "application": 8, "fresh passport": 12,
        "first passport": 12, "new passport": 8, "police verification": 12,
        "police clearance": 10, "document": 5, "documents required": 8,
        "submitted": 6, "verification pending": 10, "status pending": 8,
        "application rejected": 10, "address change": 6,
    },
    "Visa": {
        "visa": 10, "schengen": 15, "stamping": 10, "embassy": 8,
        "consulate": 8, "permit": 6, "transit": 6, "work permit": 10,
        "student visa": 10, "tourist visa": 10, "visa on arrival": 12,
        "visa-free": 8, "visa denied": 12, "visa approved": 10,
        "عeob": 5,  # placeholder for arabic/multi-language
    },
    "Travel Issues": {
        "lost passport": 20, "stolen passport": 20, "passport stolen": 20,
        "passport lost": 20, "damaged passport": 15, "missing passport": 15,
        "airport": 6, "boarding pass": 5, "denied boarding": 12,
        "travel ban": 10, "immigration rejected": 10, "travel issue": 12,
        "6 month validity": 10, "passport validity": 8, "transit issue": 8,
        "stuck at airport": 15, "passport missing": 15,
    },
    "Personal Experiences": {
        "my experience": 10, "my passport arrived": 12, "happy to share": 8,
        "positive experience": 10, "excellent service": 10, "great service": 10,
        "polite staff": 10, "smooth process": 10, "helpful officer": 10,
        "thank you mea": 12, "got my passport": 8, "successfully got": 8,
        "sharing my journey": 8, "passport delivered": 10,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# GEOLOCATION DATABASE
# ─────────────────────────────────────────────────────────────────────────────
GEO_DATABASE = {
    "india": {"city": "Delhi", "country": "India"},
    "delhi": {"city": "Delhi", "country": "India"},
    "mumbai": {"city": "Mumbai", "country": "India"},
    "bombay": {"city": "Mumbai", "country": "India"},
    "bangalore": {"city": "Bangalore", "country": "India"},
    "bengaluru": {"city": "Bangalore", "country": "India"},
    "pune": {"city": "Pune", "country": "India"},
    "lucknow": {"city": "Lucknow", "country": "India"},
    "jaipur": {"city": "Jaipur", "country": "India"},
    "hyderabad": {"city": "Hyderabad", "country": "India"},
    "chennai": {"city": "Chennai", "country": "India"},
    "kolkata": {"city": "Kolkata", "country": "India"},
    "ahmedabad": {"city": "Ahmedabad", "country": "India"},
    "patna": {"city": "Patna", "country": "India"},
    "united kingdom": {"city": "London", "country": "United Kingdom"},
    "uk": {"city": "London", "country": "United Kingdom"},
    "london": {"city": "London", "country": "United Kingdom"},
    "united states": {"city": "Washington", "country": "United States"},
    "usa": {"city": "Washington", "country": "United States"},
    "new york": {"city": "New York", "country": "United States"},
    "los angeles": {"city": "Los Angeles", "country": "United States"},
    "chicago": {"city": "Chicago", "country": "United States"},
    "canada": {"city": "Ottawa", "country": "Canada"},
    "toronto": {"city": "Toronto", "country": "Canada"},
    "vancouver": {"city": "Vancouver", "country": "Canada"},
    "france": {"city": "Paris", "country": "France"},
    "paris": {"city": "Paris", "country": "France"},
    "germany": {"city": "Berlin", "country": "Germany"},
    "berlin": {"city": "Berlin", "country": "Germany"},
    "qatar": {"city": "Doha", "country": "Qatar"},
    "doha": {"city": "Doha", "country": "Qatar"},
    "thailand": {"city": "Bangkok", "country": "Thailand"},
    "bangkok": {"city": "Bangkok", "country": "Thailand"},
    "spain": {"city": "Madrid", "country": "Spain"},
    "madrid": {"city": "Madrid", "country": "Spain"},
    "dubai": {"city": "Dubai", "country": "UAE"},
    "uae": {"city": "Dubai", "country": "UAE"},
    "australia": {"city": "Sydney", "country": "Australia"},
    "sydney": {"city": "Sydney", "country": "Australia"},
    "singapore": {"city": "Singapore", "country": "Singapore"},
    "norway": {"city": "Oslo", "country": "Norway"},
    "rome": {"city": "Rome", "country": "Italy"},
    "italy": {"city": "Rome", "country": "Italy"},
}


class NlpService:

    @staticmethod
    def calculate_entropy(text: str) -> float:
        """Shannon Entropy of a string — used for gibberish detection."""
        if not text:
            return 0.0
        counts = collections.Counter(text)
        total = len(text)
        return -sum((c / total) * math.log2(c / total) for c in counts.values())

    @classmethod
    def is_gibberish(cls, text: str) -> bool:
        """
        Filters out bot spam, keyboard smashes, and meaningless content.
        Returns True only when the text is clearly non-human noise.
        """
        clean = text.strip()
        if len(clean) < 10:
            return True

        # Excessive special-character density
        special = set("!@#$%^&*()-_=+[]{};:'\",.<>/?\\|`~")
        if sum(1 for c in clean if c in special) / len(clean) > 0.40:
            return True

        # Repeated character runs (aaaaa, 11111…)
        if re.search(r"([a-zA-Z0-9])\1{4,}", clean):
            return True

        # Very low entropy on longer texts
        if len(clean) > 20 and cls.calculate_entropy(clean) < 3.0:
            return True

        # Physical keyboard-row smash sequences (QWERTY layout)
        smash_sequences = [
            "asdfgh", "sdfghj", "dfghjk", "fghjkl",
            "qwerty", "wertyu", "ertyui", "rtyuio", "tyuiop",
            "zxcvbn", "xcvbnm",
            "lkjhgf", "kjhgfd", "jhgfds", "hgfdsa",
            "poiuyt", "oiuytr", "iuytre", "uytrew", "ytrewq",
            "mnbvcx", "nbvcxz",
        ]
        lower = clean.lower()
        if any(seq in lower for seq in smash_sequences):
            return True

        return False

    @staticmethod
    def analyze_sentiment(text: str) -> str:
        """
        Accurate rule-based sentiment optimised for passport/travel domain.
        Uses weighted word lists and contextual negation handling.
        """
        text_lower = text.lower()

        # Negation detection window (preceding 3 words)
        _negations = {"not", "no", "never", "don't", "didn't", "cannot", "can't"}

        positive_words = {
            "smooth", "easy", "great", "excellent", "fast", "polite",
            "quick", "helpful", "good", "approved", "delivered", "happy",
            "thanks", "perfect", "amazing", "wonderful", "fantastic",
            "impressed", "satisfied", "success", "successful", "efficient",
            "streamlined", "simple", "hassle-free", "convenient",
        }
        negative_words = {
            "frustrat", "scam", "fake", "stuck", "delay", "slow", "error",
            "fail", "down", "ruined", "angry", "terrible", "worst",
            "stolen", "lost", "rejected", "denied", "problem", "issue",
            "horrible", "disappoint", "useless", "waste", "nightmare",
            "corrupt", "brib", "extort",
        }

        words = text_lower.split()
        pos, neg = 0, 0

        for i, word in enumerate(words):
            # Check if preceded by negation
            context = set(words[max(0, i - 3):i])
            negated = bool(context & _negations)

            # Positive stem match
            if any(word.startswith(pw) or pw in word for pw in positive_words):
                if negated:
                    neg += 1
                else:
                    pos += 1

            # Negative stem match
            if any(word.startswith(nw) or nw in word for nw in negative_words):
                if negated:
                    pos += 1
                else:
                    neg += 2           # negative carries extra weight

        # Emoji / punctuation boosts
        if any(x in text for x in ["😡", "😠", "😤", "😰", "😱", "⚠️", "🚨"]):
            neg += 3
        if any(x in text for x in ["❤️", "👍", "😊", "🙌", "🎉", "✅"]):
            pos += 2
        if "!!!" in text:
            neg += 1
        if "scam" in text_lower or "fraud" in text_lower:
            neg += 3

        if pos > neg:
            return "positive"
        if neg > pos:
            return "negative"
        return "neutral"

    @staticmethod
    def extract_geolocation(text: str) -> Optional[Dict[str, str]]:
        """
        Extracts the first city/country match from the text using a gazetteer.
        Multi-word entries are checked before single-word entries.
        """
        text_lower = text.lower()
        # Sort by length (longer first) so multi-word entries take priority
        sorted_entries = sorted(GEO_DATABASE.items(), key=lambda x: -len(x[0]))
        for key, geo in sorted_entries:
            if re.search(r"\b" + re.escape(key) + r"\b", text_lower):
                return geo
        return None

    @staticmethod
    def generate_summary(text: str) -> str:
        """
        Extractive summary: selects the most information-dense sentences.
        Returns ≤ 35 words.
        """
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        if not sentences:
            return text
        if len(text.split()) <= 30:
            return text

        result, total = [], 0
        for sent in sentences:
            words = sent.split()
            if total + len(words) <= 35:
                result.append(sent)
                total += len(words)
            else:
                remaining = 30 - total
                if remaining > 5:
                    result.append(" ".join(words[:remaining]) + "...")
                break

        return " ".join(result) if result else text[:150] + "..."

    @staticmethod
    def classify_category_semantic(
        content: str,
        embedding: np.ndarray,
        category_embeddings: Dict[str, np.ndarray],
    ) -> str:
        """
        Three-tier category classifier:

        Tier 1 – EXCLUSIVE TRIGGERS
            If a high-specificity phrase is found (e.g. 'tatkal', 'henley passport index'),
            return that category immediately.

        Tier 2 – WEIGHTED KEYWORD SCORING
            Sum weighted scores for all keywords across all categories.
            Winner must have score ≥ 6 to be accepted.

        Tier 3 – SEMANTIC EMBEDDING SIMILARITY
            Fall back to cosine similarity against pre-encoded category descriptions.
        """
        lower = content.lower()

        # ── Tier 1: Exclusive triggers ────────────────────────────────────────
        for category, triggers in EXCLUSIVE_TRIGGERS.items():
            for trigger in triggers:
                if trigger in lower:
                    return category

        # ── Tier 2: Weighted keyword scoring ─────────────────────────────────
        def has_word(phrase: str, text: str) -> bool:
            idx = text.find(phrase)
            while idx != -1:
                before_ok = True
                if idx > 0:
                    char_before = text[idx - 1]
                    if char_before.isalnum() or char_before == '_':
                        before_ok = False
                after_ok = True
                end_idx = idx + len(phrase)
                if end_idx < len(text):
                    char_after = text[end_idx]
                    if char_after.isalnum() or char_after == '_':
                        after_ok = False
                if before_ok and after_ok:
                    return True
                idx = text.find(phrase, idx + 1)
            return False

        scores: Dict[str, float] = {cat: 0.0 for cat in KEYWORD_WEIGHTS}
        for category, kw_dict in KEYWORD_WEIGHTS.items():
            for phrase, weight in kw_dict.items():
                if has_word(phrase, lower):
                    scores[category] += weight

        best_cat, best_score = max(scores.items(), key=lambda x: x[1])
        if best_score >= 6:
            return best_cat

        # ── Tier 3: Semantic embedding fallback ───────────────────────────────
        if category_embeddings:
            best_sim, best_sem_cat = -1.0, "Travel Issues"
            norm_a = np.linalg.norm(embedding)
            if norm_a > 0:
                for cat, cat_emb in category_embeddings.items():
                    norm_b = np.linalg.norm(cat_emb)
                    if norm_b > 0:
                        sim = np.dot(embedding, cat_emb) / (norm_a * norm_b)
                        if sim > best_sim:
                            best_sim = sim
                            best_sem_cat = cat
            return best_sem_cat

        return "Travel Issues"   # safe final fallback
