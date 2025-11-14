"""
AI Routing Engine Agent

Intelligently routes reports to appropriate government departments and officials.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

from .base import BaseAIAgent, ReportCategory, UrgencyLevel, AIAnalysisResult

logger = logging.getLogger(__name__)

@dataclass
class DepartmentProfile:
    """Profile of a government department for routing decisions."""
    department_id: str
    name: str
    category_expertise: List[ReportCategory]
    current_workload: int
    average_response_time: float  # hours
    success_rate: float  # 0-1
    active_staff: int
    escalation_level: int  # 1-3
    contact_info: Dict[str, str]
    geographic_coverage: List[str]  # regions covered
    specializations: List[str]

@dataclass
class RoutingDecision:
    """Decision result for report routing."""
    department_id: str
    department_name: str
    confidence_score: float
    routing_reason: str
    estimated_response_time: float
    escalation_path: List[str]
    alternative_departments: List[str]
    priority_adjustment: str  # boost, maintain, reduce

class RoutingEngineAgent(BaseAIAgent):
    """
    AI-powered routing engine for intelligent report assignment.
    
    Features:
    - Smart department matching based on category expertise
    - Workload balancing and performance optimization
    - Escalation path generation
    - Geographic and specialization matching
    - Response time prediction
    """
    
    def __init__(self):
        super().__init__()
        self.department_profiles = {}
        self.routing_history = []
        self.performance_metrics = {
            'total_routes': 0,
            'successful_routes': 0,
            'average_response_time': 0.0,
            'user_satisfaction': 0.0
        }
        self._initialize_department_profiles()
    
    def _initialize_department_profiles(self):
        """Initialize department profiles with expertise mapping."""
        # Sample department profiles - would be loaded from database in production
        self.department_profiles = {
            'emergency_services': DepartmentProfile(
                department_id='emergency_services',
                name='Emergency Services',
                category_expertise=[ReportCategory.EMERGENCY, ReportCategory.PUBLIC_SAFETY],
                current_workload=15,
                average_response_time=0.5,  # 30 minutes
                success_rate=0.95,
                active_staff=25,
                escalation_level=1,
                contact_info={'email': 'emergency@gov.gov', 'phone': '911'},
                geographic_coverage=['all_regions'],
                specializations=['fire', 'medical', 'police']
            ),
            'public_works': DepartmentProfile(
                department_id='public_works',
                name='Public Works Department',
                category_expertise=[ReportCategory.INFRASTRUCTURE, ReportCategory.UTILITIES, ReportCategory.TRANSPORTATION],
                current_workload=45,
                average_response_time=24.0,  # 24 hours
                success_rate=0.85,
                active_staff=40,
                escalation_level=2,
                contact_info={'email': 'publicworks@gov.gov', 'phone': '555-0101'},
                geographic_coverage=['all_regions'],
                specializations=['roads', 'bridges', 'water', 'electricity']
            ),
            'health_department': DepartmentProfile(
                department_id='health_department',
                name='Health Department',
                category_expertise=[ReportCategory.HEALTHCARE, ReportCategory.ENVIRONMENT],
                current_workload=30,
                average_response_time=12.0,  # 12 hours
                success_rate=0.90,
                active_staff=35,
                escalation_level=2,
                contact_info={'email': 'health@gov.gov', 'phone': '555-0202'},
                geographic_coverage=['all_regions'],
                specializations=['medical', 'sanitation', 'epidemic']
            ),
            'anti_corruption': DepartmentProfile(
                department_id='anti_corruption',
                name='Anti-Corruption Bureau',
                category_expertise=[ReportCategory.CORRUPTION, ReportCategory.GOVERNMENT_SERVICES],
                current_workload=20,
                average_response_time=48.0,  # 48 hours
                success_rate=0.88,
                active_staff=15,
                escalation_level=3,
                contact_info={'email': 'anticorruption@gov.gov', 'phone': '555-0303'},
                geographic_coverage=['all_regions'],
                specializations=['investigation', 'audit', 'transparency']
            ),
            'education_services': DepartmentProfile(
                department_id='education_services',
                name='Education Services',
                category_expertise=[ReportCategory.EDUCATION],
                current_workload=25,
                average_response_time=72.0,  # 72 hours
                success_rate=0.82,
                active_staff=20,
                escalation_level=2,
                contact_info={'email': 'education@gov.gov', 'phone': '555-0404'},
                geographic_coverage=['all_regions'],
                specializations=['schools', 'universities', 'training']
            ),
            'general_administration': DepartmentProfile(
                department_id='general_administration',
                name='General Administration',
                category_expertise=[ReportCategory.GENERAL, ReportCategory.GOVERNMENT_SERVICES],
                current_workload=35,
                average_response_time=96.0,  # 96 hours
                success_rate=0.80,
                active_staff=30,
                escalation_level=2,
                contact_info={'email': 'admin@gov.gov', 'phone': '555-0505'},
                geographic_coverage=['all_regions'],
                specializations=['general', 'citizen_services']
            )
        }
    
    def _analyze_data(self, input_data: Dict[str, Any]) -> AIAnalysisResult:
        """Analyze report and determine optimal routing."""
        try:
            report_text = input_data.get('text', '')
            report_category = input_data.get('category', ReportCategory.GENERAL)
            urgency = input_data.get('urgency', UrgencyLevel.MEDIUM)
            location = input_data.get('location', '')
            citizen_demographics = input_data.get('citizen_demographics', {})
            
            # Find best matching departments
            candidate_departments = self._find_candidate_departments(
                report_category, location, urgency
            )
            
            # Score and rank departments
            ranked_departments = self._score_and_rank_departments(
                candidate_departments, report_text, urgency, location
            )
            
            # Generate routing decision
            routing_decision = self._generate_routing_decision(
                ranked_departments, report_text, urgency
            )
            
            # Generate escalation path
            escalation_path = self._generate_escalation_path(
                routing_decision, urgency
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_routing_confidence(
                routing_decision, ranked_departments
            )
            
            predictions = {
                'primary_department': routing_decision.department_id,
                'department_name': routing_decision.department_name,
                'confidence_score': confidence_score,
                'routing_reason': routing_decision.routing_reason,
                'estimated_response_time': routing_decision.estimated_response_time,
                'escalation_path': escalation_path,
                'alternative_departments': routing_decision.alternative_departments,
                'priority_adjustment': routing_decision.priority_adjustment,
                'department_contact': routing_decision.department_id,
                'workload_impact': self._calculate_workload_impact(routing_decision.department_id)
            }
            
            # Record routing decision
            self._record_routing_decision(input_data, routing_decision, confidence_score)
            
            return AIAnalysisResult(
                confidence=confidence_score,
                predictions=predictions,
                metadata={
                    'candidate_departments': len(candidate_departments),
                    'ranked_departments': len(ranked_departments),
                    'department_profiles_considered': list(self.department_profiles.keys())
                },
                processing_time=0.0,  # Will be set by base class
                model_version="1.0.0"
            )
            
        except Exception as e:
            logger.error(f"Routing analysis failed: {e}")
            return AIAnalysisResult(
                confidence=0.0,
                predictions={'error': 'routing_failed', 'fallback_department': 'general_administration'},
                metadata={'error': str(e)},
                processing_time=0.0,
                model_version="1.0.0"
            )
    
    def _find_candidate_departments(self, category: ReportCategory, location: str, 
                                   urgency: UrgencyLevel) -> List[DepartmentProfile]:
        """Find departments that can handle the report category and location."""
        candidates = []
        
        for dept in self.department_profiles.values():
            # Check category expertise
            if category in dept.category_expertise:
                candidates.append(dept)
            # Also include general administration for fallback
            elif dept.department_id == 'general_administration' and len(candidates) == 0:
                candidates.append(dept)
        
        return candidates
    
    def _score_and_rank_departments(self, departments: List[DepartmentProfile], 
                                  report_text: str, urgency: UrgencyLevel, 
                                  location: str) -> List[Tuple[DepartmentProfile, float]]:
        """Score and rank departments based on multiple factors."""
        scored_departments = []
        
        for dept in departments:
            score = self._calculate_department_score(dept, report_text, urgency, location)
            scored_departments.append((dept, score))
        
        # Sort by score (highest first)
        scored_departments.sort(key=lambda x: x[1], reverse=True)
        
        return scored_departments
    
    def _calculate_department_score(self, dept: DepartmentProfile, report_text: str, 
                                  urgency: UrgencyLevel, location: str) -> float:
        """Calculate comprehensive score for department assignment."""
        score = 0.0
        
        # Workload factor (inverse - lower workload is better)
        max_workload = max(d.current_workload for d in self.department_profiles.values())
        workload_score = 1.0 - (dept.current_workload / max_workload)
        score += workload_score * 0.25
        
        # Performance factor (success rate)
        score += dept.success_rate * 0.20
        
        # Response time factor (faster is better)
        max_response_time = max(d.average_response_time for d in self.department_profiles.values())
        response_score = 1.0 - (dept.average_response_time / max_response_time)
        score += response_score * 0.20
        
        # Staff availability factor
        avg_staff = sum(d.active_staff for d in self.department_profiles.values()) / len(self.department_profiles)
        staff_score = min(dept.active_staff / avg_staff, 1.0)
        score += staff_score * 0.15
        
        # Urgency matching factor
        urgency_score = self._calculate_urgency_match_score(dept, urgency)
        score += urgency_score * 0.20
        
        return score
    
    def _calculate_urgency_match_score(self, dept: DepartmentProfile, 
                                     urgency: UrgencyLevel) -> float:
        """Calculate how well department matches urgency requirements."""
        urgency_weights = {
            UrgencyLevel.CRITICAL: 1.0,
            UrgencyLevel.HIGH: 0.8,
            UrgencyLevel.MEDIUM: 0.6,
            UrgencyLevel.LOW: 0.4
        }
        
        # Departments with higher escalation levels handle critical issues better
        escalation_factor = dept.escalation_level / 3.0
        urgency_match = urgency_weights.get(urgency, 0.5)
        
        return min(escalation_factor + urgency_match, 1.0)
    
    def _generate_routing_decision(self, ranked_departments: List[Tuple[DepartmentProfile, float]],
                                 report_text: str, urgency: UrgencyLevel) -> RoutingDecision:
        """Generate final routing decision based on rankings."""
        if not ranked_departments:
            # Fallback to general administration
            fallback_dept = self.department_profiles['general_administration']
            return RoutingDecision(
                department_id=fallback_dept.department_id,
                department_name=fallback_dept.name,
                confidence_score=0.3,
                routing_reason='Fallback: No suitable departments found',
                estimated_response_time=fallback_dept.average_response_time,
                escalation_path=[fallback_dept.department_id],
                alternative_departments=[],
                priority_adjustment='maintain'
            )
        
        best_dept, best_score = ranked_departments[0]
        
        # Generate routing reason
        routing_reason = self._generate_routing_reason(best_dept, best_score, urgency)
        
        # Estimate response time based on current workload
        estimated_response_time = self._estimate_response_time(best_dept, urgency)
        
        # Generate escalation path
        escalation_path = self._generate_escalation_path(best_dept, urgency)
        
        # Determine alternative departments
        alternative_departments = [dept.department_id for dept, score in ranked_departments[1:4]]
        
        # Determine priority adjustment
        priority_adjustment = self._determine_priority_adjustment(best_score, urgency)
        
        return RoutingDecision(
            department_id=best_dept.department_id,
            department_name=best_dept.name,
            confidence_score=best_score,
            routing_reason=routing_reason,
            estimated_response_time=estimated_response_time,
            escalation_path=escalation_path,
            alternative_departments=alternative_departments,
            priority_adjustment=priority_adjustment
        )
    
    def _generate_routing_reason(self, dept: DepartmentProfile, score: float, 
                               urgency: UrgencyLevel) -> str:
        """Generate human-readable routing reason."""
        reasons = []
        
        if urgency == UrgencyLevel.CRITICAL:
            reasons.append("Critical urgency requires immediate attention")
        
        if score >= 0.8:
            reasons.append("Excellent department match")
        elif score >= 0.6:
            reasons.append("Good department expertise match")
        else:
            reasons.append("Best available department")
        
        if dept.success_rate >= 0.9:
            reasons.append("High success rate")
        
        if dept.average_response_time <= 12:
            reasons.append("Fast response capability")
        
        return ", ".join(reasons)
    
    def _estimate_response_time(self, dept: DepartmentProfile, urgency: UrgencyLevel) -> float:
        """Estimate response time based on department performance and urgency."""
        base_time = dept.average_response_time
        
        # Adjust based on current workload
        workload_factor = 1.0 + (dept.current_workload / 100.0)
        
        # Adjust based on urgency (critical issues get faster response)
        urgency_factors = {
            UrgencyLevel.CRITICAL: 0.3,
            UrgencyLevel.HIGH: 0.7,
            UrgencyLevel.MEDIUM: 1.0,
            UrgencyLevel.LOW: 1.2
        }
        
        urgency_factor = urgency_factors.get(urgency, 1.0)
        
        return base_time * workload_factor * urgency_factor
    
    def _generate_escalation_path(self, routing_decision: RoutingDecision, 
                                urgency: UrgencyLevel) -> List[str]:
        """Generate escalation path for the report."""
        primary_dept_id = routing_decision.department_id
        escalation_path = [primary_dept_id]
        
        # Add escalation levels based on urgency
        if urgency == UrgencyLevel.CRITICAL:
            escalation_path.append('emergency_services')
            escalation_path.append('mayor_office')
        elif urgency == UrgencyLevel.HIGH:
            escalation_path.append('general_administration')
        
        return escalation_path
    
    def _determine_priority_adjustment(self, score: float, urgency: UrgencyLevel) -> str:
        """Determine if priority should be boosted, maintained, or reduced."""
        if urgency == UrgencyLevel.CRITICAL or score >= 0.9:
            return 'boost'
        elif urgency == UrgencyLevel.LOW and score <= 0.5:
            return 'reduce'
        else:
            return 'maintain'
    
    def _calculate_routing_confidence(self, routing_decision: RoutingDecision, 
                                    ranked_departments: List[Tuple[DepartmentProfile, float]]) -> float:
        """Calculate confidence score for routing decision."""
        if not ranked_departments:
            return 0.3
        
        best_score = routing_decision.confidence_score
        
        # Check score gap to next best option
        if len(ranked_departments) > 1:
            second_best_score = ranked_departments[1][1]
            score_gap = best_score - second_best_score
        else:
            score_gap = 0.0
        
        # Confidence based on score and gap
        if best_score >= 0.8 and score_gap >= 0.2:
            return 0.9
        elif best_score >= 0.6 and score_gap >= 0.1:
            return 0.7
        elif best_score >= 0.5:
            return 0.5
        else:
            return 0.3
    
    def _calculate_workload_impact(self, department_id: str) -> float:
        """Calculate impact of adding report to department workload."""
        dept = self.department_profiles.get(department_id)
        if not dept:
            return 0.0
        
        # Simple impact calculation based on current workload vs staff
        workload_ratio = dept.current_workload / max(dept.active_staff, 1)
        
        if workload_ratio < 1.0:
            return 0.1  # Low impact
        elif workload_ratio < 2.0:
            return 0.3  # Medium impact
        else:
            return 0.6  # High impact
    
    def _record_routing_decision(self, report_data: Dict[str, Any], 
                               routing_decision: RoutingDecision, confidence_score: float):
        """Record routing decision for analysis and improvement."""
        routing_record = {
            'timestamp': datetime.now(),
            'report_id': report_data.get('id', 'unknown'),
            'report_text': report_data.get('text', '')[:100] + '...',
            'primary_department': routing_decision.department_id,
            'confidence_score': confidence_score,
            'urgency': report_data.get('urgency', 'medium'),
            'category': report_data.get('category', 'general'),
            'estimated_response_time': routing_decision.estimated_response_time
        }
        
        self.routing_history.append(routing_record)
        
        # Keep only recent history to prevent memory issues
        if len(self.routing_history) > 1000:
            self.routing_history = self.routing_history[-1000:]
    
    def update_department_performance(self, department_id: str, 
                                    response_time: float, success: bool):
        """Update department performance metrics based on actual results."""
        dept = self.department_profiles.get(department_id)
        if not dept:
            return
        
        # Update average response time (moving average)
        dept.average_response_time = (
            (dept.average_response_time * 9 + response_time) / 10
        )
        
        # Update success rate
        if success:
            dept.success_rate = min((dept.success_rate * 99 + 1) / 100, 1.0)
        else:
            dept.success_rate = max((dept.success_rate * 99) / 100, 0.0)
        
        # Update workload (decrease if successful, increase if failed)
        if success:
            dept.current_workload = max(dept.current_workload - 1, 0)
        else:
            dept.current_workload += 1
    
    def get_department_analytics(self) -> Dict[str, Any]:
        """Get analytics data for department performance."""
        analytics = {
            'department_performance': {},
            'routing_statistics': {
                'total_routes': len(self.routing_history),
                'recent_routes': len(self.routing_history[-100:]) if self.routing_history else 0
            }
        }
        
        for dept_id, dept in self.department_profiles.items():
            analytics['department_performance'][dept_id] = {
                'name': dept.name,
                'current_workload': dept.current_workload,
                'average_response_time': dept.average_response_time,
                'success_rate': dept.success_rate,
                'active_staff': dept.active_staff,
                'escalation_level': dept.escalation_level
            }
        
        return analytics