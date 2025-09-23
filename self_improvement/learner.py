"""Self-learning and improvement system for Genesis AI Agent."""

import json
import pickle
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter

from core.config import Config
from utils.logger import get_logger


@dataclass
class LearningEntry:
    """Represents a learning entry in the system."""
    timestamp: str
    entry_type: str  # 'analysis', 'suggestion', 'implementation', 'feedback'
    context: Dict[str, Any]
    outcome: Optional[str] = None
    confidence: float = 0.5
    user_rating: Optional[int] = None  # 1-5 scale


@dataclass
class PatternMatch:
    """Represents a discovered pattern."""
    pattern_type: str
    frequency: int
    success_rate: float
    contexts: List[Dict[str, Any]]
    last_seen: str


class SelfLearner:
    """Handles self-improvement and learning from interactions."""
    
    def __init__(self, config: Config):
        """Initialize the self-learning system."""
        self.config = config
        self.logger = get_logger(__name__)
        
        self.feedback_storage_path = Path(config.feedback_storage_path)
        self.model_weights_path = Path(config.model_weights_path)
        
        # Ensure storage directories exist
        self.feedback_storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.model_weights_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Learning data
        self.learning_entries: List[LearningEntry] = []
        self.patterns: Dict[str, PatternMatch] = {}
        self.success_metrics: Dict[str, float] = defaultdict(float)
        
        # Load existing data
        self._load_learning_data()
        
        self.logger.info("Self-learning system initialized")
    
    async def learn_from_analysis(self, path: str, results: List[str]) -> None:
        """Learn from code analysis results."""
        if not self.config.learning_enabled:
            return
        
        entry = LearningEntry(
            timestamp=datetime.now().isoformat(),
            entry_type='analysis',
            context={
                'path': path,
                'results_count': len(results),
                'results': results[:10],  # Store first 10 results
                'file_types': self._extract_file_types(path),
            }
        )
        
        self.learning_entries.append(entry)
        await self._analyze_patterns(entry)
        await self._save_learning_data()
        
        self.logger.debug(f"Learned from analysis of {path}")
    
    async def learn_from_suggestions(self, suggestions: List[str]) -> None:
        """Learn from generated suggestions."""
        if not self.config.learning_enabled:
            return
        
        entry = LearningEntry(
            timestamp=datetime.now().isoformat(),
            entry_type='suggestion',
            context={
                'suggestions_count': len(suggestions),
                'suggestions': suggestions[:5],  # Store first 5 suggestions
                'suggestion_types': self._categorize_suggestions(suggestions),
            }
        )
        
        self.learning_entries.append(entry)
        await self._analyze_patterns(entry)
        await self._save_learning_data()
        
        self.logger.debug(f"Learned from {len(suggestions)} suggestions")
    
    async def learn_from_implementation(self, suggestion: Dict[str, Any], 
                                       result: str) -> None:
        """Learn from implementation results."""
        if not self.config.learning_enabled:
            return
        
        # Determine if implementation was successful
        success = 'error' not in result.lower() and 'failed' not in result.lower()
        
        entry = LearningEntry(
            timestamp=datetime.now().isoformat(),
            entry_type='implementation',
            context={
                'suggestion_type': suggestion.get('type'),
                'file_path': suggestion.get('file_path'),
                'confidence': suggestion.get('confidence', 0.5),
                'success': success,
            },
            outcome=result,
            confidence=suggestion.get('confidence', 0.5)
        )
        
        self.learning_entries.append(entry)
        
        # Update success metrics
        suggestion_type = suggestion.get('type', 'unknown')
        self._update_success_metrics(suggestion_type, success)
        
        await self._analyze_patterns(entry)
        await self._save_learning_data()
        
        self.logger.debug(f"Learned from implementation: {result}")
    
    async def learn_from_feedback(self, feedback: str, rating: Optional[int] = None) -> None:
        """Learn from user feedback."""
        if not self.config.learning_enabled:
            return
        
        entry = LearningEntry(
            timestamp=datetime.now().isoformat(),
            entry_type='feedback',
            context={
                'feedback': feedback,
                'sentiment': self._analyze_sentiment(feedback),
                'keywords': self._extract_keywords(feedback),
            },
            user_rating=rating
        )
        
        self.learning_entries.append(entry)
        await self._analyze_patterns(entry)
        await self._save_learning_data()
        
        self.logger.info(f"Learned from user feedback: {feedback[:50]}...")
    
    async def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from learning data."""
        total_entries = len(self.learning_entries)
        
        if total_entries == 0:
            return {'message': 'No learning data available yet'}
        
        # Calculate time-based statistics
        recent_entries = [
            entry for entry in self.learning_entries
            if self._is_recent(entry.timestamp, days=7)
        ]
        
        # Entry type distribution
        type_distribution = Counter(entry.entry_type for entry in self.learning_entries)
        
        # Success rate analysis
        success_analysis = self._calculate_success_rates()
        
        # Pattern analysis
        pattern_summary = {
            pattern_type: {
                'frequency': pattern.frequency,
                'success_rate': pattern.success_rate,
                'last_seen': pattern.last_seen
            }
            for pattern_type, pattern in self.patterns.items()
        }
        
        return {
            'total_entries': total_entries,
            'recent_entries': len(recent_entries),
            'entry_types': dict(type_distribution),
            'success_rates': success_analysis,
            'patterns': pattern_summary,
            'recommendations': await self._generate_recommendations(),
        }
    
    async def get_personalized_suggestions(self, context: Dict[str, Any]) -> List[str]:
        """Get personalized suggestions based on learning history."""
        suggestions = []
        
        # Find similar contexts from learning history
        similar_contexts = self._find_similar_contexts(context)
        
        # Generate suggestions based on successful patterns
        for ctx in similar_contexts:
            if ctx.get('success', False):
                suggestion_type = ctx.get('suggestion_type')
                if suggestion_type and suggestion_type in self.success_metrics:
                    if self.success_metrics[suggestion_type] > 0.7:
                        suggestions.append(f"Consider {suggestion_type} based on past success")
        
        # Add pattern-based suggestions
        for pattern_type, pattern in self.patterns.items():
            if pattern.success_rate > 0.8 and pattern.frequency > 3:
                suggestions.append(f"Apply {pattern_type} pattern (success rate: {pattern.success_rate:.1%})")
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _load_learning_data(self) -> None:
        """Load learning data from storage."""
        try:
            if self.feedback_storage_path.exists():
                with open(self.feedback_storage_path, 'r') as f:
                    data = json.load(f)
                    
                    self.learning_entries = [
                        LearningEntry(**entry) for entry in data.get('entries', [])
                    ]
                    self.success_metrics = defaultdict(float, data.get('success_metrics', {}))
            
            if self.model_weights_path.exists():
                with open(self.model_weights_path, 'rb') as f:
                    patterns_data = pickle.load(f)
                    self.patterns = {
                        k: PatternMatch(**v) for k, v in patterns_data.items()
                    }
            
            self.logger.info(f"Loaded {len(self.learning_entries)} learning entries")
            
        except Exception as e:
            self.logger.error(f"Error loading learning data: {e}")
    
    async def _save_learning_data(self) -> None:
        """Save learning data to storage."""
        try:
            # Save learning entries and metrics
            data = {
                'entries': [asdict(entry) for entry in self.learning_entries],
                'success_metrics': dict(self.success_metrics),
                'last_updated': datetime.now().isoformat(),
            }
            
            with open(self.feedback_storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Save patterns
            patterns_data = {
                k: asdict(v) for k, v in self.patterns.items()
            }
            
            with open(self.model_weights_path, 'wb') as f:
                pickle.dump(patterns_data, f)
            
        except Exception as e:
            self.logger.error(f"Error saving learning data: {e}")
    
    async def _analyze_patterns(self, entry: LearningEntry) -> None:
        """Analyze patterns in the new learning entry."""
        # Extract potential patterns based on entry type
        if entry.entry_type == 'analysis':
            await self._analyze_analysis_patterns(entry)
        elif entry.entry_type == 'suggestion':
            await self._analyze_suggestion_patterns(entry)
        elif entry.entry_type == 'implementation':
            await self._analyze_implementation_patterns(entry)
        elif entry.entry_type == 'feedback':
            await self._analyze_feedback_patterns(entry)
    
    async def _analyze_analysis_patterns(self, entry: LearningEntry) -> None:
        """Analyze patterns in code analysis."""
        file_types = entry.context.get('file_types', [])
        results_count = entry.context.get('results_count', 0)
        
        for file_type in file_types:
            pattern_key = f"analysis_{file_type}"
            self._update_pattern(pattern_key, entry.context, results_count > 0)
    
    async def _analyze_suggestion_patterns(self, entry: LearningEntry) -> None:
        """Analyze patterns in suggestions."""
        suggestion_types = entry.context.get('suggestion_types', [])
        
        for suggestion_type in suggestion_types:
            pattern_key = f"suggestion_{suggestion_type}"
            self._update_pattern(pattern_key, entry.context, True)
    
    async def _analyze_implementation_patterns(self, entry: LearningEntry) -> None:
        """Analyze patterns in implementations."""
        suggestion_type = entry.context.get('suggestion_type')
        success = entry.context.get('success', False)
        
        if suggestion_type:
            pattern_key = f"implementation_{suggestion_type}"
            self._update_pattern(pattern_key, entry.context, success)
    
    async def _analyze_feedback_patterns(self, entry: LearningEntry) -> None:
        """Analyze patterns in user feedback."""
        sentiment = entry.context.get('sentiment', 'neutral')
        keywords = entry.context.get('keywords', [])
        
        pattern_key = f"feedback_{sentiment}"
        self._update_pattern(pattern_key, entry.context, sentiment == 'positive')
        
        for keyword in keywords:
            keyword_pattern = f"keyword_{keyword}"
            self._update_pattern(keyword_pattern, entry.context, sentiment == 'positive')
    
    def _update_pattern(self, pattern_key: str, context: Dict[str, Any], success: bool) -> None:
        """Update or create a pattern."""
        if pattern_key in self.patterns:
            pattern = self.patterns[pattern_key]
            pattern.frequency += 1
            pattern.contexts.append(context)
            
            # Update success rate
            total_success = pattern.success_rate * (pattern.frequency - 1) + (1 if success else 0)
            pattern.success_rate = total_success / pattern.frequency
            
            pattern.last_seen = datetime.now().isoformat()
        else:
            self.patterns[pattern_key] = PatternMatch(
                pattern_type=pattern_key,
                frequency=1,
                success_rate=1.0 if success else 0.0,
                contexts=[context],
                last_seen=datetime.now().isoformat()
            )
    
    def _update_success_metrics(self, suggestion_type: str, success: bool) -> None:
        """Update success metrics for a suggestion type."""
        current_value = self.success_metrics[suggestion_type]
        # Simple moving average update
        self.success_metrics[suggestion_type] = current_value * 0.9 + (1.0 if success else 0.0) * 0.1
    
    def _extract_file_types(self, path: str) -> List[str]:
        """Extract file types from a path."""
        path_obj = Path(path)
        
        if path_obj.is_file():
            return [path_obj.suffix[1:]] if path_obj.suffix else ['unknown']
        
        file_types = set()
        for file_path in path_obj.rglob('*'):
            if file_path.is_file() and file_path.suffix:
                file_types.add(file_path.suffix[1:])
        
        return list(file_types)
    
    def _categorize_suggestions(self, suggestions: List[str]) -> List[str]:
        """Categorize suggestions into types."""
        categories = []
        
        for suggestion in suggestions:
            suggestion_lower = suggestion.lower()
            
            if 'docstring' in suggestion_lower:
                categories.append('documentation')
            elif 'style' in suggestion_lower or 'format' in suggestion_lower:
                categories.append('style')
            elif 'performance' in suggestion_lower or 'optimize' in suggestion_lower:
                categories.append('performance')
            elif 'security' in suggestion_lower:
                categories.append('security')
            elif 'test' in suggestion_lower:
                categories.append('testing')
            else:
                categories.append('general')
        
        return list(set(categories))
    
    def _analyze_sentiment(self, feedback: str) -> str:
        """Analyze sentiment of feedback (simple implementation)."""
        feedback_lower = feedback.lower()
        
        positive_words = ['good', 'great', 'excellent', 'helpful', 'useful', 'perfect', 'amazing']
        negative_words = ['bad', 'terrible', 'wrong', 'useless', 'horrible', 'awful', 'broken']
        
        positive_count = sum(1 for word in positive_words if word in feedback_lower)
        negative_count = sum(1 for word in negative_words if word in feedback_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _extract_keywords(self, feedback: str) -> List[str]:
        """Extract keywords from feedback."""
        # Simple keyword extraction
        import re
        
        words = re.findall(r'\b\w+\b', feedback.lower())
        
        # Filter common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'this', 'that',
            'these', 'those'
        }

        keywords = [word for word in words if word not in stop_words and len(word) > 3]

        return list(set(keywords))
    
    def _is_recent(self, timestamp: str, days: int = 7) -> bool:
        """Check if a timestamp is within the last N days."""
        try:
            entry_time = datetime.fromisoformat(timestamp)
            cutoff_time = datetime.now() - timedelta(days=days)
            return entry_time > cutoff_time
        except:
            return False
    
    def _calculate_success_rates(self) -> Dict[str, float]:
        """Calculate success rates for different types of operations."""
        success_rates = {}
        
        implementation_entries = [
            entry for entry in self.learning_entries
            if entry.entry_type == 'implementation'
        ]
        
        if implementation_entries:
            success_count = sum(
                1 for entry in implementation_entries
                if entry.context.get('success', False)
            )
            success_rates['implementation'] = success_count / len(implementation_entries)
        
        return success_rates
    
    def _find_similar_contexts(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar contexts from learning history."""
        similar_contexts = []
        
        for entry in self.learning_entries:
            if entry.entry_type == 'implementation':
                entry_context = entry.context
                
                # Simple similarity based on shared keys
                shared_keys = set(context.keys()) & set(entry_context.keys())
                if len(shared_keys) > 0:
                    similarity = len(shared_keys) / max(len(context), len(entry_context))
                    if similarity > 0.5:
                        similar_contexts.append(entry_context)
        
        return similar_contexts
    
    async def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on learning data."""
        recommendations = []
        
        # Analyze most successful patterns
        successful_patterns = [
            (pattern_type, pattern) for pattern_type, pattern in self.patterns.items()
            if pattern.success_rate > 0.8 and pattern.frequency > 2
        ]
        
        if successful_patterns:
            recommendations.append(
                f"Focus on {len(successful_patterns)} high-success patterns identified"
            )
        
        # Analyze areas for improvement
        low_success_patterns = [
            pattern_type for pattern_type, pattern in self.patterns.items()
            if pattern.success_rate < 0.5 and pattern.frequency > 2
        ]
        
        if low_success_patterns:
            recommendations.append(
                f"Review and improve {len(low_success_patterns)} low-success patterns"
            )
        
        # Feedback analysis
        feedback_entries = [
            entry for entry in self.learning_entries
            if entry.entry_type == 'feedback'
        ]
        
        if feedback_entries:
            positive_feedback = sum(
                1 for entry in feedback_entries
                if entry.context.get('sentiment') == 'positive'
            )
            feedback_ratio = positive_feedback / len(feedback_entries)
            
            if feedback_ratio < 0.7:
                recommendations.append("Focus on improving user satisfaction based on feedback")
        
        return recommendations if recommendations else ["Continue learning from interactions"]