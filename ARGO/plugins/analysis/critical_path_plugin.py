"""
Critical Path Method (CPM) Analysis Plugin for ARGO
Calculates and analyzes the critical path of project schedules

This plugin provides:
1. Critical Path Identification using networkx graph algorithms
2. Forward/Backward Pass calculations
3. Float/Slack analysis for all activities
4. Critical path visualization data
5. Near-critical path identification
6. Schedule compression analysis opportunities

Uses networkx for efficient graph-based CPM calculations.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import time
from datetime import datetime, timedelta

try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

from core.plugins import (
    Plugin,
    BaseAnalyzer,
    AnalysisResult,
    PluginMetadata,
    PluginCapability
)

logger = logging.getLogger(__name__)


class CriticalPathAnalyzer(BaseAnalyzer):
    """
    Critical Path Method (CPM) Analyzer

    Calculates critical path using network analysis algorithms.
    Provides comprehensive float analysis and schedule optimization insights.

    Key Metrics:
    - Critical Path: Longest path through project network
    - Total Float: Amount of delay possible without affecting project end
    - Free Float: Amount of delay possible without affecting successors
    - Near-Critical Activities: Activities with float < 5 days
    """

    def __init__(self, system=None, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.system = system
        self.graph = None

    @property
    def name(self) -> str:
        return "critical_path_analyzer"

    @property
    def supported_formats(self) -> List[str]:
        return ['.xer', '.xml', '.json']

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Critical Path Method (CPM) analysis with networkx"

    def validate(self, file_path: str) -> tuple[bool, Optional[str]]:
        """Validate input for CPM analysis"""
        is_valid, error = super().validate(file_path)

        if not is_valid:
            return False, error

        if not HAS_PANDAS:
            return False, "pandas not installed"

        if not HAS_NETWORKX:
            return False, "networkx not installed. Install with: pip install networkx"

        return True, None

    def analyze(self, file_path: str, options: Optional[Dict] = None) -> AnalysisResult:
        """
        Perform Critical Path Method analysis

        Options:
            - activities_df: DataFrame with activities (required)
            - relationships_df: DataFrame with relationships (required)
            - near_critical_threshold: Days threshold for near-critical (default: 5)
            - calculate_alternate_paths: Find alternate critical paths (default: True)
        """
        start_time = time.time()

        try:
            logger.info(f"Starting Critical Path Analysis: {Path(file_path).name}")

            options = options or {}

            # Get parsed data
            activities_df = options.get('activities_df')
            relationships_df = options.get('relationships_df')

            if activities_df is None or relationships_df is None:
                return AnalysisResult(
                    status='error',
                    data={},
                    errors=["Both activities_df and relationships_df required"]
                )

            # Build network graph
            G = self._build_network_graph(activities_df, relationships_df)
            self.graph = G

            if G is None or G.number_of_nodes() == 0:
                return AnalysisResult(
                    status='error',
                    data={},
                    errors=["Failed to build network graph"]
                )

            # Perform CPM calculations
            activities_with_cpm = self._calculate_cpm(G, activities_df)

            # Identify critical path(s)
            critical_paths = self._identify_critical_paths(G, activities_with_cpm)

            # Near-critical analysis
            near_critical_threshold = options.get('near_critical_threshold', 5)
            near_critical = self._identify_near_critical(activities_with_cpm, near_critical_threshold)

            # Calculate metrics
            metrics = self._calculate_metrics(activities_with_cpm, critical_paths)

            # Find schedule compression opportunities
            compression_opportunities = self._find_compression_opportunities(
                activities_with_cpm,
                critical_paths
            )

            execution_time = (time.time() - start_time) * 1000

            logger.info(f"✓ CPM Analysis complete: {len(critical_paths)} critical path(s) found")

            return AnalysisResult(
                status='success',
                data={
                    'activities_with_cpm': activities_with_cpm.to_dict('records'),
                    'critical_paths': critical_paths,
                    'near_critical_activities': near_critical,
                    'metrics': metrics,
                    'compression_opportunities': compression_opportunities
                },
                metadata={
                    'analyzer': self.name,
                    'version': self.version,
                    'schedule_file': str(Path(file_path).name),
                    'total_activities': len(activities_df),
                    'total_relationships': len(relationships_df),
                    'network_nodes': G.number_of_nodes(),
                    'network_edges': G.number_of_edges()
                },
                execution_time_ms=execution_time
            )

        except Exception as e:
            logger.error(f"CPM Analysis failed: {e}", exc_info=True)
            return AnalysisResult(
                status='error',
                data={},
                errors=[f"CPM analysis failed: {str(e)}"],
                execution_time_ms=(time.time() - start_time) * 1000
            )

    # ==================== NETWORK BUILDING ====================

    def _build_network_graph(
        self,
        activities_df: pd.DataFrame,
        relationships_df: pd.DataFrame
    ) -> nx.DiGraph:
        """Build directed graph from activities and relationships"""
        try:
            G = nx.DiGraph()

            # Add nodes (activities) with durations
            for _, activity in activities_df.iterrows():
                G.add_node(
                    activity['activity_id'],
                    duration=activity.get('duration_days', 0),
                    name=activity.get('activity_name', ''),
                    status=activity.get('status', ''),
                    percent_complete=activity.get('percent_complete', 0)
                )

            # Add edges (relationships) with lag
            for _, rel in relationships_df.iterrows():
                pred = rel['predecessor_id']
                succ = rel['successor_id']
                lag = rel.get('lag_days', 0)
                rel_type = rel.get('relationship_type', 'PR_FS')

                # For now, only handle Finish-to-Start (most common)
                # More complex logic needed for SS, FF, SF
                if 'FS' in rel_type or rel_type == 'PR_FS':
                    G.add_edge(pred, succ, lag=lag, type=rel_type)

            # Add artificial start and end nodes for single-point entry/exit
            start_nodes = [n for n in G.nodes() if G.in_degree(n) == 0]
            end_nodes = [n for n in G.nodes() if G.out_degree(n) == 0]

            if len(start_nodes) > 0:
                G.add_node('START', duration=0, name='Project Start')
                for node in start_nodes:
                    G.add_edge('START', node, lag=0, type='ARTIFICIAL')

            if len(end_nodes) > 0:
                G.add_node('END', duration=0, name='Project End')
                for node in end_nodes:
                    G.add_edge(node, 'END', lag=0, type='ARTIFICIAL')

            logger.debug(f"Built network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

            return G

        except Exception as e:
            logger.error(f"Failed to build network graph: {e}")
            return None

    # ==================== CPM CALCULATIONS ====================

    def _calculate_cpm(
        self,
        G: nx.DiGraph,
        activities_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Calculate Critical Path Method values (forward/backward pass)"""
        try:
            # Forward Pass: Calculate Early Start (ES) and Early Finish (EF)
            early_start = {'START': 0}
            early_finish = {'START': 0}

            # Topological sort for forward pass
            for node in nx.topological_sort(G):
                if node == 'START':
                    continue

                # Early Start = max(predecessor EF + lag)
                predecessors = list(G.predecessors(node))
                if len(predecessors) == 0:
                    early_start[node] = 0
                else:
                    es_values = []
                    for pred in predecessors:
                        pred_ef = early_finish.get(pred, 0)
                        lag = G[pred][node].get('lag', 0)
                        es_values.append(pred_ef + lag)
                    early_start[node] = max(es_values)

                # Early Finish = ES + duration
                duration = G.nodes[node].get('duration', 0)
                early_finish[node] = early_start[node] + duration

            # Project duration
            project_duration = early_finish.get('END', 0)

            # Backward Pass: Calculate Late Start (LS) and Late Finish (LF)
            late_finish = {'END': project_duration}
            late_start = {'END': project_duration}

            # Reverse topological sort for backward pass
            for node in reversed(list(nx.topological_sort(G))):
                if node == 'END':
                    continue

                # Late Finish = min(successor LS - lag)
                successors = list(G.successors(node))
                if len(successors) == 0:
                    late_finish[node] = project_duration
                else:
                    lf_values = []
                    for succ in successors:
                        succ_ls = late_start.get(succ, project_duration)
                        lag = G[node][succ].get('lag', 0)
                        lf_values.append(succ_ls - lag)
                    late_finish[node] = min(lf_values)

                # Late Start = LF - duration
                duration = G.nodes[node].get('duration', 0)
                late_start[node] = late_finish[node] - duration

            # Calculate Float values
            total_float = {}
            free_float = {}
            is_critical = {}

            for node in G.nodes():
                if node in ['START', 'END']:
                    continue

                # Total Float = LS - ES (or LF - EF)
                tf = late_start.get(node, 0) - early_start.get(node, 0)
                total_float[node] = tf

                # Free Float = min(successor ES) - EF
                successors = list(G.successors(node))
                if len(successors) == 0:
                    free_float[node] = 0
                else:
                    successor_es = [early_start.get(s, 0) - G[node][s].get('lag', 0) for s in successors]
                    ff = min(successor_es) - early_finish.get(node, 0)
                    free_float[node] = ff

                # Critical if total float <= 0
                is_critical[node] = (tf <= 0)

            # Add CPM data to activities DataFrame
            activities_with_cpm = activities_df.copy()
            activities_with_cpm['early_start_cpm'] = activities_with_cpm['activity_id'].map(early_start)
            activities_with_cpm['early_finish_cpm'] = activities_with_cpm['activity_id'].map(early_finish)
            activities_with_cpm['late_start_cpm'] = activities_with_cpm['activity_id'].map(late_start)
            activities_with_cpm['late_finish_cpm'] = activities_with_cpm['activity_id'].map(late_finish)
            activities_with_cpm['total_float_cpm'] = activities_with_cpm['activity_id'].map(total_float)
            activities_with_cpm['free_float_cpm'] = activities_with_cpm['activity_id'].map(free_float)
            activities_with_cpm['is_critical_cpm'] = activities_with_cpm['activity_id'].map(is_critical)

            return activities_with_cpm

        except Exception as e:
            logger.error(f"CPM calculation failed: {e}")
            raise

    def _identify_critical_paths(
        self,
        G: nx.DiGraph,
        activities_df: pd.DataFrame
    ) -> List[Dict]:
        """Identify critical path(s) through the network"""
        try:
            # Filter critical activities
            critical_activities = activities_df[activities_df['is_critical_cpm'] == True]

            if len(critical_activities) == 0:
                return []

            # Build subgraph of only critical activities
            critical_ids = set(critical_activities['activity_id'].values)
            critical_ids.add('START')
            critical_ids.add('END')

            critical_subgraph = G.subgraph(critical_ids)

            # Find all paths from START to END
            try:
                all_paths = list(nx.all_simple_paths(critical_subgraph, 'START', 'END'))
            except nx.NetworkXNoPath:
                all_paths = []

            # Remove START/END from paths and calculate metrics
            critical_paths = []
            for path in all_paths:
                # Remove artificial nodes
                path_activities = [node for node in path if node not in ['START', 'END']]

                if len(path_activities) == 0:
                    continue

                # Calculate path metrics
                path_duration = sum(
                    G.nodes[node].get('duration', 0)
                    for node in path_activities
                )

                path_info = {
                    'path': path_activities,
                    'path_length': len(path_activities),
                    'total_duration': path_duration,
                    'activity_names': [
                        G.nodes[node].get('name', node)
                        for node in path_activities
                    ]
                }

                critical_paths.append(path_info)

            # Sort by duration (longest first)
            critical_paths.sort(key=lambda x: x['total_duration'], reverse=True)

            return critical_paths

        except Exception as e:
            logger.error(f"Critical path identification failed: {e}")
            return []

    def _identify_near_critical(
        self,
        activities_df: pd.DataFrame,
        threshold: float = 5.0
    ) -> List[Dict]:
        """Identify near-critical activities (small float)"""
        try:
            near_critical = activities_df[
                (activities_df['is_critical_cpm'] == False) &
                (activities_df['total_float_cpm'] > 0) &
                (activities_df['total_float_cpm'] <= threshold)
            ]

            near_critical_list = []
            for _, activity in near_critical.iterrows():
                near_critical_list.append({
                    'activity_id': activity['activity_id'],
                    'activity_name': activity.get('activity_name', ''),
                    'total_float': activity['total_float_cpm'],
                    'duration': activity.get('duration_days', 0)
                })

            return near_critical_list

        except Exception as e:
            logger.error(f"Near-critical identification failed: {e}")
            return []

    # ==================== METRICS ====================

    def _calculate_metrics(
        self,
        activities_df: pd.DataFrame,
        critical_paths: List[Dict]
    ) -> Dict:
        """Calculate overall CPM metrics"""
        try:
            critical_activities = activities_df[activities_df['is_critical_cpm'] == True]
            non_critical = activities_df[activities_df['is_critical_cpm'] == False]

            metrics = {
                'total_activities': len(activities_df),
                'critical_activities': len(critical_activities),
                'non_critical_activities': len(non_critical),
                'critical_percentage': (len(critical_activities) / len(activities_df) * 100) if len(activities_df) > 0 else 0,
                'number_of_critical_paths': len(critical_paths),
                'longest_critical_path_duration': critical_paths[0]['total_duration'] if critical_paths else 0,
                'longest_critical_path_activities': critical_paths[0]['path_length'] if critical_paths else 0,
                'average_total_float': non_critical['total_float_cpm'].mean() if len(non_critical) > 0 else 0,
                'max_total_float': activities_df['total_float_cpm'].max(),
                'min_total_float': activities_df['total_float_cpm'].min(),
            }

            return metrics

        except Exception as e:
            logger.error(f"Metrics calculation failed: {e}")
            return {}

    def _find_compression_opportunities(
        self,
        activities_df: pd.DataFrame,
        critical_paths: List[Dict]
    ) -> List[Dict]:
        """Identify opportunities for schedule compression (crashing/fast-tracking)"""
        try:
            if not critical_paths:
                return []

            # Get longest critical path
            longest_path = critical_paths[0]
            critical_ids = longest_path['path']

            # Find critical activities with longest durations (good candidates for crashing)
            critical_activities = activities_df[activities_df['activity_id'].isin(critical_ids)]
            critical_activities = critical_activities.sort_values('duration_days', ascending=False)

            opportunities = []

            # Top 5 longest critical activities
            for _, activity in critical_activities.head(5).iterrows():
                opportunities.append({
                    'activity_id': activity['activity_id'],
                    'activity_name': activity.get('activity_name', ''),
                    'current_duration': activity.get('duration_days', 0),
                    'compression_type': 'crashing',
                    'reason': 'Long duration critical activity - candidate for crashing (adding resources)',
                    'potential_impact': 'High - directly reduces project duration'
                })

            return opportunities

        except Exception as e:
            logger.error(f"Compression opportunities analysis failed: {e}")
            return []


# Plugin registration
class CriticalPathPlugin(Plugin):
    """Critical Path Analysis Plugin"""

    metadata = PluginMetadata(
        name="critical_path_analyzer",
        version="1.0.0",
        description="Critical Path Method (CPM) analysis using networkx",
        author="ARGO Development Team",
        capabilities=[PluginCapability.ANALYZER]
    )

    def initialize(self, system):
        """Initialize plugin"""
        self.analyzer = CriticalPathAnalyzer(system=system)
        if hasattr(system, 'plugin_manager'):
            system.plugin_manager.register_analyzer(self.analyzer)
        logger.info("✅ Critical Path Plugin initialized")
