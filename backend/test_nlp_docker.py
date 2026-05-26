import sys
import os
import numpy as np

# Adjust path to import app modules
sys.path.append("/app")

from app.services.nlp_service import NlpService
from app.services.clustering_service import ClusteringService
from app.services.scraper_service import MOCK_POSTS_TEMPLATES

print("Checking Mock Templates NLP processing inside Docker:")
cat_embeddings = ClusteringService.get_category_embeddings()

for idx, template in enumerate(MOCK_POSTS_TEMPLATES):
    content = template["content"]
    is_gib = NlpService.is_gibberish(content)
    entropy = NlpService.calculate_entropy(content)
    
    # Calculate category
    try:
        emb = ClusteringService.encode_text(content)
        category = NlpService.classify_category_semantic(
            content=content,
            embedding=np.array(emb),
            category_embeddings=cat_embeddings
        )
    except Exception as e:
        category = f"Error: {e}"
        
    print(f"\n--- Post {idx} ---")
    print(f"Content: {content[:80]}...")
    print(f"Gibberish: {is_gib} (Entropy: {entropy:.2f})")
    print(f"Category: {category}")
