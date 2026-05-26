import pytest
import sys
import os

# Adjust path to find app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.nlp_service import NlpService

def test_gibberish_filter():
    # True Gibberish / Bot Spam
    assert NlpService.is_gibberish("aaaaa") == True  # Too short, repetitive
    assert NlpService.is_gibberish("asdfghjklqwe") == True  # Keyboard smash pattern
    assert NlpService.is_gibberish("buy cheap passport fast legal click here now!!!") == False  # Normal (though spam, it's not gibberish)
    assert NlpService.is_gibberish("short") == True  # Less than 10 chars
    assert NlpService.is_gibberish("!!!@@@###$$$%%%^^^&&&***") == True  # High non-alnum ratio
    
    # Meaningful text
    valid_text = "I am having extreme delays in getting my passport renewed from Delhi. The status says police verification pending."
    assert NlpService.is_gibberish(valid_text) == False

def test_sentiment_analysis():
    # Negatives
    assert NlpService.analyze_sentiment("This passport renewal is a complete scam, they took my money and delayed the slot.") == "negative"
    assert NlpService.analyze_sentiment("Very frustrated! The appointments portal is down and my flight is in two days. absolute disaster.") == "negative"
    
    # Positives
    assert NlpService.analyze_sentiment("Got my new passport today, the process was super smooth and fast! Highly recommend this service.") == "positive"
    assert NlpService.analyze_sentiment("Thank you to the officer who helped me expedite my visa application, very helpful.") == "positive"
    
    # Neutrals
    assert NlpService.analyze_sentiment("The passport office is located on the second floor near the central metro station.") == "neutral"

def test_geolocation_extraction():
    # Indian Cities
    geo_india = NlpService.extract_geolocation("I am visiting the passport seva kendra in Pune tomorrow morning.")
    assert geo_india is not None
    assert geo_india["city"] == "Pune"
    assert geo_india["country"] == "India"

    # UK
    geo_uk = NlpService.extract_geolocation("Applied for my documents at the high commission in London.")
    assert geo_uk is not None
    assert geo_uk["city"] == "London"
    assert geo_uk["country"] == "United Kingdom"

    # Unknown
    geo_none = NlpService.extract_geolocation("Just sitting in my room reading travel blogs.")
    assert geo_none is None

def test_summary_generation():
    long_text = (
        "Yesterday I went to the main passport office to renew my passport because it is expiring next month. "
        "I was very worried about the long queues but when I arrived the staff was very organized. "
        "They guided me to the correct counter and the police verification was completed on the spot. "
        "I highly recommend coming early in the morning around 8 AM before the rush begins."
    )
    summary = NlpService.generate_summary(long_text)
    words = summary.split()
    
    assert len(words) <= 35
    assert len(words) > 5
    assert summary.endswith("...") or len(summary) < len(long_text)
