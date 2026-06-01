"""
services/ml_predictor.py
=========================
ML Predictor — Optional machine-learning crystal system classifier.

Uses a trained scikit-learn model (RandomForest by default) to predict the
crystal system directly from peak features, providing an independent
cross-check alongside the database matching approach.

Model inputs (feature vector per sample)
-----------------------------------------
- Number of detected peaks
- Mean, std, min, max of 2θ positions
- Mean, std of d-spacings
- Mean, std of FWHM
- Estimated crystallite size (Scherrer, mean)
- Mean peak intensity (normalised)

Model output
-------------
Crystal system label: one of CRYSTAL_SYSTEMS in constants.py

Model files (in backend/models/)
----------------------------------
- trained_model.pkl    : fitted classifier pipeline
- scaler.pkl           : StandardScaler for feature normalisation
- label_encoder.pkl    : LabelEncoder mapping string → integer

Usage:
    from services.ml_predictor import MLPredictor

    predictor = MLPredictor()
    if predictor.is_available():
        prediction = predictor.predict(peaks_df)
        print(prediction.crystal_system, prediction.confidence)
"""

import logging
import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class MLPrediction:
    """Result of ML crystal system prediction."""
    crystal_system: str
    confidence: float          # probability [0–1] for the top class
    all_probabilities: dict    # {crystal_system: probability}
    model_available: bool = True


class MLPredictor:
    """
    Loads a pre-trained scikit-learn classifier and predicts crystal system
    from XRD peak features.

    If model files are not present, :meth:`is_available` returns False and
    :meth:`predict` returns a fallback result instead of raising.
    """

    def __init__(self) -> None:
        self._model = None
        self._scaler = None
        self._label_encoder = None
        self._loaded = False
        self._load_model()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Return True if all model files were loaded successfully."""
        return self._loaded

    def predict(self, peaks_df: pd.DataFrame) -> MLPrediction:
        """
        Predict the crystal system from detected XRD peaks.

        Parameters
        ----------
        peaks_df : pd.DataFrame
            Must contain columns: two_theta, intensity, fwhm_deg (optional).

        Returns
        -------
        MLPrediction
            Prediction with crystal system label and confidence score.
            If model is unavailable, returns a placeholder result.
        """
        if not self._loaded:
            logger.warning("ML model not available — returning placeholder prediction.")
            return MLPrediction(
                crystal_system="Unknown",
                confidence=0.0,
                all_probabilities={},
                model_available=False,
            )

        features = self._extract_features(peaks_df)
        features_scaled = self._scaler.transform([features])

        proba = self._model.predict_proba(features_scaled)[0]
        classes = self._label_encoder.classes_
        top_idx = int(np.argmax(proba))

        all_probs = {cls: round(float(p), 4) for cls, p in zip(classes, proba)}

        logger.info(
            "ML prediction: %s (confidence=%.1f%%)",
            classes[top_idx], proba[top_idx] * 100,
        )

        return MLPrediction(
            crystal_system=str(classes[top_idx]),
            confidence=round(float(proba[top_idx]), 4),
            all_probabilities=all_probs,
            model_available=True,
        )

    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        (Re-)train the classifier on new data and save model files.

        This is called from training scripts in datasets/, not at runtime.
        """
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import LabelEncoder, StandardScaler

        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = RandomForestClassifier(n_estimators=200, random_state=42)
        model.fit(X_scaled, y_encoded)

        Path(settings.MODELS_DIR).mkdir(parents=True, exist_ok=True)
        for obj, path in [
            (model, settings.MODEL_PATH),
            (scaler, settings.SCALER_PATH),
            (label_encoder, settings.LABEL_ENCODER_PATH),
        ]:
            with open(path, "wb") as f:
                pickle.dump(obj, f)

        self._model = model
        self._scaler = scaler
        self._label_encoder = label_encoder
        self._loaded = True
        logger.info("ML model trained and saved to %s", settings.MODELS_DIR)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        """Attempt to load pre-trained model files from disk."""
        paths = {
            "model":   settings.MODEL_PATH,
            "scaler":  settings.SCALER_PATH,
            "encoder": settings.LABEL_ENCODER_PATH,
        }
        for name, path in paths.items():
            if not Path(path).exists():
                logger.info("ML model file not found (%s): %s", name, path)
                return

        try:
            with open(settings.MODEL_PATH, "rb") as f:
                self._model = pickle.load(f)
            with open(settings.SCALER_PATH, "rb") as f:
                self._scaler = pickle.load(f)
            with open(settings.LABEL_ENCODER_PATH, "rb") as f:
                self._label_encoder = pickle.load(f)
            self._loaded = True
            logger.info("ML model loaded successfully.")
        except Exception as exc:
            logger.warning("Failed to load ML model: %s", exc)

    def _extract_features(self, peaks_df: pd.DataFrame) -> list[float]:
        """Build feature vector from peaks DataFrame."""
        angles = peaks_df["two_theta"].to_numpy()
        intensities = peaks_df["intensity"].to_numpy()
        fwhm = peaks_df["fwhm_deg"].to_numpy() if "fwhm_deg" in peaks_df.columns else np.zeros(len(angles))
        d_spacings = peaks_df["d_spacing"].to_numpy() if "d_spacing" in peaks_df.columns else np.zeros(len(angles))

        max_int = intensities.max() or 1.0

        features = [
            float(len(angles)),                             # peak count
            float(np.mean(angles)),                         # mean 2θ
            float(np.std(angles)),                          # std 2θ
            float(np.min(angles)),                          # min 2θ
            float(np.max(angles)),                          # max 2θ
            float(np.mean(d_spacings)),                     # mean d
            float(np.std(d_spacings)) if len(d_spacings) > 1 else 0.0,
            float(np.mean(fwhm)),                           # mean FWHM
            float(np.std(fwhm)) if len(fwhm) > 1 else 0.0,
            float(np.mean(intensities) / max_int),          # normalised mean intensity
        ]
        return features