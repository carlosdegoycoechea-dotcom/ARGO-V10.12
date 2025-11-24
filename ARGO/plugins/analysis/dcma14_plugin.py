"""
DCMA 14-Point Assessment Plugin for ARGO
Implements the Defense Contract Management Agency's 14-Point Schedule Assessment

This plugin evaluates schedule quality based on DCMA standards:
1. Logic: Activities are logically linked
2. Leads: Inappropriate use of lead time
3. Lags: Excessive use of lag time
4. Relationship Types: Proper use of FS/SS/SF/FF
5. Hard Constraints: Minimal use of constraints
6. High Float: Activities with excessive float
7. Negative Float: Behind schedule activities
8. High Duration: Overly long activities
9. Invalid Dates: Date logic errors
10. Resources: Proper resource loading
11. Missed Tasks: Tasks that should have started
12. Critical Path Test: Valid critical path
13. Critical Path Length Index: Ratio analysis
14. Baseline: Existence of performance baseline

Each point is scored as Pass/Fail based on DCMA thresholds.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import time
from datetime import datetime, timedelta

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


class DCMA14Analyzer(BaseAnalyzer):
    """
    DCMA 14-Point Schedule Assessment Analyzer

    Evaluates schedule quality against DCMA standards.
    Provides pass/fail scoring and detailed findings for each metric.

    DCMA Thresholds:
    - Logic: >95% of activities linked
    - Leads: <5% of relationships with leads
    - Lags: <5% of relationships with lags >10 days
    - Hard Constraints: <5% of activities with hard constraints
    - High Float: <5% of activities with >44 working days float
    - Negative Float: 0 activities with negative float
    - High Duration: <5% of activities >44 working days
    - Missed Tasks: 0 tasks that should have started
    - Critical Path Length Index: 0.90 to 1.10
    """

    def __init__(self, system=None, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.system = system

        # DCMA Thresholds (configurable)
        self.thresholds = {
            'logic_threshold': self.config.get('logic_threshold', 0.95),  # 95%
            'lead_threshold': self.config.get('lead_threshold', 0.05),    # 5%
            'lag_threshold': self.config.get('lag_threshold', 0.05),      # 5%
            'lag_days_threshold': self.config.get('lag_days_threshold', 10),
            'constraint_threshold': self.config.get('constraint_threshold', 0.05),
            'float_high_threshold': self.config.get('float_high_threshold', 44),  # days
            'float_high_percent': self.config.get('float_high_percent', 0.05),
            'negative_float_threshold': self.config.get('negative_float_threshold', 0),
            'duration_high_threshold': self.config.get('duration_high_threshold', 44),
            'duration_high_percent': self.config.get('duration_high_percent', 0.05),
            'cpli_min': self.config.get('cpli_min', 0.90),
            'cpli_max': self.config.get('cpli_max', 1.10),
        }

    @property
    def name(self) -> str:
        return "dcma14_analyzer"

    @property
    def supported_formats(self) -> List[str]:
        return ['.xer', '.xml', '.json']  # Can analyze parsed schedule data

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "DCMA 14-Point Schedule Quality Assessment"

    def validate(self, file_path: str) -> tuple[bool, Optional[str]]:
        """Validate input for DCMA analysis"""
        is_valid, error = super().validate(file_path)

        if not is_valid:
            return False, error

        if not HAS_PANDAS:
            return False, "pandas not installed"

        return True, None

    def analyze(self, file_path: str, options: Optional[Dict] = None) -> AnalysisResult:
        """
        Perform DCMA 14-Point Assessment on schedule data

        Options:
            - activities_df: DataFrame with activities (if already parsed)
            - relationships_df: DataFrame with relationships
            - strict_mode: Use stricter thresholds (default: False)
        """
        start_time = time.time()

        try:
            logger.info(f"Starting DCMA 14-Point Assessment: {Path(file_path).name}")

            options = options or {}

            # Get parsed data (either from options or parse the file)
            activities_df = options.get('activities_df')
            relationships_df = options.get('relationships_df')

            if activities_df is None:
                return AnalysisResult(
                    status='error',
                    data={},
                    errors=["activities_df required in options. Parse schedule file first."]
                )

            # Run all 14 assessments
            results = {}

            # 1. Logic
            results['logic'] = self._assess_logic(activities_df, relationships_df)

            # 2. Leads
            results['leads'] = self._assess_leads(relationships_df)

            # 3. Lags
            results['lags'] = self._assess_lags(relationships_df)

            # 4. Relationship Types
            results['relationship_types'] = self._assess_relationship_types(relationships_df)

            # 5. Hard Constraints
            results['hard_constraints'] = self._assess_constraints(activities_df)

            # 6. High Float
            results['high_float'] = self._assess_high_float(activities_df)

            # 7. Negative Float
            results['negative_float'] = self._assess_negative_float(activities_df)

            # 8. High Duration
            results['high_duration'] = self._assess_high_duration(activities_df)

            # 9. Invalid Dates
            results['invalid_dates'] = self._assess_invalid_dates(activities_df)

            # 10. Resources
            results['resources'] = self._assess_resources(activities_df, options)

            # 11. Missed Tasks
            results['missed_tasks'] = self._assess_missed_tasks(activities_df)

            # 12. Critical Path Test
            results['critical_path_test'] = self._assess_critical_path_test(activities_df)

            # 13. Critical Path Length Index (CPLI)
            results['cpli'] = self._assess_cpli(activities_df, options)

            # 14. Baseline
            results['baseline'] = self._assess_baseline(activities_df, options)

            # Calculate overall score
            passed_count = sum(1 for r in results.values() if r['pass'])
            total_count = len(results)
            overall_score = (passed_count / total_count) * 100

            # Generate summary
            summary = {
                'overall_score': overall_score,
                'passed_checks': passed_count,
                'total_checks': total_count,
                'rating': self._get_rating(overall_score),
                'dcma_compliant': passed_count >= 12  # At least 12/14 to pass
            }

            execution_time = (time.time() - start_time) * 1000

            logger.info(f"✓ DCMA Assessment complete: {passed_count}/{total_count} passed ({overall_score:.1f}%)")

            return AnalysisResult(
                status='success',
                data={
                    'summary': summary,
                    'detailed_results': results,
                    'thresholds_used': self.thresholds
                },
                metadata={
                    'analyzer': self.name,
                    'version': self.version,
                    'schedule_file': str(Path(file_path).name),
                    'total_activities': len(activities_df),
                    'assessment_standard': 'DCMA 14-Point'
                },
                execution_time_ms=execution_time
            )

        except Exception as e:
            logger.error(f"DCMA Assessment failed: {e}", exc_info=True)
            return AnalysisResult(
                status='error',
                data={},
                errors=[f"DCMA assessment failed: {str(e)}"],
                execution_time_ms=(time.time() - start_time) * 1000
            )

    # ==================== ASSESSMENT METHODS ====================

    def _assess_logic(self, activities_df: pd.DataFrame, relationships_df: Optional[pd.DataFrame]) -> Dict:
        """1. Logic: Are activities properly linked?"""
        try:
            if relationships_df is None or len(relationships_df) == 0:
                return {
                    'pass': False,
                    'score': 0,
                    'message': 'No relationships found',
                    'details': {}
                }

            # Get active tasks (exclude milestones and completed)
            active_tasks = activities_df[
                (activities_df['status'] != 'TK_Complete') &
                (activities_df.get('task_type', '') != 'Milestone')
            ]

            if len(active_tasks) == 0:
                return {'pass': True, 'score': 100, 'message': 'No active tasks to assess'}

            # Get unique task IDs from relationships
            linked_tasks = set(relationships_df['predecessor_id'].unique()) | set(relationships_df['successor_id'].unique())

            # Count tasks with logic
            tasks_with_logic = active_tasks[active_tasks['activity_id'].isin(linked_tasks)]
            logic_percent = len(tasks_with_logic) / len(active_tasks)

            passed = logic_percent >= self.thresholds['logic_threshold']

            return {
                'pass': passed,
                'score': logic_percent * 100,
                'message': f'{logic_percent*100:.1f}% of activities have logic (threshold: {self.thresholds["logic_threshold"]*100:.0f}%)',
                'details': {
                    'total_active_tasks': len(active_tasks),
                    'tasks_with_logic': len(tasks_with_logic),
                    'tasks_without_logic': len(active_tasks) - len(tasks_with_logic),
                    'threshold': self.thresholds['logic_threshold']
                }
            }
        except Exception as e:
            return {'pass': False, 'score': 0, 'message': f'Error: {str(e)}', 'details': {}}

    def _assess_leads(self, relationships_df: Optional[pd.DataFrame]) -> Dict:
        """2. Leads: Inappropriate use of lead time"""
        try:
            if relationships_df is None or len(relationships_df) == 0:
                return {'pass': True, 'score': 100, 'message': 'No relationships to assess'}

            # Count relationships with negative lag (leads)
            total_rels = len(relationships_df)
            leads = relationships_df[relationships_df.get('lag_days', 0) < 0]
            lead_percent = len(leads) / total_rels if total_rels > 0 else 0

            passed = lead_percent <= self.thresholds['lead_threshold']

            return {
                'pass': passed,
                'score': (1 - lead_percent) * 100,
                'message': f'{lead_percent*100:.1f}% of relationships use leads (threshold: {self.thresholds["lead_threshold"]*100:.0f}%)',
                'details': {
                    'total_relationships': total_rels,
                    'relationships_with_leads': len(leads),
                    'lead_percent': lead_percent,
                    'threshold': self.thresholds['lead_threshold']
                }
            }
        except Exception as e:
            return {'pass': False, 'score': 0, 'message': f'Error: {str(e)}', 'details': {}}

    def _assess_lags(self, relationships_df: Optional[pd.DataFrame]) -> Dict:
        """3. Lags: Excessive use of lag time"""
        try:
            if relationships_df is None or len(relationships_df) == 0:
                return {'pass': True, 'score': 100, 'message': 'No relationships to assess'}

            total_rels = len(relationships_df)
            excessive_lags = relationships_df[relationships_df.get('lag_days', 0) > self.thresholds['lag_days_threshold']]
            lag_percent = len(excessive_lags) / total_rels if total_rels > 0 else 0

            passed = lag_percent <= self.thresholds['lag_threshold']

            return {
                'pass': passed,
                'score': (1 - lag_percent) * 100,
                'message': f'{lag_percent*100:.1f}% of relationships have excessive lags (>{self.thresholds["lag_days_threshold"]} days)',
                'details': {
                    'total_relationships': total_rels,
                    'relationships_with_excessive_lags': len(excessive_lags),
                    'lag_percent': lag_percent,
                    'lag_threshold_days': self.thresholds['lag_days_threshold']
                }
            }
        except Exception as e:
            return {'pass': False, 'score': 0, 'message': f'Error: {str(e)}', 'details': {}}

    def _assess_relationship_types(self, relationships_df: Optional[pd.DataFrame]) -> Dict:
        """4. Relationship Types: Proper use of FS/SS/SF/FF"""
        try:
            if relationships_df is None or len(relationships_df) == 0:
                return {'pass': True, 'score': 100, 'message': 'No relationships to assess'}

            # Count relationship types
            rel_types = relationships_df['relationship_type'].value_counts()
            total = len(relationships_df)

            # DCMA prefers Finish-to-Start (FS) relationships
            fs_count = rel_types.get('PR_FS', 0) + rel_types.get('FS', 0)
            fs_percent = fs_count / total if total > 0 else 0

            # Pass if >80% are FS (industry best practice)
            passed = fs_percent >= 0.80

            return {
                'pass': passed,
                'score': fs_percent * 100,
                'message': f'{fs_percent*100:.1f}% are Finish-to-Start relationships (recommended: >80%)',
                'details': {
                    'total_relationships': total,
                    'finish_to_start': fs_count,
                    'other_types': total - fs_count,
                    'relationship_type_distribution': rel_types.to_dict()
                }
            }
        except Exception as e:
            return {'pass': False, 'score': 0, 'message': f'Error: {str(e)}', 'details': {}}

    def _assess_constraints(self, activities_df: pd.DataFrame) -> Dict:
        """5. Hard Constraints: Minimal use of date constraints"""
        try:
            # Count activities with hard constraints (not ASAP/ALAP)
            hard_constraints = ['MSO', 'MFO', 'SNET', 'SNLT', 'FNET', 'FNLT']

            if 'constraint_type' not in activities_df.columns:
                return {'pass': True, 'score': 100, 'message': 'No constraint data available'}

            total = len(activities_df)
            constrained = activities_df[activities_df['constraint_type'].isin(hard_constraints)]
            constraint_percent = len(constrained) / total if total > 0 else 0

            passed = constraint_percent <= self.thresholds['constraint_threshold']

            return {
                'pass': passed,
                'score': (1 - constraint_percent) * 100,
                'message': f'{constraint_percent*100:.1f}% have hard constraints (threshold: {self.thresholds["constraint_threshold"]*100:.0f}%)',
                'details': {
                    'total_activities': total,
                    'hard_constrained_activities': len(constrained),
                    'constraint_percent': constraint_percent,
                    'threshold': self.thresholds['constraint_threshold']
                }
            }
        except Exception as e:
            return {'pass': False, 'score': 0, 'message': f'Error: {str(e)}', 'details': {}}

    def _assess_high_float(self, activities_df: pd.DataFrame) -> Dict:
        """6. High Float: Activities with excessive float"""
        try:
            if 'total_float_days' not in activities_df.columns:
                return {'pass': True, 'score': 100, 'message': 'No float data available'}

            # Active tasks only
            active = activities_df[activities_df['status'] != 'TK_Complete']
            total = len(active)

            if total == 0:
                return {'pass': True, 'score': 100, 'message': 'No active tasks'}

            high_float = active[active['total_float_days'] > self.thresholds['float_high_threshold']]
            high_float_percent = len(high_float) / total

            passed = high_float_percent <= self.thresholds['float_high_percent']

            return {
                'pass': passed,
                'score': (1 - high_float_percent) * 100,
                'message': f'{high_float_percent*100:.1f}% have high float (>{self.thresholds["float_high_threshold"]} days)',
                'details': {
                    'total_active_activities': total,
                    'high_float_activities': len(high_float),
                    'high_float_percent': high_float_percent,
                    'float_threshold_days': self.thresholds['float_high_threshold']
                }
            }
        except Exception as e:
            return {'pass': False, 'score': 0, 'message': f'Error: {str(e)}', 'details': {}}

    def _assess_negative_float(self, activities_df: pd.DataFrame) -> Dict:
        """7. Negative Float: Behind schedule activities"""
        try:
            if 'total_float_days' not in activities_df.columns:
                return {'pass': True, 'score': 100, 'message': 'No float data available'}

            active = activities_df[activities_df['status'] != 'TK_Complete']
            total = len(active)

            if total == 0:
                return {'pass': True, 'score': 100, 'message': 'No active tasks'}

            negative_float = active[active['total_float_days'] < 0]
            negative_count = len(negative_float)

            passed = negative_count <= self.thresholds['negative_float_threshold']

            return {
                'pass': passed,
                'score': 100 if passed else 0,
                'message': f'{negative_count} activities with negative float (threshold: {self.thresholds["negative_float_threshold"]})',
                'details': {
                    'total_active_activities': total,
                    'negative_float_activities': negative_count,
                    'threshold': self.thresholds['negative_float_threshold']
                }
            }
        except Exception as e:
            return {'pass': False, 'score': 0, 'message': f'Error: {str(e)}', 'details': {}}

    def _assess_high_duration(self, activities_df: pd.DataFrame) -> Dict:
        """8. High Duration: Overly long activities"""
        try:
            if 'duration_days' not in activities_df.columns:
                return {'pass': True, 'score': 100, 'message': 'No duration data available'}

            active = activities_df[activities_df['status'] != 'TK_Complete']
            total = len(active)

            if total == 0:
                return {'pass': True, 'score': 100, 'message': 'No active tasks'}

            high_duration = active[active['duration_days'] > self.thresholds['duration_high_threshold']]
            high_duration_percent = len(high_duration) / total

            passed = high_duration_percent <= self.thresholds['duration_high_percent']

            return {
                'pass': passed,
                'score': (1 - high_duration_percent) * 100,
                'message': f'{high_duration_percent*100:.1f}% have long durations (>{self.thresholds["duration_high_threshold"]} days)',
                'details': {
                    'total_active_activities': total,
                    'high_duration_activities': len(high_duration),
                    'high_duration_percent': high_duration_percent,
                    'duration_threshold_days': self.thresholds['duration_high_threshold']
                }
            }
        except Exception as e:
            return {'pass': False, 'score': 0, 'message': f'Error: {str(e)}', 'details': {}}

    def _assess_invalid_dates(self, activities_df: pd.DataFrame) -> Dict:
        """9. Invalid Dates: Date logic errors"""
        try:
            issues = []

            # Check for activities where finish < start
            if 'start_date' in activities_df.columns and 'finish_date' in activities_df.columns:
                invalid = activities_df[
                    (pd.notna(activities_df['start_date'])) &
                    (pd.notna(activities_df['finish_date'])) &
                    (activities_df['finish_date'] < activities_df['start_date'])
                ]
                if len(invalid) > 0:
                    issues.append(f'{len(invalid)} activities have finish before start')

            # Check for null dates on active tasks
            active = activities_df[activities_df['status'] != 'TK_Complete']
            null_starts = active[pd.isna(active['start_date'])]
            null_finishes = active[pd.isna(active['finish_date'])]

            if len(null_starts) > 0:
                issues.append(f'{len(null_starts)} active tasks missing start dates')
            if len(null_finishes) > 0:
                issues.append(f'{len(null_finishes)} active tasks missing finish dates')

            passed = len(issues) == 0

            return {
                'pass': passed,
                'score': 100 if passed else 0,
                'message': 'No date issues found' if passed else '; '.join(issues),
                'details': {
                    'total_issues': len(issues),
                    'issues': issues
                }
            }
        except Exception as e:
            return {'pass': False, 'score': 0, 'message': f'Error: {str(e)}', 'details': {}}

    def _assess_resources(self, activities_df: pd.DataFrame, options: Dict) -> Dict:
        """10. Resources: Proper resource loading"""
        try:
            # Check if resource data is available
            resources_df = options.get('resources_df')

            if resources_df is None or len(resources_df) == 0:
                return {
                    'pass': False,
                    'score': 0,
                    'message': 'No resource data available',
                    'details': {'note': 'Resource loading data not provided'}
                }

            # If resources exist, consider passed
            # (More detailed analysis would require resource assignments)
            return {
                'pass': True,
                'score': 100,
                'message': f'{len(resources_df)} resources loaded',
                'details': {
                    'total_resources': len(resources_df)
                }
            }
        except Exception as e:
            return {'pass': False, 'score': 0, 'message': f'Error: {str(e)}', 'details': {}}

    def _assess_missed_tasks(self, activities_df: pd.DataFrame) -> Dict:
        """11. Missed Tasks: Tasks that should have started but haven't"""
        try:
            if 'start_date' not in activities_df.columns or 'status' not in activities_df.columns:
                return {'pass': True, 'score': 100, 'message': 'Insufficient data to assess'}

            now = pd.Timestamp.now()

            # Tasks that should have started (planned start < now) but haven't (status = not started)
            missed = activities_df[
                (pd.notna(activities_df['start_date'])) &
                (activities_df['start_date'] < now) &
                (activities_df.get('percent_complete', 0) == 0) &
                (activities_df['status'] != 'TK_Complete')
            ]

            missed_count = len(missed)
            passed = missed_count == 0

            return {
                'pass': passed,
                'score': 100 if passed else 0,
                'message': f'{missed_count} tasks missed their planned start (threshold: 0)',
                'details': {
                    'missed_tasks': missed_count,
                    'threshold': 0
                }
            }
        except Exception as e:
            return {'pass': False, 'score': 0, 'message': f'Error: {str(e)}', 'details': {}}

    def _assess_critical_path_test(self, activities_df: pd.DataFrame) -> Dict:
        """12. Critical Path Test: Valid critical path exists"""
        try:
            if 'is_critical' not in activities_df.columns:
                return {'pass': False, 'score': 0, 'message': 'No critical path data'}

            critical_activities = activities_df[activities_df['is_critical'] == True]
            critical_count = len(critical_activities)

            # Critical path should exist and be reasonable (not too many or too few tasks)
            total_active = len(activities_df[activities_df['status'] != 'TK_Complete'])
            critical_percent = critical_count / total_active if total_active > 0 else 0

            # Typically 10-30% of tasks on critical path is reasonable
            passed = critical_count > 0 and 0.10 <= critical_percent <= 0.30

            return {
                'pass': passed,
                'score': 100 if passed else 50,
                'message': f'{critical_count} activities on critical path ({critical_percent*100:.1f}% of active)',
                'details': {
                    'critical_activities': critical_count,
                    'total_active_activities': total_active,
                    'critical_percent': critical_percent
                }
            }
        except Exception as e:
            return {'pass': False, 'score': 0, 'message': f'Error: {str(e)}', 'details': {}}

    def _assess_cpli(self, activities_df: pd.DataFrame, options: Dict) -> Dict:
        """13. Critical Path Length Index: Ratio of critical path to total duration"""
        try:
            if 'is_critical' not in activities_df.columns or 'duration_days' not in activities_df.columns:
                return {'pass': False, 'score': 0, 'message': 'Insufficient data for CPLI'}

            # Calculate critical path length (sum of critical activities' durations)
            critical_activities = activities_df[activities_df['is_critical'] == True]
            critical_path_length = critical_activities['duration_days'].sum()

            # Get project duration (from options or calculate)
            project_duration = options.get('project_duration_days')
            if project_duration is None:
                # Calculate from start/finish dates
                if 'start_date' in activities_df.columns and 'finish_date' in activities_df.columns:
                    min_start = activities_df['start_date'].min()
                    max_finish = activities_df['finish_date'].max()
                    if pd.notna(min_start) and pd.notna(max_finish):
                        project_duration = (max_finish - min_start).days

            if project_duration is None or project_duration == 0:
                return {'pass': False, 'score': 0, 'message': 'Cannot calculate project duration'}

            cpli = critical_path_length / project_duration

            # DCMA threshold: 0.90 to 1.10
            passed = self.thresholds['cpli_min'] <= cpli <= self.thresholds['cpli_max']

            return {
                'pass': passed,
                'score': 100 if passed else 50,
                'message': f'CPLI = {cpli:.2f} (acceptable range: {self.thresholds["cpli_min"]:.2f} to {self.thresholds["cpli_max"]:.2f})',
                'details': {
                    'cpli': cpli,
                    'critical_path_length_days': critical_path_length,
                    'project_duration_days': project_duration,
                    'cpli_min_threshold': self.thresholds['cpli_min'],
                    'cpli_max_threshold': self.thresholds['cpli_max']
                }
            }
        except Exception as e:
            return {'pass': False, 'score': 0, 'message': f'Error: {str(e)}', 'details': {}}

    def _assess_baseline(self, activities_df: pd.DataFrame, options: Dict) -> Dict:
        """14. Baseline: Existence of performance baseline"""
        try:
            # Check if baseline data exists
            baseline_exists = options.get('has_baseline', False)

            # Could also check for baseline columns in activities_df
            baseline_cols = [col for col in activities_df.columns if 'baseline' in col.lower()]
            if len(baseline_cols) > 0:
                baseline_exists = True

            return {
                'pass': baseline_exists,
                'score': 100 if baseline_exists else 0,
                'message': 'Performance baseline exists' if baseline_exists else 'No performance baseline found',
                'details': {
                    'has_baseline': baseline_exists,
                    'baseline_columns_found': baseline_cols
                }
            }
        except Exception as e:
            return {'pass': False, 'score': 0, 'message': f'Error: {str(e)}', 'details': {}}

    # ==================== HELPER METHODS ====================

    def _get_rating(self, score: float) -> str:
        """Convert score to letter rating"""
        if score >= 90:
            return 'A - Excellent'
        elif score >= 80:
            return 'B - Good'
        elif score >= 70:
            return 'C - Fair'
        elif score >= 60:
            return 'D - Poor'
        else:
            return 'F - Failing'


# Plugin registration
class DCMA14Plugin(Plugin):
    """DCMA 14-Point Assessment Plugin"""

    metadata = PluginMetadata(
        name="dcma14_analyzer",
        version="1.0.0",
        description="DCMA 14-Point Schedule Quality Assessment",
        author="ARGO Development Team",
        capabilities=[PluginCapability.ANALYZER]
    )

    def initialize(self, system):
        """Initialize plugin"""
        self.analyzer = DCMA14Analyzer(system=system)
        if hasattr(system, 'plugin_manager'):
            system.plugin_manager.register_analyzer(self.analyzer)
        logger.info("✅ DCMA 14-Point Plugin initialized")
