"""Data Agent - Reads and processes CSV files"""

import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ResourceRecord:
    resource_id: str
    resource_name: str
    resource_type: str
    monthly_cost: float
    previous_month_cost: float
    cpu_avg: float
    cpu_p95: float
    memory_avg: float
    memory_p95: float
    storage_growth_pct: float
    latency_ms: float
    availability: float

class DataAgent:
    """Agent responsible for reading and merging CSV datasets"""

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).resolve().parent.parent / "data"
        self.cost_df = None
        self.metrics_df = None
        self.combined_df = None

    def load_datasets(self) -> None:
        """Load all required CSV datasets"""
        # Load cost data
        cost_path = self.data_dir / "cloud_cost.csv"
        self.cost_df = pd.read_csv(cost_path)

        # Load metrics data
        metrics_path = self.data_dir / "resource_metrics.csv"
        self.metrics_df = pd.read_csv(metrics_path)

        # Merge datasets
        self.combined_df = self._merge_dataframes()

    def _merge_dataframes(self) -> pd.DataFrame:
        """Merge cost data with metrics data on resource_id"""
        merged = self.cost_df.merge(
            self.metrics_df,
            on='resource_id',
            how='left'
        )
        return merged

    def get_all_records(self) -> List[Dict]:
        """Return all records as list of dictionaries"""
        if self.combined_df is None:
            self.load_datasets()

        return self.combined_df.to_dict('records')

    def get_resource_record(self, resource_id: str) -> Optional[Dict]:
        """Get a single resource record by ID"""
        if self.combined_df is None:
            self.load_datasets()

        record = self.combined_df[self.combined_df['resource_id'] == resource_id]
        if len(record) > 0:
            return record.iloc[0].to_dict()
        return None

    def get_mock_data_samples(self, n: int = 5) -> List[Dict]:
        """Return random sample of records"""
        import random
        if self.combined_df is None:
            self.load_datasets()

        sample = self.combined_df.sample(n=min(n, len(self.combined_df)))
        return sample.to_dict('records')