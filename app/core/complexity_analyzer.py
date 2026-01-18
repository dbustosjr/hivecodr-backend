"""Requirement complexity analyzer for intelligent generation planning."""

from typing import Dict, Any, List
import re


class ComplexityAnalyzer:
    """Analyzes requirement complexity and provides generation strategies."""

    # Keywords indicating complexity
    COMPLEX_KEYWORDS = [
        'multiple', 'many', 'various', 'several', 'complex',
        'advanced', 'sophisticated', 'comprehensive', 'detailed'
    ]

    RELATIONSHIP_KEYWORDS = [
        'relationship', 'related', 'linked', 'connected', 'belongs to',
        'has many', 'many to many', 'one to many', 'foreign key'
    ]

    FEATURE_KEYWORDS = [
        'search', 'filter', 'pagination', 'sort', 'export',
        'chart', 'graph', 'analytics', 'dashboard', 'report',
        'notification', 'email', 'authentication', 'authorization'
    ]

    def __init__(self):
        """Initialize the complexity analyzer."""
        pass

    def analyze(self, requirements: str) -> Dict[str, Any]:
        """
        Analyze requirement complexity and return generation strategy.

        Args:
            requirements: Plain English requirements

        Returns:
            Dict containing:
            - complexity_score: int (0-100)
            - complexity_level: str (simple/moderate/complex)
            - model_count_estimate: int
            - has_relationships: bool
            - has_advanced_features: bool
            - generation_strategy: str (single_phase/progressive)
            - core_features: List[str]
            - advanced_features: List[str]
            - simplification_suggestions: List[str]
        """
        requirements_lower = requirements.lower()

        # Count indicators
        complexity_indicators = sum(
            1 for keyword in self.COMPLEX_KEYWORDS
            if keyword in requirements_lower
        )

        relationship_indicators = sum(
            1 for keyword in self.RELATIONSHIP_KEYWORDS
            if keyword in requirements_lower
        )

        feature_indicators = sum(
            1 for keyword in self.FEATURE_KEYWORDS
            if keyword in requirements_lower
        )

        # Estimate model count (count nouns that might be entities)
        model_estimate = self._estimate_model_count(requirements)

        # Calculate complexity score (0-100)
        complexity_score = min(100, (
            complexity_indicators * 10 +
            relationship_indicators * 15 +
            feature_indicators * 8 +
            model_estimate * 12 +
            len(requirements.split()) * 0.1
        ))

        # Determine complexity level
        if complexity_score < 30:
            complexity_level = "simple"
            generation_strategy = "single_phase"
        elif complexity_score < 60:
            complexity_level = "moderate"
            generation_strategy = "single_phase"
        else:
            complexity_level = "complex"
            generation_strategy = "progressive"

        # Extract features
        core_features, advanced_features = self._categorize_features(requirements)

        # Generate simplification suggestions
        simplification_suggestions = self._generate_simplifications(
            requirements, complexity_level, advanced_features
        )

        return {
            "complexity_score": int(complexity_score),
            "complexity_level": complexity_level,
            "model_count_estimate": model_estimate,
            "has_relationships": relationship_indicators > 0,
            "has_advanced_features": feature_indicators > 2,
            "generation_strategy": generation_strategy,
            "core_features": core_features,
            "advanced_features": advanced_features,
            "simplification_suggestions": simplification_suggestions,
            "word_count": len(requirements.split())
        }

    def _estimate_model_count(self, requirements: str) -> int:
        """Estimate number of database models needed."""
        # Common entity indicators
        entity_patterns = [
            r'\b(user|users)\b',
            r'\b(post|posts|article|articles)\b',
            r'\b(comment|comments)\b',
            r'\b(product|products)\b',
            r'\b(order|orders)\b',
            r'\b(category|categories)\b',
            r'\b(workout|workouts)\b',
            r'\b(exercise|exercises)\b',
            r'\b(session|sessions)\b',
            r'\b(goal|goals)\b',
            r'\b(achievement|achievements)\b',
            r'\b(routine|routines)\b',
            r'\b(set|sets)\b',
            r'\b(rep|reps)\b',
            r'\b(progress|tracking)\b'
        ]

        requirements_lower = requirements.lower()
        model_count = 0

        for pattern in entity_patterns:
            if re.search(pattern, requirements_lower):
                model_count += 1

        return max(1, model_count)

    def _categorize_features(self, requirements: str) -> tuple:
        """Categorize features into core and advanced."""
        requirements_lower = requirements.lower()

        # Core features are always needed
        core_features = []
        if 'create' in requirements_lower or 'add' in requirements_lower:
            core_features.append("Create operations")
        if 'read' in requirements_lower or 'view' in requirements_lower or 'list' in requirements_lower:
            core_features.append("Read operations")
        if 'update' in requirements_lower or 'edit' in requirements_lower or 'modify' in requirements_lower:
            core_features.append("Update operations")
        if 'delete' in requirements_lower or 'remove' in requirements_lower:
            core_features.append("Delete operations")

        # Default to full CRUD if no specific operations mentioned
        if not core_features:
            core_features = ["Full CRUD operations"]

        # Advanced features are optional enhancements
        advanced_features = []
        if 'search' in requirements_lower:
            advanced_features.append("Search functionality")
        if 'filter' in requirements_lower:
            advanced_features.append("Filtering")
        if 'pagination' in requirements_lower or 'page' in requirements_lower:
            advanced_features.append("Pagination")
        if 'sort' in requirements_lower:
            advanced_features.append("Sorting")
        if 'chart' in requirements_lower or 'graph' in requirements_lower or 'analytics' in requirements_lower:
            advanced_features.append("Charts and analytics")
        if 'export' in requirements_lower:
            advanced_features.append("Data export")
        if 'notification' in requirements_lower:
            advanced_features.append("Notifications")
        if 'email' in requirements_lower:
            advanced_features.append("Email integration")

        return core_features, advanced_features

    def _generate_simplifications(
        self,
        requirements: str,
        complexity_level: str,
        advanced_features: List[str]
    ) -> List[str]:
        """Generate suggestions for simplifying requirements."""
        suggestions = []

        if complexity_level == "complex":
            suggestions.append("Focus on core CRUD operations first")

            if advanced_features:
                suggestions.append(
                    f"Remove advanced features: {', '.join(advanced_features[:3])}"
                )

            if "chart" in requirements.lower() or "graph" in requirements.lower():
                suggestions.append("Defer charts/analytics to Phase 2")

            if "notification" in requirements.lower() or "email" in requirements.lower():
                suggestions.append("Defer notifications/emails to Phase 2")

            suggestions.append("Reduce number of models by focusing on main entities")
            suggestions.append("Simplify relationships (start with one-to-many only)")

        elif complexity_level == "moderate":
            if len(advanced_features) > 3:
                suggestions.append("Consider implementing advanced features in Phase 2")

        return suggestions

    def create_simplified_requirements(
        self,
        original_requirements: str,
        simplification_level: int = 1
    ) -> str:
        """
        Create simplified version of requirements.

        Args:
            original_requirements: Original requirements
            simplification_level: 1 (light), 2 (moderate), 3 (heavy)

        Returns:
            Simplified requirements string
        """
        analysis = self.analyze(original_requirements)

        if simplification_level == 1:
            # Light: Remove advanced features but keep relationships
            if analysis['advanced_features']:
                return f"{original_requirements}\n\nNOTE: Focus on core CRUD operations. Advanced features ({', '.join(analysis['advanced_features'][:2])}) can be added later."
            return original_requirements

        elif simplification_level == 2:
            # Moderate: Core models with basic relationships
            core_features = ', '.join(analysis['core_features'])
            return f"Create a basic application with {analysis['model_count_estimate']} main entities supporting {core_features}. Include basic relationships between entities. Defer advanced features for later implementation."

        else:  # simplification_level == 3
            # Heavy: Minimal CRUD only
            return f"Create a simple CRUD application with {max(2, analysis['model_count_estimate'] - 2)} core entities. Focus on basic Create, Read, Update, Delete operations only. No advanced features."


# Global instance
complexity_analyzer = ComplexityAnalyzer()
