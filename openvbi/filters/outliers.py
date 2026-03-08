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
        super().__init__()

    @property
    def params(self) -> dict[str,Any]:
        return self._params
    
    def _execute(self, dataset: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        self.n_inputs = dataset.shape[0]
        dataset['Outlier'] = False
        processed_data = dataset[["lat", "lon", "z"]]
        scaler = StandardScaler()
        # Pass 1: Lenient threshold (99th percentile)
        filtered_data_1 = self._detect_outliers(
            processed_data.copy(),
            scaler,
            threshold_percentile=self._params['thresholds'][0],
            original_gdf=dataset
        )
        assert isinstance(filtered_data_1, gpd.GeoDataFrame)

        # Pass 2: Moderate threshold (98th percentile)
        filtered_data_2 = self._detect_outliers(
            filtered_data_1.copy(),
            scaler,
            threshold_percentile=self._params['thresholds'][1],
            original_gdf=dataset
        )
        assert isinstance(filtered_data_2, gpd.GeoDataFrame)

        # Pass 3: Final threshold (98th percentile, return smoothed depth)
        final_smoothed_depth = self._detect_outliers(
            filtered_data_2.copy(),
            scaler,
            threshold_percentile=self._params['thresholds'][2],
            original_gdf=dataset,
            return_smoothed=True
        )
        assert isinstance(final_smoothed_depth, pd.Series)
        self._outliers_flags = dataset['Outlier']
        self._smoothed_depths = final_smoothed_depth
        dataset.drop(columns='Outlier')
        return dataset[self._outliers_flags]

    def _metadata(self, meta: md.Metadata) -> None:
        n_outputs: int = self._outliers_flags.sum()
        meta.addProcessingAction(md.ProcessingType.ALGORITHM, dt.now(tz=timezone.utc),
                                 name='Outlier Removal (MICE)',
                                 source='OpenVBI',
                                 version=version(),
                                 parameters=self._params,
                                 comment=f'After filtering, total {n_outputs} points selected from {self.n_inputs}.')

    def _detect_outliers(self, data: gpd.GeoDataFrame, scaler: StandardScaler, threshold_percentile:
                        float, original_gdf: gpd.GeoDataFrame, return_smoothed: bool = False) -> pd.Series | gpd.GeoDataFrame:
        # Normalize data
        data_scaled = scaler.fit_transform(data)

        # Use MICE algorithm for Predictive Mean Matching Imputation
        imputer = IterativeImputer(
            estimator=LinearRegression(),
            max_iter=self._params['imputer_iterations'],
            random_state=self._params['imputer_random'],
            sample_posterior=False
        )
        
        # Apply imputation
        data_imputed = imputer.fit_transform(data_scaled)
        
        # Smooth the imputed depth values
        smoothed_depth = uniform_filter1d(data_imputed[:, 2], size=self._params['smoother_width'])
        
        # Calculate residuals and detect outliers
        residuals = np.abs(data_scaled[:, 2] - smoothed_depth)
        threshold = np.percentile(residuals, threshold_percentile)
        outliers = residuals > threshold
        
        # Denormalize smoothed imputed depth
        assert scaler.scale_ and scaler.mean_
        smoothed_depth_denorm = smoothed_depth * scaler.scale_[2] + scaler.mean_[2]
        
        # Update the original GeoDataFrame's `Outlier` column
        original_gdf.loc[data.index[outliers], 'Outlier'] = True

        if return_smoothed:
            # Create a full-length smoothed depth array, filling with NaN for removed rows
            full_smoothed_depth = pd.Series(index=original_gdf.index, dtype=float)
            full_smoothed_depth[data.index] = smoothed_depth_denorm
            return full_smoothed_depth

        # Remove outliers from the current dataset for the next iteration
        return data[~outliers]
