from sqlalchemy.orm import Session
from deep_translator import GoogleTranslator
from app.models.models import TranslationCache
from app.core.config import settings

# Code normalizer for target languages
LANG_MAPPING = {
    "en": "en",
    "hi": "hi",
    "pa": "pa",
    "es": "es",
    "fr": "fr",
    "de": "de",
    "ar": "ar",
    "zh": "zh-CN",
    "ru": "ru",
    "ja": "ja"
}

class TranslationService:
    @staticmethod
    def translate_post(db: Session, post_id: str, content: str, summary: str, target_lang: str) -> dict:
        """
        Translates post content and summary on-demand.
        Looks up in DB cache first; otherwise calls deep-translator and caches the result.
        """
        # Map target language code if needed
        g_lang = LANG_MAPPING.get(target_lang.lower())
        if not g_lang:
            return {"content": content, "summary": summary} # Unsupported fallback

        # Check DB Cache
        cached = db.query(TranslationCache).filter(
            TranslationCache.post_id == post_id,
            TranslationCache.language == target_lang
        ).first()

        if cached:
            return {
                "content": cached.translated_content,
                "summary": cached.translated_summary
            }

        # Not cached, translate content and summary
        try:
            translator = GoogleTranslator(source='auto', target=g_lang)
            translated_content = translator.translate(content)
            
            translated_summary = None
            if summary:
                translated_summary = translator.translate(summary)
                
            # Store in Cache
            new_cache = TranslationCache(
                post_id=post_id,
                language=target_lang,
                translated_content=translated_content,
                translated_summary=translated_summary
            )
            db.add(new_cache)
            db.commit()
            
            return {
                "content": translated_content,
                "summary": translated_summary
            }
        except Exception as e:
            print(f"Translation error (post={post_id}, lang={target_lang}): {e}")
            # Fallback to original text on failure
            return {
                "content": content,
                "summary": summary
            }
cls = TranslationService
