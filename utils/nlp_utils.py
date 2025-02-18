# utils/nlp_utils.py
import spacy
from textblob import TextBlob
from collections import Counter

# Load the English NLP model
nlp = spacy.load("en_core_web_sm")


def analyze_text(text):
    """Analyze the given text for sentiment, keywords, categories, and named entities."""

    result = {
        "category": "General",
        "sentiment": None,
        "keywords": [],
        "named_entities": []
    }

    # Sentiment Analysis (Improved)
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity

    if polarity > 0.2:
        result["sentiment"] = "Positive"
    elif polarity < -0.2:
        result["sentiment"] = "Negative"
    else:
        result["sentiment"] = "Neutral"

    # Keyword Extraction (Excludes Stopwords, Numbers, and Short Words)
    doc = nlp(text)
    keywords = [
        token.text.lower() for token in doc
        if token.is_alpha and not token.is_stop and len(token.text) > 2
    ]

    # Frequency-based Keyword Filtering
    most_common_keywords = [word for word, count in Counter(keywords).most_common(10)]
    result["keywords"] = most_common_keywords

    # Named Entity Recognition (NER)
    result["named_entities"] = [(ent.text, ent.label_) for ent in doc.ents]

    # Advanced Text Categorization (Better Keyword Matching)
    category_keywords = {
        "Infrastructure": ["road", "pothole", "bridge", "highway", "street", "traffic"],
        "Healthcare": ["hospital", "clinic", "doctor", "medicine", "nurse"],
        "Public Safety": ["crime", "theft", "police", "fire", "emergency"],
        "Education": ["school", "teacher", "university", "student", "classroom"]
    }

    for category, words in category_keywords.items():
        if any(word in text.lower() for word in words):
            result["category"] = category
            break

    return result
