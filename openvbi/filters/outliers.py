from typing import Any

import numpy as np
import pandas as pd
import geopandas as gpd
from datetime import datetime as dt, timezone

from sklearn.experimental import enable_iterative_imputer  # this enables the sklearn experimental feature
from sklearn.impute import IterativeImputer
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from scipy.ndimage import uniform_filter1d

from openvbi import version
from openvbi.filters import Filter
import openvbi.core.metadata as md

class Outliers(Filter):
    def __init__(self):
        self._params: dict = {
            'thresholds': [99, 98, 98],
            'imputer_iterations': 15,
            'imputer_random': 42,
            'smoother_width': 50
        }
        self._smoothed_depth = pd.Series()
        self._outliers_flags = pd.Series()
        super().__init__()

    @property
    def params(self) -> dict[str,Any]:
        return self._params
    
    @property
    def smoothed(self) -> pd.Series:
        return self._smoothed_depth
    
    @property
    def outliers(self) -> pd.Series:
        return self._outliers_flags
    
    def _execute(self, dataset: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        self._n_inputs = dataset.shape[0]
        self._outliers_flags: pd.Series = pd.Series(False, index=dataset.index, dtype=bool)
        self._smoothed_depth = pd.Series(np.nan, index=dataset.index, dtype=float)
        
        processed_data = dataset[["lat", "lon", "z"]].copy()
        processed_data = self._detect_outliers(processed_data, self._params['thresholds'][0])
        processed_data = self._detect_outliers(processed_data, self._params['thresholds'][1])
        self._detect_outliers(processed_data, self._params['thresholds'][2], compute_smoothed=True)
        
        return dataset[~self._outliers_flags]

    def _metadata(self, meta: md.Metadata) -> None:
        n_outputs: int = self._n_inputs - self._outliers_flags.sum()
        meta.addProcessingAction(md.ProcessingType.ALGORITHM, dt.now(tz=timezone.utc),
                                 name='Outlier Removal (MICE)',
                                 source='OpenVBI',
                                 version=version(),
                                 parameters=self.params,
                                 comment=f'After filtering, total {n_outputs} points selected from {self._n_inputs}.')

    def _detect_outliers(self, data: gpd.GeoDataFrame, threshold_percentile: float,
                         compute_smoothed: bool = False) -> gpd.GeoDataFrame:
        # Normalize data
        scaler = StandardScaler()
        data_scaled = scaler.fit_transform(data)
        assert scaler.scale_ is not None and scaler.mean_ is not None
        
        # Use MICE algorithm for Predictive Mean Matching Imputation
        imputer = IterativeImputer(
            estimator=LinearRegression(),
            max_iter=self._params['imputer_iterations'],
            random_state=self._params['imputer_random'],
            sample_posterior=False
        )
        data_imputed = imputer.fit_transform(data_scaled)
        
        # Smooth the imputed depth values
        smoothed_depth = uniform_filter1d(data_imputed[:, 2], size=self._params['smoother_width'])
        
        # Calculate residuals and detect outliers
        residuals = np.abs(data_scaled[:, 2] - smoothed_depth)
        threshold = np.percentile(residuals, threshold_percentile)
        outliers = residuals > threshold
        self._outliers_flags[data.index[outliers]] = True
        
        # Denormalize smoothed imputed depth
        smoothed_depth_denorm = smoothed_depth * scaler.scale_[2] + scaler.mean_[2]
        if compute_smoothed:
            # Create a full-length smoothed depth array, filling with NaN for removed rows
            self._smoothed_depth[data.index] = smoothed_depth_denorm

        # Remove outliers from the current dataset for the next iteration
        return data[~outliers]
