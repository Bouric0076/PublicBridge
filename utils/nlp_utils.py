# utils/nlp_utils.py
import nltk
from textblob import TextBlob
from collections import Counter
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk import ne_chunk, pos_tag
import logging
from functools import lru_cache

# Set up logging
logger = logging.getLogger(__name__)

# Download NLTK resources with error handling
def setup_nltk():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
    
    try:
        nltk.data.find('taggers/averaged_perceptron_tagger')
    except LookupError:
        nltk.download('averaged_perceptron_tagger', quiet=True)

setup_nltk()

# Cached stop words
stop_words = set(stopwords.words('english'))

# Category keywords (optimized)
CATEGORY_KEYWORDS = {
    "Infrastructure": {"road", "pothole", "bridge", "highway", "street", "traffic", "construction"},
    "Healthcare": {"hospital", "clinic", "doctor", "medicine", "nurse", "health", "medical"},
    "Public Safety": {"crime", "theft", "police", "fire", "emergency", "accident", "safety"},
    "Education": {"school", "teacher", "university", "student", "classroom", "education"},
    "Environment": {"pollution", "waste", "environment", "water", "air", "garbage"}
}

@lru_cache(maxsize=128)
def preprocess_text(text):
    """Preprocess text with caching for better performance."""
    if not text:
        return ""
    return ' '.join(text.lower().split())

def analyze_text(text):
    """Analyze the given text for sentiment, keywords, categories, and named entities."""
    result = {
        "category": "General",
        "sentiment": "Neutral",
        "keywords": [],
        "named_entities": [],
        "confidence": 0.0
    }
    
    try:
        if not text or not isinstance(text, str):
            return result
        
        # Preprocess text
        processed_text = preprocess_text(text)
        if not processed_text:
            return result
        
        # Sentiment Analysis
        blob = TextBlob(processed_text)
        polarity = blob.sentiment.polarity
        
        if polarity > 0.2:
            result["sentiment"] = "Positive"
        elif polarity < -0.2:
            result["sentiment"] = "Negative"
        else:
            result["sentiment"] = "Neutral"
        
        # Keyword Extraction
        tokens = word_tokenize(processed_text)
        keywords = [
            token.lower() for token in tokens
            if (token.isalpha() and token.lower() not in stop_words and len(token) > 2)
        ]
        
        # Get most common keywords
        keyword_freq = Counter(keywords)
        result["keywords"] = [word for word, _ in keyword_freq.most_common(10)]
        
        # Text Categorization
        text_words = set(processed_text.split())
        category_scores = {}
        
        for category, keywords in CATEGORY_KEYWORDS.items():
            matches = text_words.intersection(keywords)
            if matches:
                category_scores[category] = len(matches)
        
        if category_scores:
            result["category"] = max(category_scores, key=category_scores.get)
        
        # Named Entity Recognition
        try:
            entities = ne_chunk(pos_tag(tokens))
            result["named_entities"] = [
                (str(ent), ent.label()) for ent in entities 
                if hasattr(ent, 'label')
            ]
        except Exception as e:
            logger.warning(f"NER failed: {e}")
        
        # Calculate confidence
        confidence_factors = [
            0.3 if result["sentiment"] != "Neutral" else 0.1,
            0.3 if len(result["keywords"]) > 3 else 0.1,
            0.2 if result["category"] != "General" else 0.05,
            0.2 if len(result["named_entities"]) > 0 else 0.05
        ]
        
        result["confidence"] = sum(confidence_factors)
        
    except Exception as e:
        logger.error(f"Error in analyze_text: {e}")
    
    return result