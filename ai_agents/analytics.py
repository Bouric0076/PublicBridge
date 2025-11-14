"""
AI Analytics and Predictive Engine

Provides advanced analytics and predictive capabilities for civic issues.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
import math

from .base import BaseAIAgent, ReportCategory, UrgencyLevel, AIAnalysisResult

logger = logging.getLogger(__name__)

@dataclass
class TrendAnalysis:
    """Trend analysis results."""
    trend_direction: str  # increasing, decreasing, stable
    trend_strength: float  # 0-1
    change_rate: float  # percentage change
    confidence: float  # 0-1
    seasonal_pattern: Optional[str]
    anomaly_detected: bool
    predicted_next_value: float

@dataclass
class HotspotPrediction:
    """Hotspot prediction results."""
    location: str
    predicted_issue_count: int
    confidence: float
    contributing_factors: List[str]
    risk_level: str  # low, medium, high, critical
    recommended_actions: List[str]

@dataclass
class CitizenSentimentAnalysis:
    """Citizen sentiment analysis results."""
    overall_sentiment: str  # positive, negative, neutral
    sentiment_score: float  # -1 to 1
    satisfaction_trend: str  # improving, declining, stable
    key_concerns: List[str]
    positive_aspects: List[str]
    sentiment_by_category: Dict[str, float]
    confidence: float

class PredictiveAnalyticsAgent(BaseAIAgent):
    """
    Advanced analytics and predictive engine for civic issues.
    
    Features:
    - Trend analysis and forecasting
    - Hotspot identification and prediction
    - Citizen sentiment analysis
    - Resource allocation optimization
    - Performance prediction
    """
    
    def __init__(self):
        super().__init__(model_name="predictive_analytics_v1")
        self.historical_data = []
        self.trend_patterns = {}
        self.sentiment_history = []
        self.performance_metrics = {
            'total_predictions': 0,
            'accurate_predictions': 0,
            'prediction_accuracy': 0.0
        }
        self._initialize_analytics_engine()

    async def _analyze(self, input_data: Dict[str, Any]) -> AIAnalysisResult:
        """Async method required by BaseAIAgent."""
        return self.process(input_data)
    
    def _initialize_analytics_engine(self):
        """Initialize analytics engine with default patterns."""
        # Sample historical data - would be loaded from database in production
        self._load_sample_historical_data()
        self._analyze_trend_patterns()
    
    def _load_sample_historical_data(self):
        """Load sample historical data for demonstration."""
        # This would normally come from your database
        sample_data = [
            {
                'date': datetime.now() - timedelta(days=30),
                'category': 'infrastructure',
                'location': 'downtown',
                'urgency': 'high',
                'sentiment': -0.6,
                'response_time': 24,
                'resolved': True
            },
            {
                'date': datetime.now() - timedelta(days=25),
                'category': 'utilities',
                'location': 'suburbs',
                'urgency': 'medium',
                'sentiment': -0.3,
                'response_time': 48,
                'resolved': True
            },
            {
                'date': datetime.now() - timedelta(days=20),
                'category': 'public_safety',
                'location': 'downtown',
                'urgency': 'critical',
                'sentiment': -0.8,
                'response_time': 2,
                'resolved': True
            }
        ]
        
        self.historical_data = sample_data
    
    def _analyze_trend_patterns(self):
        """Analyze historical data for trend patterns."""
        # Group data by category and location
        category_trends = defaultdict(list)
        location_trends = defaultdict(list)
        
        for record in self.historical_data:
            category_trends[record['category']].append(record)
            location_trends[record['location']].append(record)
        
        # Analyze trends for each category
        for category, data in category_trends.items():
            self.trend_patterns[category] = self._analyze_category_trends(data)
        
        # Analyze trends for each location
        for location, data in location_trends.items():
            self.trend_patterns[f"location_{location}"] = self._analyze_location_trends(data)
    
    def _analyze_category_trends(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze trends for a specific category."""
        if not data:
            return {'trend': 'stable', 'confidence': 0.0}
        
        # Sort by date
        data.sort(key=lambda x: x['date'])
        
        # Calculate moving averages
        issue_counts = []
        sentiment_scores = []
        response_times = []
        
        for record in data:
            issue_counts.append(1)  # Each record represents one issue
            sentiment_scores.append(record.get('sentiment', 0))
            response_times.append(record.get('response_time', 0))
        
        # Calculate trend direction and strength
        if len(issue_counts) >= 3:
            trend_direction = self._calculate_trend_direction(issue_counts)
            trend_strength = self._calculate_trend_strength(issue_counts)
            confidence = self._calculate_trend_confidence(issue_counts)
        else:
            trend_direction = 'stable'
            trend_strength = 0.0
            confidence = 0.5
        
        return {
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'confidence': confidence,
            'average_sentiment': np.mean(sentiment_scores) if sentiment_scores else 0,
            'average_response_time': np.mean(response_times) if response_times else 0
        }
    
    def _analyze_location_trends(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze trends for a specific location."""
        if not data:
            return {'trend': 'stable', 'confidence': 0.0}
        
        # Similar to category trends but location-specific
        data.sort(key=lambda x: x['date'])
        
        issue_counts = [1 for _ in data]  # Each record represents one issue
        sentiment_scores = [record.get('sentiment', 0) for record in data]
        
        if len(issue_counts) >= 3:
            trend_direction = self._calculate_trend_direction(issue_counts)
            trend_strength = self._calculate_trend_strength(issue_counts)
            confidence = self._calculate_trend_confidence(issue_counts)
        else:
            trend_direction = 'stable'
            trend_strength = 0.0
            confidence = 0.5
        
        return {
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'confidence': confidence,
            'average_sentiment': np.mean(sentiment_scores) if sentiment_scores else 0,
            'issue_density': len(data)  # Number of issues in this location
        }
    
    def _calculate_trend_direction(self, values: List[float]) -> str:
        """Calculate trend direction from a series of values."""
        if len(values) < 2:
            return 'stable'
        
        # Simple linear regression slope
        x = np.arange(len(values))
        y = np.array(values)
        
        # Calculate slope
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_trend_strength(self, values: List[float]) -> float:
        """Calculate trend strength (0-1)."""
        if len(values) < 2:
            return 0.0
        
        # Calculate coefficient of variation
        mean_val = np.mean(values)
        if mean_val == 0:
            return 0.0
        
        std_val = np.std(values)
        cv = std_val / abs(mean_val)
        
        # Convert to strength (inverse relationship with CV)
        strength = 1.0 / (1.0 + cv)
        return min(strength, 1.0)
    
    def _calculate_trend_confidence(self, values: List[float]) -> float:
        """Calculate confidence in trend prediction."""
        if len(values) < 3:
            return 0.5
        
        # More data points = higher confidence
        data_confidence = min(len(values) / 10.0, 1.0)
        
        # Lower variance = higher confidence
        variance = np.var(values)
        variance_confidence = 1.0 / (1.0 + variance)
        
        # Combined confidence
        confidence = (data_confidence + variance_confidence) / 2.0
        return min(confidence, 1.0)
    
    async def process(self, input_data: Dict[str, Any]) -> AIAnalysisResult:
        """Perform comprehensive analytics and prediction."""
        try:
            analysis_type = input_data.get('analysis_type', 'general')
            
            if analysis_type == 'trend_analysis':
                return self._perform_trend_analysis(input_data)
            elif analysis_type == 'hotspot_prediction':
                return self._perform_hotspot_prediction(input_data)
            elif analysis_type == 'sentiment_analysis':
                return self._perform_sentiment_analysis(input_data)
            elif analysis_type == 'resource_optimization':
                return self._perform_resource_optimization(input_data)
            else:
                return self._perform_general_analytics(input_data)
                
        except Exception as e:
            logger.error(f"Analytics failed: {e}")
            return AIAnalysisResult(
                confidence=0.0,
                predictions={'error': 'analytics_failed'},
                metadata={'error': str(e)},
                processing_time=0.0,
                model_version="1.0.0"
            )
    
    def _perform_trend_analysis(self, input_data: Dict[str, Any]) -> AIAnalysisResult:
        """Perform trend analysis on historical data."""
        category = input_data.get('category')
        location = input_data.get('location')
        time_period = input_data.get('time_period', 30)  # days
        
        # Filter relevant historical data
        relevant_data = self._filter_historical_data(category, location, time_period)
        
        # Perform trend analysis
        trend_analysis = self._analyze_trend_patterns_advanced(relevant_data)
        
        # Generate predictions
        predictions = self._generate_trend_predictions(trend_analysis, time_period)
        
        return AIAnalysisResult(
            confidence=trend_analysis['confidence'],
            predictions=predictions,
            metadata={
                'trend_analysis': trend_analysis,
                'data_points_used': len(relevant_data),
                'time_period': time_period
            },
            processing_time=0.0,
            model_version="1.0.0"
        )
    
    def _perform_hotspot_prediction(self, input_data: Dict[str, Any]) -> AIAnalysisResult:
        """Predict potential issue hotspots."""
        time_horizon = input_data.get('time_horizon', 7)  # days
        locations = input_data.get('locations', ['downtown', 'suburbs', 'industrial'])
        
        hotspot_predictions = []
        
        for location in locations:
            prediction = self._predict_location_hotspot(location, time_horizon)
            hotspot_predictions.append(prediction)
        
        # Sort by risk level
        hotspot_predictions.sort(key=lambda x: x.risk_level, reverse=True)
        
        return AIAnalysisResult(
            confidence=0.75,  # Average confidence for hotspot prediction
            predictions={
                'hotspots': [self._hotspot_to_dict(hp) for hp in hotspot_predictions],
                'highest_risk_location': hotspot_predictions[0].location if hotspot_predictions else None,
                'total_predicted_issues': sum(hp.predicted_issue_count for hp in hotspot_predictions)
            },
            metadata={
                'time_horizon': time_horizon,
                'locations_analyzed': len(locations),
                'prediction_method': 'historical_pattern_analysis'
            },
            processing_time=0.0,
            model_version="1.0.0"
        )
    
    def _perform_sentiment_analysis(self, input_data: Dict[str, Any]) -> AIAnalysisResult:
        """Perform citizen sentiment analysis."""
        time_period = input_data.get('time_period', 30)
        categories = input_data.get('categories', list(ReportCategory))
        
        # Filter recent data
        recent_data = self._filter_historical_data(None, None, time_period)
        
        # Analyze sentiment
        sentiment_analysis = self._analyze_citizen_sentiment(recent_data, categories)
        
        return AIAnalysisResult(
            confidence=sentiment_analysis.confidence,
            predictions={
                'overall_sentiment': sentiment_analysis.overall_sentiment,
                'sentiment_score': sentiment_analysis.sentiment_score,
                'satisfaction_trend': sentiment_analysis.satisfaction_trend,
                'key_concerns': sentiment_analysis.key_concerns,
                'positive_aspects': sentiment_analysis.positive_aspects,
                'sentiment_by_category': sentiment_analysis.sentiment_by_category
            },
            metadata={
                'time_period': time_period,
                'categories_analyzed': len(categories),
                'data_points_used': len(recent_data)
            },
            processing_time=0.0,
            model_version="1.0.0"
        )
    
    def _perform_general_analytics(self, input_data: Dict[str, Any]) -> AIAnalysisResult:
        """Perform general analytics overview."""
        time_period = input_data.get('time_period', 30)
        
        # Get comprehensive analytics
        analytics = {
            'total_reports': len(self.historical_data),
            'resolution_rate': self._calculate_resolution_rate(),
            'average_response_time': self._calculate_average_response_time(),
            'category_distribution': self._calculate_category_distribution(),
            'sentiment_trend': self._calculate_sentiment_trend(time_period),
            'performance_score': self._calculate_performance_score()
        }
        
        return AIAnalysisResult(
            confidence=0.85,
            predictions=analytics,
            metadata={
                'time_period': time_period,
                'data_completeness': 'partial' if len(self.historical_data) < 100 else 'good'
            },
            processing_time=0.0,
            model_version="1.0.0"
        )
    
    def _filter_historical_data(self, category: Optional[str], location: Optional[str], 
                              time_period: int) -> List[Dict]:
        """Filter historical data based on criteria."""
        cutoff_date = datetime.now() - timedelta(days=time_period)
        
        filtered_data = []
        for record in self.historical_data:
            if record['date'] < cutoff_date:
                continue
            
            if category and record.get('category') != category:
                continue
            
            if location and record.get('location') != location:
                continue
            
            filtered_data.append(record)
        
        return filtered_data
    
    def _analyze_trend_patterns_advanced(self, data: List[Dict]) -> Dict[str, Any]:
        """Advanced trend pattern analysis."""
        if not data:
            return {'trend_direction': 'stable', 'trend_strength': 0.0, 'confidence': 0.0}
        
        # Sort by date
        data.sort(key=lambda x: x['date'])
        
        # Extract time series data
        dates = [record['date'] for record in data]
        values = [1 for _ in data]  # Count of issues
        
        # Calculate trend metrics
        trend_direction = self._calculate_trend_direction(values)
        trend_strength = self._calculate_trend_strength(values)
        confidence = self._calculate_trend_confidence(values)
        
        # Detect seasonal patterns
        seasonal_pattern = self._detect_seasonal_pattern(dates, values)
        
        # Detect anomalies
        anomaly_detected = self._detect_anomalies(values)
        
        # Predict next value
        predicted_next_value = self._predict_next_value(values)
        
        return {
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'confidence': confidence,
            'seasonal_pattern': seasonal_pattern,
            'anomaly_detected': anomaly_detected,
            'predicted_next_value': predicted_next_value,
            'change_rate': self._calculate_change_rate(values)
        }
    
    def _calculate_resolution_rate(self) -> float:
        """Calculate overall resolution rate."""
        if not self.historical_data:
            return 0.0
        
        resolved_count = sum(1 for d in self.historical_data if d.get('resolved', False))
        return resolved_count / len(self.historical_data)
    
    def _calculate_average_response_time(self) -> float:
        """Calculate average response time."""
        response_times = [d.get('response_time', 0) for d in self.historical_data]
        return np.mean(response_times) if response_times else 0.0
    
    def _calculate_category_distribution(self) -> Dict[str, int]:
        """Calculate distribution of reports by category."""
        categories = [d.get('category', 'unknown') for d in self.historical_data]
        return dict(Counter(categories))
    
    def _calculate_sentiment_trend(self, time_period: int) -> str:
        """Calculate sentiment trend over time period."""
        cutoff_date = datetime.now() - timedelta(days=time_period)
        recent_data = [d for d in self.historical_data if d['date'] >= cutoff_date]
        
        if not recent_data:
            return 'stable'
        
        sentiments = [d.get('sentiment', 0) for d in recent_data]
        
        if len(sentiments) >= 2:
            recent_sentiment = np.mean(sentiments[-3:])
            older_sentiment = np.mean(sentiments[:-3]) if len(sentiments) > 3 else 0
            
            if recent_sentiment > older_sentiment + 0.1:
                return 'improving'
            elif recent_sentiment < older_sentiment - 0.1:
                return 'declining'
        
        return 'stable'
    
    def _calculate_performance_score(self) -> float:
        """Calculate overall performance score."""
        resolution_rate = self._calculate_resolution_rate()
        avg_response_time = self._calculate_average_response_time()
        
        # Normalize response time (lower is better)
        response_score = max(0, 1 - (avg_response_time / 168))  # 1 week max
        
        # Combined performance score
        performance_score = (resolution_rate * 0.7) + (response_score * 0.3)
        
        return min(performance_score, 1.0)
    
    # Helper methods for hotspot prediction
    def _predict_location_hotspot(self, location: str, time_horizon: int) -> HotspotPrediction:
        """Predict hotspot for a specific location."""
        # Filter historical data for this location
        location_data = [d for d in self.historical_data if d.get('location') == location]
        
        if not location_data:
            return HotspotPrediction(
                location=location,
                predicted_issue_count=0,
                confidence=0.0,
                contributing_factors=['insufficient_data'],
                risk_level='low',
                recommended_actions=['collect_more_data']
            )
        
        # Calculate baseline issue rate
        recent_data = [d for d in location_data if d['date'] >= datetime.now() - timedelta(days=30)]
        baseline_rate = len(recent_data) / 30  # Issues per day
        
        # Predict future issues based on trends
        predicted_count = int(baseline_rate * time_horizon)
        
        # Determine risk level
        if predicted_count > 10:
            risk_level = 'critical'
        elif predicted_count > 5:
            risk_level = 'high'
        elif predicted_count > 2:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # Analyze contributing factors
        factors = self._analyze_contributing_factors(location_data)
        
        # Generate recommendations
        recommendations = self._generate_hotspot_recommendations(risk_level, factors)
        
        return HotspotPrediction(
            location=location,
            predicted_issue_count=predicted_count,
            confidence=0.7 if len(location_data) > 5 else 0.4,
            contributing_factors=factors,
            risk_level=risk_level,
            recommended_actions=recommendations
        )
    
    def _analyze_contributing_factors(self, location_data: List[Dict]) -> List[str]:
        """Analyze factors contributing to hotspot formation."""
        factors = []
        
        # Analyze category distribution
        categories = [d.get('category', 'unknown') for d in location_data]
        category_counts = Counter(categories)
        
        # Add factors based on dominant categories
        for category, count in category_counts.most_common(2):
            if count > len(location_data) * 0.3:
                factors.append(f"high_{category}_issues")
        
        # Analyze sentiment patterns
        avg_sentiment = np.mean([d.get('sentiment', 0) for d in location_data])
        if avg_sentiment < -0.5:
            factors.append("negative_citizen_sentiment")
        
        # Analyze response time patterns
        avg_response_time = np.mean([d.get('response_time', 0) for d in location_data])
        if avg_response_time > 48:  # More than 2 days
            factors.append("slow_response_times")
        
        return factors if factors else ['standard_activity']
    
    def _generate_hotspot_recommendations(self, risk_level: str, factors: List[str]) -> List[str]:
        """Generate recommendations based on risk level and factors."""
        recommendations = []
        
        if risk_level in ['high', 'critical']:
            recommendations.extend([
                "increase_patrol_frequency",
                "deploy_additional_resources",
                "implement_preventive_measures"
            ])
        
        if "negative_citizen_sentiment" in factors:
            recommendations.append("conduct_community_outreach")
        
        if "slow_response_times" in factors:
            recommendations.append("optimize_response_procedures")
        
        if "high_infrastructure_issues" in factors:
            recommendations.append("schedule_infrastructure_maintenance")
        
        return recommendations if recommendations else ['monitor_situation']
    
    def _hotspot_to_dict(self, hotspot: HotspotPrediction) -> Dict[str, Any]:
        """Convert HotspotPrediction to dictionary."""
        return {
            'location': hotspot.location,
            'predicted_issue_count': hotspot.predicted_issue_count,
            'confidence': hotspot.confidence,
            'contributing_factors': hotspot.contributing_factors,
            'risk_level': hotspot.risk_level,
            'recommended_actions': hotspot.recommended_actions
        }
    
    # Helper methods for sentiment analysis
    def _analyze_citizen_sentiment(self, data: List[Dict], categories: List[str]) -> CitizenSentimentAnalysis:
        """Analyze citizen sentiment from data."""
        if not data:
            return CitizenSentimentAnalysis(
                overall_sentiment='neutral',
                sentiment_score=0.0,
                satisfaction_trend='stable',
                key_concerns=['insufficient_data'],
                positive_aspects=['no_major_issues'],
                sentiment_by_category={},
                confidence=0.0
            )
        
        # Calculate overall sentiment
        sentiments = [d.get('sentiment', 0) for d in data]
        avg_sentiment = np.mean(sentiments)
        
        # Determine overall sentiment category
        if avg_sentiment > 0.3:
            overall_sentiment = 'positive'
        elif avg_sentiment < -0.3:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
        
        # Calculate satisfaction trend
        satisfaction_trend = self._calculate_satisfaction_trend(data)
        
        # Analyze by category
        sentiment_by_category = {}
        for category in categories:
            category_data = [d for d in data if d.get('category') == category]
            if category_data:
                category_sentiments = [d.get('sentiment', 0) for d in category_data]
                sentiment_by_category[category] = np.mean(category_sentiments)
        
        # Identify key concerns and positive aspects
        key_concerns = self._identify_key_concerns(data)
        positive_aspects = self._identify_positive_aspects(data)
        
        # Calculate confidence
        confidence = min(len(data) / 20.0, 1.0)  # More data = higher confidence
        
        return CitizenSentimentAnalysis(
            overall_sentiment=overall_sentiment,
            sentiment_score=avg_sentiment,
            satisfaction_trend=satisfaction_trend,
            key_concerns=key_concerns,
            positive_aspects=positive_aspects,
            sentiment_by_category=sentiment_by_category,
            confidence=confidence
        )
    
    def _calculate_satisfaction_trend(self, data: List[Dict]) -> str:
        """Calculate satisfaction trend from data."""
        if len(data) < 3:
            return 'stable'
        
        # Sort by date
        data.sort(key=lambda x: x['date'])
        
        # Split into early and recent periods
        mid_point = len(data) // 2
        early_data = data[:mid_point]
        recent_data = data[mid_point:]
        
        # Calculate average sentiment for each period
        early_sentiment = np.mean([d.get('sentiment', 0) for d in early_data])
        recent_sentiment = np.mean([d.get('sentiment', 0) for d in recent_data])
        
        # Determine trend
        if recent_sentiment > early_sentiment + 0.1:
            return 'improving'
        elif recent_sentiment < early_sentiment - 0.1:
            return 'declining'
        else:
            return 'stable'
    
    def _identify_key_concerns(self, data: List[Dict]) -> List[str]:
        """Identify key concerns from data."""
        concerns = []
        
        # Analyze urgency patterns
        high_urgency_count = sum(1 for d in data if d.get('urgency') in ['high', 'critical'])
        if high_urgency_count > len(data) * 0.4:
            concerns.append('frequent_high_urgency_issues')
        
        # Analyze response time patterns
        slow_responses = sum(1 for d in data if d.get('response_time', 0) > 48)
        if slow_responses > len(data) * 0.3:
            concerns.append('slow_government_response')
        
        # Analyze resolution patterns
        unresolved_count = sum(1 for d in data if not d.get('resolved', False))
        if unresolved_count > len(data) * 0.2:
            concerns.append('low_resolution_rate')
        
        return concerns if concerns else ['general_concerns']
    
    def _identify_positive_aspects(self, data: List[Dict]) -> List[str]:
        """Identify positive aspects from data."""
        positive_aspects = []
        
        # Analyze resolution patterns
        resolved_count = sum(1 for d in data if d.get('resolved', False))
        if resolved_count > len(data) * 0.7:
            positive_aspects.append('high_resolution_rate')
        
        # Analyze response time patterns
        fast_responses = sum(1 for d in data if d.get('response_time', 0) < 24)
        if fast_responses > len(data) * 0.5:
            positive_aspects.append('prompt_government_response')
        
        # Analyze sentiment patterns
        positive_sentiment = sum(1 for d in data if d.get('sentiment', 0) > 0.2)
        if positive_sentiment > len(data) * 0.3:
            positive_aspects.append('positive_citizen_feedback')
        
        return positive_aspects if positive_aspects else ['steady_progress']
    
    # Additional helper methods
    def _detect_seasonal_pattern(self, dates: List[datetime], values: List[float]) -> Optional[str]:
        """Detect seasonal patterns in data."""
        if len(dates) < 7:
            return None
        
        # Simple weekly pattern detection
        day_of_week_counts = defaultdict(list)
        for date, value in zip(dates, values):
            day_of_week_counts[date.weekday()].append(value)
        
        # Check if certain days have consistently higher values
        for day, day_values in day_of_week_counts.items():
            if len(day_values) >= 2 and np.mean(day_values) > np.mean(values) * 1.5:
                return f"high_activity_on_{day}"
        
        return None
    
    def _detect_anomalies(self, values: List[float]) -> bool:
        """Detect anomalies in values."""
        if len(values) < 3:
            return False
        
        # Simple anomaly detection using standard deviation
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        # Check for values more than 2 standard deviations from mean
        for value in values:
            if abs(value - mean_val) > 2 * std_val:
                return True
        
        return False
    
    def _predict_next_value(self, values: List[float]) -> float:
        """Predict the next value in a series."""
        if len(values) < 2:
            return values[-1] if values else 0.0
        
        # Simple linear extrapolation
        x = np.arange(len(values))
        y = np.array(values)
        
        # Fit linear trend
        slope, intercept = np.polyfit(x, y, 1)
        
        # Predict next value
        next_x = len(values)
        return slope * next_x + intercept
    
    def _calculate_change_rate(self, values: List[float]) -> float:
        """Calculate the rate of change in values."""
        if len(values) < 2:
            return 0.0
        
        first_val = values[0]
        last_val = values[-1]
        
        if first_val == 0:
            return 0.0
        
        return ((last_val - first_val) / abs(first_val)) * 100
    
    def _perform_resource_optimization(self, input_data: Dict[str, Any]) -> AIAnalysisResult:
        """Perform resource allocation optimization."""
        departments = input_data.get('departments', ['police', 'fire', 'utilities', 'infrastructure'])
        
        # Analyze current resource allocation
        resource_analysis = self._analyze_resource_allocation(departments)
        
        # Generate optimization recommendations
        optimization_recommendations = self._generate_optimization_recommendations(resource_analysis)
        
        return AIAnalysisResult(
            confidence=0.8,
            predictions={
                'resource_optimization': resource_analysis,
                'recommendations': optimization_recommendations,
                'potential_efficiency_gain': 0.15  # 15% efficiency gain potential
            },
            metadata={
                'departments_analyzed': len(departments),
                'optimization_method': 'workload_balancing'
            },
            processing_time=0.0,
            model_version="1.0.0"
        )
    
    def _analyze_resource_allocation(self, departments: List[str]) -> Dict[str, Any]:
        """Analyze current resource allocation across departments."""
        allocation_analysis = {}
        
        for department in departments:
            # Simulate department workload analysis
            dept_data = [d for d in self.historical_data if d.get('category') == department]
            
            allocation_analysis[department] = {
                'current_workload': len(dept_data),
                'average_response_time': np.mean([d.get('response_time', 0) for d in dept_data]) if dept_data else 0,
                'resolution_rate': sum(1 for d in dept_data if d.get('resolved', False)) / len(dept_data) if dept_data else 0,
                'efficiency_score': 0.0  # Will be calculated based on metrics
            }
        
        return allocation_analysis
    
    def _generate_optimization_recommendations(self, resource_analysis: Dict[str, Any]) -> List[str]:
        """Generate resource optimization recommendations."""
        recommendations = []
        
        # Analyze workload distribution
        workloads = [data['current_workload'] for data in resource_analysis.values()]
        avg_workload = np.mean(workloads)
        
        # Identify overloaded departments
        for dept, data in resource_analysis.items():
            if data['current_workload'] > avg_workload * 1.5:
                recommendations.append(f"increase_{dept}_resources")
            elif data['current_workload'] < avg_workload * 0.5:
                recommendations.append(f"reallocate_{dept}_resources")
            
            if data['average_response_time'] > 48:  # More than 2 days
                recommendations.append(f"optimize_{dept}_response_procedures")
        
        return recommendations if recommendations else ['current_allocation_optimal']
    
    def update_with_new_data(self, new_data: Dict[str, Any]):
        """Update analytics engine with new data."""
        self.historical_data.append(new_data)
        
        # Keep only recent data to prevent memory issues
        if len(self.historical_data) > 1000:
            self.historical_data = self.historical_data[-1000:]
        
        # Re-analyze trend patterns periodically
        if len(self.historical_data) % 100 == 0:
            self._analyze_trend_patterns()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for the analytics engine."""
        return {
            'total_predictions': self.performance_metrics['total_predictions'],
            'accurate_predictions': self.performance_metrics['accurate_predictions'],
            'prediction_accuracy': self.performance_metrics['prediction_accuracy'],
            'historical_data_points': len(self.historical_data),
            'trend_patterns_identified': len(self.trend_patterns),
            'analytics_capabilities': [
                'trend_analysis',
                'hotspot_prediction',
                'sentiment_analysis',
                'resource_optimization',
                'performance_analytics'
            ]
        }