"""
Float (Slack) Analysis Plugin for ARGO
Analyzes total float and free float in project schedules

Float (also called slack) represents the amount of time an activity can be delayed
without impacting the project completion date (total float) or without delaying
any successor activities (free float).

Key Analyses:
1. Total Float distribution across activities
2. Free Float identification
3. Float consumption tracking
4. Negative float (behind schedule) identification
5. Float trend analysis
6. Schedule risk assessment based on float margins
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import time
from datetime import datetime

try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from core.plugins import (
    Plugin,
    BaseAnalyzer,
    AnalysisResult,
    PluginMetadata,
    PluginCapability
)

logger = logging.getLogger(__name__)


class FloatAnalyzer(BaseAnalyzer):
    """
    Float/Slack Analysis Analyzer

    Analyzes schedule float to identify:
    - Activities with negative float (behind schedule)
    - Activities with high float (potential slack)
    - Float consumption patterns
    - Schedule risk indicators
    """

    def __init__(self, system=None, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.system = system

    @property
    def name(self) -> str:
        return "float_analyzer"

    @property
    def supported_formats(self) -> List[str]:
        return ['.xer', '.xml', '.json']

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Float and slack analysis for schedule risk assessment"

    def validate(self, file_path: str) -> tuple[bool, Optional[str]]:
        """Validate input"""
        is_valid, error = super().validate(file_path)
        if not is_valid:
            return False, error

        if not HAS_PANDAS:
            return False, "pandas not installed"

        return True, None

    def analyze(self, file_path: str, options: Optional[Dict] = None) -> AnalysisResult:
        """
        Perform Float Analysis

        Options:
            - activities_df: DataFrame with activities (required)
            - high_float_threshold: Days for "high float" (default: 44)
            - near_critical_threshold: Days for "near critical" (default: 5)
        """
        start_time = time.time()

        try:
            logger.info(f"Starting Float Analysis: {Path(file_path).name}")

            options = options or {}
            activities_df = options.get('activities_df')

            if activities_df is None:
                return AnalysisResult(
                    status='error',
                    data={},
                    errors=["activities_df required in options"]
                )

            # Check for required float columns
            if 'total_float_days' not in activities_df.columns and 'total_float_cpm' not in activities_df.columns:
                return AnalysisResult(
                    status='error',
                    data={},
                    errors=["Float data not available. Run CPM analysis first."]
                )

            # Use CPM float if available, otherwise use existing float
            float_col = 'total_float_cpm' if 'total_float_cpm' in activities_df.columns else 'total_float_days'
            free_float_col = 'free_float_cpm' if 'free_float_cpm' in activities_df.columns else 'free_float_days'

            # Thresholds
            high_float_threshold = options.get('high_float_threshold', 44)
            near_critical_threshold = options.get('near_critical_threshold', 5)

            # Perform analyses
            distribution = self._analyze_float_distribution(activities_df, float_col, high_float_threshold)
            negative_float_analysis = self._analyze_negative_float(activities_df, float_col)
            near_critical_analysis = self._analyze_near_critical(activities_df, float_col, near_critical_threshold)
            free_float_analysis = self._analyze_free_float(activities_df, free_float_col)
            risk_assessment = self._assess_schedule_risk(activities_df, float_col)

            execution_time = (time.time() - start_time) * 1000

            logger.info(f"✓ Float Analysis complete")

            return AnalysisResult(
                status='success',
                data={
                    'distribution': distribution,
                    'negative_float': negative_float_analysis,
                    'near_critical': near_critical_analysis,
                    'free_float': free_float_analysis,
                    'risk_assessment': risk_assessment
                },
                metadata={
                    'analyzer': self.name,
                    'version': self.version,
                    'schedule_file': str(Path(file_path).name),
                    'total_activities': len(activities_df),
                    'high_float_threshold': high_float_threshold,
                    'near_critical_threshold': near_critical_threshold
                },
                execution_time_ms=execution_time
            )

        except Exception as e:
            logger.error(f"Float Analysis failed: {e}", exc_info=True)
            return AnalysisResult(
                status='error',
                data={},
                errors=[f"Float analysis failed: {str(e)}"],
                execution_time_ms=(time.time() - start_time) * 1000
            )

    # ==================== ANALYSIS METHODS ====================

    def _analyze_float_distribution(
        self,
        activities_df: pd.DataFrame,
        float_col: str,
        high_threshold: float
    ) -> Dict:
        """Analyze overall float distribution"""
        try:
            active = activities_df[activities_df['status'] != 'TK_Complete'].copy()

            if len(active) == 0:
                return {'message': 'No active activities to analyze'}

            float_series = active[float_col].dropna()

            # Categorize by float ranges
            negative = active[active[float_col] < 0]
            zero_to_5 = active[(active[float_col] >= 0) & (active[float_col] <= 5)]
            five_to_15 = active[(active[float_col] > 5) & (active[float_col] <= 15)]
            fifteen_to_44 = active[(active[float_col] > 15) & (active[float_col] <= 44)]
            over_44 = active[active[float_col] > high_threshold]

            return {
                'total_active_activities': len(active),
                'statistics': {
                    'mean_float': float(float_series.mean()),
                    'median_float': float(float_series.median()),
                    'std_dev': float(float_series.std()),
                    'min_float': float(float_series.min()),
                    'max_float': float(float_series.max())
                },
                'distribution_by_range': {
                    'negative_float': {
                        'count': len(negative),
                        'percentage': len(negative) / len(active) * 100
                    },
                    '0_to_5_days': {
                        'count': len(zero_to_5),
                        'percentage': len(zero_to_5) / len(active) * 100
                    },
                    '6_to_15_days': {
                        'count': len(five_to_15),
                        'percentage': len(five_to_15) / len(active) * 100
                    },
                    '16_to_44_days': {
                        'count': len(fifteen_to_44),
                        'percentage': len(fifteen_to_44) / len(active) * 100
                    },
                    'over_44_days': {
                        'count': len(over_44),
                        'percentage': len(over_44) / len(active) * 100
                    }
                }
            }

        except Exception as e:
            logger.error(f"Float distribution analysis failed: {e}")
            return {'error': str(e)}

    def _analyze_negative_float(
        self,
        activities_df: pd.DataFrame,
        float_col: str
    ) -> Dict:
        """Analyze activities with negative float (behind schedule)"""
        try:
            active = activities_df[activities_df['status'] != 'TK_Complete']
            negative_float = active[active[float_col] < 0].copy()

            if len(negative_float) == 0:
                return {
                    'status': 'healthy',
                    'count': 0,
                    'message': 'No activities with negative float',
                    'activities': []
                }

            # Sort by most negative first
            negative_float = negative_float.sort_values(float_col)

            activities_list = []
            for _, activity in negative_float.head(20).iterrows():  # Top 20 worst
                activities_list.append({
                    'activity_id': activity['activity_id'],
                    'activity_name': activity.get('activity_name', ''),
                    'total_float': float(activity[float_col]),
                    'duration': activity.get('duration_days', 0),
                    'percent_complete': activity.get('percent_complete', 0)
                })

            return {
                'status': 'critical',
                'count': len(negative_float),
                'total_days_behind': abs(float(negative_float[float_col].sum())),
                'most_negative_float': float(negative_float[float_col].min()),
                'activities': activities_list,
                'message': f'{len(negative_float)} activities behind schedule (negative float)'
            }

        except Exception as e:
            logger.error(f"Negative float analysis failed: {e}")
            return {'error': str(e)}

    def _analyze_near_critical(
        self,
        activities_df: pd.DataFrame,
        float_col: str,
        threshold: float
    ) -> Dict:
        """Analyze near-critical activities (low positive float)"""
        try:
            active = activities_df[activities_df['status'] != 'TK_Complete']
            near_critical = active[
                (active[float_col] > 0) &
                (active[float_col] <= threshold)
            ].copy()

            if len(near_critical) == 0:
                return {
                    'count': 0,
                    'message': f'No near-critical activities (<= {threshold} days float)',
                    'activities': []
                }

            # Sort by float (lowest first)
            near_critical = near_critical.sort_values(float_col)

            activities_list = []
            for _, activity in near_critical.head(20).iterrows():
                activities_list.append({
                    'activity_id': activity['activity_id'],
                    'activity_name': activity.get('activity_name', ''),
                    'total_float': float(activity[float_col]),
                    'duration': activity.get('duration_days', 0),
                    'percent_complete': activity.get('percent_complete', 0)
                })

            return {
                'count': len(near_critical),
                'percentage_of_active': len(near_critical) / len(active) * 100 if len(active) > 0 else 0,
                'threshold_days': threshold,
                'activities': activities_list,
                'message': f'{len(near_critical)} near-critical activities (high risk of becoming critical)'
            }

        except Exception as e:
            logger.error(f"Near-critical analysis failed: {e}")
            return {'error': str(e)}

    def _analyze_free_float(
        self,
        activities_df: pd.DataFrame,
        free_float_col: str
    ) -> Dict:
        """Analyze free float (slack before affecting successors)"""
        try:
            if free_float_col not in activities_df.columns:
                return {
                    'available': False,
                    'message': 'Free float data not available'
                }

            active = activities_df[activities_df['status'] != 'TK_Complete']

            with_free_float = active[active[free_float_col] > 0]

            return {
                'available': True,
                'total_activities': len(active),
                'activities_with_free_float': len(with_free_float),
                'percentage_with_free_float': len(with_free_float) / len(active) * 100 if len(active) > 0 else 0,
                'average_free_float': float(with_free_float[free_float_col].mean()) if len(with_free_float) > 0 else 0,
                'max_free_float': float(active[free_float_col].max())
            }

        except Exception as e:
            logger.error(f"Free float analysis failed: {e}")
            return {'error': str(e)}

    def _assess_schedule_risk(
        self,
        activities_df: pd.DataFrame,
        float_col: str
    ) -> Dict:
        """Assess overall schedule risk based on float margins"""
        try:
            active = activities_df[activities_df['status'] != 'TK_Complete']

            if len(active) == 0:
                return {'risk_level': 'unknown', 'message': 'No active activities'}

            # Calculate risk indicators
            negative_count = len(active[active[float_col] < 0])
            near_critical_count = len(active[(active[float_col] >= 0) & (active[float_col] <= 5)])
            avg_float = float(active[float_col].mean())

            # Risk scoring
            risk_score = 0

            # Negative float is critical
            if negative_count > 0:
                negative_ratio = negative_count / len(active)
                risk_score += negative_ratio * 100  # Up to 100 points

            # Near-critical activities indicate risk
            if near_critical_count > 0:
                near_critical_ratio = near_critical_count / len(active)
                risk_score += near_critical_ratio * 50  # Up to 50 points

            # Low average float indicates risk
            if avg_float < 10:
                risk_score += (10 - avg_float) * 2  # Up to 20 points

            # Determine risk level
            if risk_score >= 60:
                risk_level = 'high'
                risk_color = 'red'
                recommendation = 'URGENT: Schedule is severely constrained. Immediate action required.'
            elif risk_score >= 30:
                risk_level = 'medium'
                risk_color = 'yellow'
                recommendation = 'CAUTION: Schedule has limited flexibility. Monitor closely.'
            else:
                risk_level = 'low'
                risk_color = 'green'
                recommendation = 'Schedule has adequate float margins.'

            return {
                'risk_level': risk_level,
                'risk_score': risk_score,
                'risk_color': risk_color,
                'recommendation': recommendation,
                'indicators': {
                    'negative_float_activities': negative_count,
                    'near_critical_activities': near_critical_count,
                    'average_float_days': avg_float
                }
            }

        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return {'error': str(e)}


# Plugin registration
class FloatAnalysisPlugin(Plugin):
    """Float/Slack Analysis Plugin"""

    metadata = PluginMetadata(
        name="float_analyzer",
        version="1.0.0",
        description="Float and slack analysis for schedule risk assessment",
        author="ARGO Development Team",
        capabilities=[PluginCapability.ANALYZER]
    )

    def initialize(self, system):
        """Initialize plugin"""
        self.analyzer = FloatAnalyzer(system=system)
        if hasattr(system, 'plugin_manager'):
            system.plugin_manager.register_analyzer(self.analyzer)
        logger.info("✅ Float Analysis Plugin initialized")
