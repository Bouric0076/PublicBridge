# utils/nlp_utils.py  
import nltk  
from textblob import TextBlob  
from collections import Counter  
from nltk.tokenize import word_tokenize, sent_tokenize  
from nltk.corpus import stopwords  
from nltk import ne_chunk, pos_tag  

# Download necessary NLTK resources (do this only once)  
nltk.download('punkt')  
nltk.download('stopwords')  
nltk.download('averaged_perceptron_tagger')  
nltk.download('maxent_ne_chunker')  
nltk.download('words')  

# Define the stop words  
stop_words = set(stopwords.words('english'))  

def analyze_text(text):  
    """Analyze the given text for sentiment, keywords, categories, and named entities."""  

    result = {  
        "category": "General",  
        "sentiment": None,  
        "keywords": [],  
        "named_entities": []  
    }  

    # Sentiment Analysis  
    blob = TextBlob(text)  
    polarity = blob.sentiment.polarity  
    subjectivity = blob.sentiment.subjectivity  

    if polarity > 0.2:  
        result["sentiment"] = "Positive"  
    elif polarity < -0.2:  
        result["sentiment"] = "Negative"  
    else:  
        result["sentiment"] = "Neutral"  

    # Keyword Extraction (Excludes Stopwords and Short Words)  
    tokens = word_tokenize(text)  # Tokenizing the text into words  
    keywords = [  
        token.lower() for token in tokens  
        if token.isalpha() and token.lower() not in stop_words and len(token) > 2  
    ]  

    # Frequency-based Keyword Filtering  
    most_common_keywords = [word for word, count in Counter(keywords).most_common(10)]  
    result["keywords"] = most_common_keywords  

    # Named Entity Recognition (NER)  
    named_entities = ne_chunk(pos_tag(tokens))  
    result["named_entities"] = [(str(ent), ent.label()) for ent in named_entities if hasattr(ent, 'label')]  

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