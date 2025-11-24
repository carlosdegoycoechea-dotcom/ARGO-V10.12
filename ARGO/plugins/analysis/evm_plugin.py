"""
Earned Value Management (EVM) Plugin for ARGO
Calculates and analyzes Earned Value metrics for project performance

EVM integrates scope, schedule, and cost to assess project performance and predict outcomes.

Key Metrics:
- PV (Planned Value): Authorized budget assigned to scheduled work
- EV (Earned Value): Budget for work actually completed
- AC (Actual Cost): Actual cost incurred for work performed
- SV (Schedule Variance): EV - PV (schedule performance)
- CV (Cost Variance): EV - AC (cost performance)
- SPI (Schedule Performance Index): EV / PV
- CPI (Cost Performance Index): EV / AC
- EAC (Estimate At Completion): Forecasted total cost
- ETC (Estimate To Complete): Remaining cost forecast
- VAC (Variance At Completion): BAC - EAC

Standard: ANSI/EIA-748 (Earned Value Management Systems)
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


class EVMAnalyzer(BaseAnalyzer):
    """
    Earned Value Management Analyzer

    Calculates EVM metrics and provides performance forecasts.
    Requires cost and progress data to be available in schedule.
    """

    def __init__(self, system=None, config: Optional[Dict] = None):
        super().__init__()
        self.config = config or {}
        self.system = system

    @property
    def name(self) -> str:
        return "evm_analyzer"

    @property
    def supported_formats(self) -> List[str]:
        return ['.xer', '.xml', '.json']

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Earned Value Management (EVM) analysis and forecasting"

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
        Perform Earned Value Management Analysis

        Options:
            - activities_df: DataFrame with activities (required)
            - budget_at_completion: Total project budget (BAC)
            - actual_cost_to_date: Actual costs incurred (optional)
            - status_date: Analysis date (default: today)
        """
        start_time = time.time()

        try:
            logger.info(f"Starting EVM Analysis: {Path(file_path).name}")

            options = options or {}
            activities_df = options.get('activities_df')

            if activities_df is None:
                return AnalysisResult(
                    status='error',
                    data={},
                    errors=["activities_df required in options"]
                )

            # Get BAC (Budget At Completion)
            budget_at_completion = options.get('budget_at_completion')

            if budget_at_completion is None:
                # Try to calculate from activities
                if 'budget' in activities_df.columns or 'planned_cost' in activities_df.columns:
                    cost_col = 'budget' if 'budget' in activities_df.columns else 'planned_cost'
                    budget_at_completion = activities_df[cost_col].sum()
                else:
                    # Fallback: use duration as proxy
                    logger.warning("No cost data found. Using duration as proxy for EVM calculations.")
                    budget_at_completion = activities_df.get('duration_days', 0).sum()

            # Status date
            status_date = options.get('status_date', datetime.now())

            # Calculate EVM metrics
            evm_metrics = self._calculate_evm_metrics(
                activities_df,
                budget_at_completion,
                status_date,
                options
            )

            # Performance analysis
            performance = self._analyze_performance(evm_metrics)

            # Forecasting
            forecast = self._forecast_completion(evm_metrics, budget_at_completion)

            # Trend analysis
            trend = self._analyze_trend(evm_metrics)

            execution_time = (time.time() - start_time) * 1000

            logger.info(f"✓ EVM Analysis complete: SPI={evm_metrics.get('spi', 0):.2f}, CPI={evm_metrics.get('cpi', 0):.2f}")

            return AnalysisResult(
                status='success',
                data={
                    'evm_metrics': evm_metrics,
                    'performance': performance,
                    'forecast': forecast,
                    'trend': trend
                },
                metadata={
                    'analyzer': self.name,
                    'version': self.version,
                    'schedule_file': str(Path(file_path).name),
                    'total_activities': len(activities_df),
                    'status_date': status_date.isoformat() if isinstance(status_date, datetime) else str(status_date),
                    'budget_at_completion': budget_at_completion
                },
                execution_time_ms=execution_time
            )

        except Exception as e:
            logger.error(f"EVM Analysis failed: {e}", exc_info=True)
            return AnalysisResult(
                status='error',
                data={},
                errors=[f"EVM analysis failed: {str(e)}"],
                execution_time_ms=(time.time() - start_time) * 1000
            )

    # ==================== EVM CALCULATIONS ====================

    def _calculate_evm_metrics(
        self,
        activities_df: pd.DataFrame,
        bac: float,
        status_date: datetime,
        options: Dict
    ) -> Dict:
        """Calculate core EVM metrics"""
        try:
            # Determine if we have cost data or use duration as proxy
            has_cost_data = 'budget' in activities_df.columns or 'planned_cost' in activities_df.columns
            cost_col = 'budget' if 'budget' in activities_df.columns else ('planned_cost' if 'planned_cost' in activities_df.columns else None)
            actual_cost_col = 'actual_cost' if 'actual_cost' in activities_df.columns else None

            # Calculate PV (Planned Value) - budget for work scheduled to be complete
            if has_cost_data:
                # Activities that should be complete or in progress by status date
                pv = activities_df[
                    (activities_df['start_date'] <= status_date) |
                    (pd.isna(activities_df['start_date']))
                ][cost_col].sum()
            else:
                # Use percent of time elapsed as proxy
                total_duration = activities_df['duration_days'].sum()
                pv = bac * (activities_df[activities_df.get('percent_complete', 0) > 0]['duration_days'].sum() / total_duration)

            # Calculate EV (Earned Value) - budget for work actually completed
            if has_cost_data and 'percent_complete' in activities_df.columns:
                ev = (activities_df[cost_col] * activities_df['percent_complete'] / 100).sum()
            else:
                # Use percent complete as proxy
                avg_completion = activities_df.get('percent_complete', 0).mean()
                ev = bac * (avg_completion / 100)

            # Calculate AC (Actual Cost) - actual costs incurred
            if actual_cost_col and actual_cost_col in activities_df.columns:
                ac = activities_df[actual_cost_col].sum()
            else:
                # If no actual cost data, use AC from options or assume AC = EV (no cost variance)
                ac = options.get('actual_cost_to_date', ev)

            # Variance calculations
            sv = ev - pv  # Schedule Variance
            cv = ev - ac  # Cost Variance

            # Performance indices
            spi = ev / pv if pv > 0 else 1.0  # Schedule Performance Index
            cpi = ev / ac if ac > 0 else 1.0  # Cost Performance Index

            # Percent complete
            percent_complete = (ev / bac * 100) if bac > 0 else 0

            return {
                'bac': bac,  # Budget At Completion
                'pv': pv,    # Planned Value
                'ev': ev,    # Earned Value
                'ac': ac,    # Actual Cost
                'sv': sv,    # Schedule Variance
                'cv': cv,    # Cost Variance
                'spi': spi,  # Schedule Performance Index
                'cpi': cpi,  # Cost Performance Index
                'percent_complete': percent_complete,
                'has_cost_data': has_cost_data
            }

        except Exception as e:
            logger.error(f"EVM metrics calculation failed: {e}")
            return {}

    def _analyze_performance(self, metrics: Dict) -> Dict:
        """Analyze project performance based on EVM metrics"""
        try:
            spi = metrics.get('spi', 1.0)
            cpi = metrics.get('cpi', 1.0)
            sv = metrics.get('sv', 0)
            cv = metrics.get('cv', 0)

            # Schedule performance
            if spi >= 1.0:
                schedule_status = 'ahead' if spi > 1.05 else 'on_track'
                schedule_health = 'green'
                schedule_message = f'Ahead of schedule (SPI: {spi:.2f})'
            elif spi >= 0.95:
                schedule_status = 'slightly_behind'
                schedule_health = 'yellow'
                schedule_message = f'Slightly behind schedule (SPI: {spi:.2f})'
            else:
                schedule_status = 'behind'
                schedule_health = 'red'
                schedule_message = f'Behind schedule (SPI: {spi:.2f})'

            # Cost performance
            if cpi >= 1.0:
                cost_status = 'under_budget' if cpi > 1.05 else 'on_budget'
                cost_health = 'green'
                cost_message = f'Under budget (CPI: {cpi:.2f})'
            elif cpi >= 0.95:
                cost_status = 'slightly_over'
                cost_health = 'yellow'
                cost_message = f'Slightly over budget (CPI: {cpi:.2f})'
            else:
                cost_status = 'over_budget'
                cost_health = 'red'
                cost_message = f'Over budget (CPI: {cpi:.2f})'

            # Overall health (worst of schedule and cost)
            if schedule_health == 'red' or cost_health == 'red':
                overall_health = 'red'
                overall_status = 'critical'
            elif schedule_health == 'yellow' or cost_health == 'yellow':
                overall_health = 'yellow'
                overall_status = 'warning'
            else:
                overall_health = 'green'
                overall_status = 'healthy'

            return {
                'overall': {
                    'status': overall_status,
                    'health': overall_health
                },
                'schedule': {
                    'status': schedule_status,
                    'health': schedule_health,
                    'message': schedule_message,
                    'spi': spi,
                    'variance_days': sv  # In cost units or duration proxy
                },
                'cost': {
                    'status': cost_status,
                    'health': cost_health,
                    'message': cost_message,
                    'cpi': cpi,
                    'variance_amount': cv
                }
            }

        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return {}

    def _forecast_completion(self, metrics: Dict, bac: float) -> Dict:
        """Forecast project completion metrics"""
        try:
            ev = metrics.get('ev', 0)
            ac = metrics.get('ac', 0)
            cpi = metrics.get('cpi', 1.0)
            spi = metrics.get('spi', 1.0)

            # EAC (Estimate At Completion) - forecasted total cost
            # Method: EAC = BAC / CPI (assumes current performance continues)
            eac = bac / cpi if cpi > 0 else bac

            # ETC (Estimate To Complete) - remaining cost
            etc = eac - ac

            # VAC (Variance At Completion) - projected cost variance
            vac = bac - eac

            # TCPI (To-Complete Performance Index) - efficiency needed to meet budget
            # TCPI = (BAC - EV) / (BAC - AC)
            remaining_work = bac - ev
            remaining_budget = bac - ac
            tcpi = remaining_work / remaining_budget if remaining_budget > 0 else 1.0

            # Schedule forecast (using SPI)
            # If we have duration data, forecast schedule completion
            percent_complete = metrics.get('percent_complete', 0)
            if spi > 0:
                forecasted_duration_factor = 1 / spi
            else:
                forecasted_duration_factor = 1.0

            return {
                'eac': eac,  # Estimate At Completion
                'etc': etc,  # Estimate To Complete
                'vac': vac,  # Variance At Completion
                'tcpi': tcpi,  # To-Complete Performance Index
                'cost_overrun_percentage': ((eac - bac) / bac * 100) if bac > 0 else 0,
                'schedule_extension_factor': forecasted_duration_factor,
                'interpretation': {
                    'eac': f'Projected final cost: {eac:.2f} (BAC: {bac:.2f})',
                    'etc': f'Remaining cost: {etc:.2f}',
                    'vac': 'Under budget' if vac > 0 else 'Over budget',
                    'tcpi': f'Need CPI of {tcpi:.2f} to stay on budget'
                }
            }

        except Exception as e:
            logger.error(f"Forecast calculation failed: {e}")
            return {}

    def _analyze_trend(self, metrics: Dict) -> Dict:
        """Analyze trends (simplified - would need historical data for full trend analysis)"""
        try:
            spi = metrics.get('spi', 1.0)
            cpi = metrics.get('cpi', 1.0)

            # Simple trend indication based on current indices
            # (In production, this would compare against historical SPI/CPI values)

            if spi > 1.0 and cpi > 1.0:
                trend = 'improving'
                trend_message = 'Both schedule and cost performance are positive'
            elif spi < 1.0 and cpi < 1.0:
                trend = 'declining'
                trend_message = 'Both schedule and cost performance are negative'
            elif spi > cpi:
                trend = 'schedule_better'
                trend_message = 'Schedule performance better than cost performance'
            else:
                trend = 'cost_better'
                trend_message = 'Cost performance better than schedule performance'

            return {
                'trend': trend,
                'message': trend_message,
                'current_spi': spi,
                'current_cpi': cpi,
                'note': 'Full trend analysis requires historical data'
            }

        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return {}


# Plugin registration
class EVMPlugin(Plugin):
    """Earned Value Management Plugin"""

    metadata = PluginMetadata(
        name="evm_analyzer",
        version="1.0.0",
        description="Earned Value Management (EVM) analysis and forecasting",
        author="ARGO Development Team",
        capabilities=[PluginCapability.ANALYZER]
    )

    def initialize(self, system):
        """Initialize plugin"""
        self.analyzer = EVMAnalyzer(system=system)
        if hasattr(system, 'plugin_manager'):
            system.plugin_manager.register_analyzer(self.analyzer)
        logger.info("✅ EVM Plugin initialized")
