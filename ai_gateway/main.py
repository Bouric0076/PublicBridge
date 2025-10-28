from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import torch
import asyncio
import logging
from datetime import datetime
import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import nltk
from textblob import TextBlob
import os
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import PlainTextResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PublicBridge AI Gateway",
    description="AI-powered analysis and processing for citizen reports",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
REQUEST_COUNT = Counter('ai_gateway_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('ai_gateway_request_duration_seconds', 'Request latency')
ANALYSIS_ERRORS = Counter('ai_gateway_analysis_errors_total', 'Analysis errors', ['analysis_type'])

# Pydantic models
class ReportData(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1, max_length=5000)
    category: Optional[str] = None
    location: Optional[str] = None
    urgency: Optional[str] = None

class AIAnalysisRequest(BaseModel):
    report: ReportData
    analysis_types: List[str] = Field(default=["sentiment", "urgency", "category"])
    include_explanation: bool = True

class AIAnalysisResponse(BaseModel):
    report_id: str
    sentiment_score: float
    urgency_score: float
    category_prediction: str
    confidence_scores: Dict[str, float]
    explanation: Optional[str] = None
    processing_time: float
    model_version: str

class BatchAnalysisRequest(BaseModel):
    reports: List[ReportData]
    analysis_types: List[str] = Field(default=["sentiment", "urgency", "category"])

class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    model_status: Dict[str, str]
    uptime: float

# AI Model Manager
class AIModelManager:
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_cache = {}
        
    async def initialize_models(self):
        """Initialize and cache AI models."""
        try:
            # Sentiment Analysis Model
            self.models['sentiment'] = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Text Classification Model for categories
            self.models['category'] = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # Urgency Detection Model (custom fine-tuned)
            self.models['urgency'] = pipeline(
                "text-classification",
                model="distilbert-base-uncased",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("AI models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI models: {e}")
            raise
    
    def get_sentiment_score(self, text: str) -> float:
        """Calculate sentiment score (-1 to 1)."""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            # Convert from TextBlob scale (-1 to 1) to our scale (0 to 1)
            return (polarity + 1) / 2
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            ANALYSIS_ERRORS.labels(analysis_type='sentiment').inc()
            return 0.5  # Neutral as fallback
    
    def get_urgency_score(self, text: str, title: str) -> float:
        """Calculate urgency score (0 to 1)."""
        try:
            # Combine title and description for analysis
            combined_text = f"{title} {text}"
            
            # Keywords indicating high urgency
            urgent_keywords = [
                'emergency', 'urgent', 'immediate', 'critical', 'dangerous',
                'life-threatening', 'fire', 'flood', 'collapse', 'explosion',
                'injury', 'medical', 'hospital', 'ambulance', 'police'
            ]
            
            text_lower = combined_text.lower()
            urgency_score = 0.0
            
            # Check for urgent keywords
            for keyword in urgent_keywords:
                if keyword in text_lower:
                    urgency_score += 0.2
            
            # Use AI model for additional context
            if 'urgency' in self.models:
                result = self.models['urgency'](combined_text[:512])  # Limit text length
                # Map model output to urgency score
                if result[0]['label'] == 'URGENT':
                    urgency_score = max(urgency_score, result[0]['score'])
            
            return min(urgency_score, 1.0)
            
        except Exception as e:
            logger.error(f"Urgency analysis error: {e}")
            ANALYSIS_ERRORS.labels(analysis_type='urgency').inc()
            return 0.3  # Medium urgency as fallback
    
    def predict_category(self, text: str, title: str) -> tuple[str, dict]:
        """Predict category and return confidence scores."""
        try:
            categories = [
                'Infrastructure',
                'Safety',
                'Environmental',
                'Health',
                'Transportation',
                'Utilities',
                'Public Services',
                'Other'
            ]
            
            combined_text = f"{title} {text}"
            
            if 'category' in self.models:
                result = self.models['category'](
                    combined_text[:512],  # Limit text length
                    candidate_labels=categories
                )
                
                predicted_category = result['labels'][0]
                confidence_scores = dict(zip(result['labels'], result['scores']))
                
                return predicted_category, confidence_scores
            else:
                # Fallback to keyword-based classification
                return self._keyword_based_category(text, title)
                
        except Exception as e:
            logger.error(f"Category prediction error: {e}")
            ANALYSIS_ERRORS.labels(analysis_type='category').inc()
            return 'Other', {'Other': 0.5}
    
    def _keyword_based_category(self, text: str, title: str) -> tuple[str, dict]:
        """Fallback keyword-based category prediction."""
        combined_text = f"{title} {text}".lower()
        
        category_keywords = {
            'Infrastructure': ['road', 'bridge', 'building', 'construction', 'damage'],
            'Safety': ['dangerous', 'unsafe', 'hazard', 'risk', 'threat'],
            'Environmental': ['pollution', 'waste', 'trash', 'environment', 'green'],
            'Health': ['medical', 'health', 'hospital', 'clinic', 'doctor'],
            'Transportation': ['traffic', 'parking', 'transport', 'bus', 'train'],
            'Utilities': ['water', 'electricity', 'power', 'gas', 'internet'],
            'Public Services': ['police', 'fire', 'emergency', 'service', 'government']
        }
        
        scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            scores[category] = min(score * 0.2, 1.0)
        
        if not scores or max(scores.values()) == 0:
            return 'Other', {'Other': 1.0}
        
        predicted_category = max(scores, key=scores.get)
        return predicted_category, scores

# Initialize model manager
model_manager = AIModelManager()

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize models on startup."""
    await model_manager.initialize_models()
    logger.info("AI Gateway started successfully")

# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        model_status={name: "loaded" for name in model_manager.models},
        uptime=0.0  # Calculate actual uptime in production
    )

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(generate_latest())

# AI Analysis endpoint
@app.post("/analyze", response_model=AIAnalysisResponse)
async def analyze_report(request: AIAnalysisRequest, background_tasks: BackgroundTasks):
    """Analyze a single report using AI models."""
    start_time = datetime.utcnow()
    
    try:
        REQUEST_COUNT.labels(method="POST", endpoint="/analyze").inc()
        
        report = request.report
        analysis_types = request.analysis_types
        
        # Perform analysis
        sentiment_score = 0.5
        urgency_score = 0.3
        category_prediction = "Other"
        confidence_scores = {}
        explanation = None
        
        if "sentiment" in analysis_types:
            sentiment_score = model_manager.get_sentiment_score(report.description)
        
        if "urgency" in analysis_types:
            urgency_score = model_manager.get_urgency_score(report.description, report.title)
        
        if "category" in analysis_types:
            category_prediction, confidence_scores = model_manager.predict_category(
                report.description, report.title
            )
        
        # Generate explanation if requested
        if request.include_explanation:
            explanation = f"Report shows {category_prediction.lower()} issue with "
            explanation += f"{'high' if urgency_score > 0.7 else 'medium' if urgency_score > 0.3 else 'low'} urgency. "
            explanation += f"Sentiment is {'positive' if sentiment_score > 0.6 else 'negative' if sentiment_score < 0.4 else 'neutral'}."
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        response = AIAnalysisResponse(
            report_id=f"report_{int(start_time.timestamp())}",
            sentiment_score=sentiment_score,
            urgency_score=urgency_score,
            category_prediction=category_prediction,
            confidence_scores=confidence_scores,
            explanation=explanation,
            processing_time=processing_time,
            model_version="1.0.0"
        )
        
        # Log processing time
        REQUEST_LATENCY.observe(processing_time)
        
        return response
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Analysis failed")

# Batch analysis endpoint
@app.post("/analyze/batch")
async def analyze_batch_reports(request: BatchAnalysisRequest):
    """Analyze multiple reports in batch."""
    try:
        REQUEST_COUNT.labels(method="POST", endpoint="/analyze/batch").inc()
        
        results = []
        for i, report in enumerate(request.reports):
            # Process each report
            single_request = AIAnalysisRequest(
                report=report,
                analysis_types=request.analysis_types
            )
            
            # Use the analyze function but don't return HTTP response
            result = await analyze_report(single_request, BackgroundTasks())
            results.append(result)
        
        return {
            "results": results,
            "total_processed": len(results),
            "analysis_types": request.analysis_types
        }
        
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Batch analysis failed")

# Model information endpoint
@app.get("/models")
async def get_model_info():
    """Get information about loaded AI models."""
    return {
        "models": list(model_manager.models.keys()),
        "device": str(model_manager.device),
        "model_versions": {
            "sentiment": "distilbert-base-uncased-finetuned-sst-2-english",
            "category": "facebook/bart-large-mnli",
            "urgency": "distilbert-base-uncased"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)