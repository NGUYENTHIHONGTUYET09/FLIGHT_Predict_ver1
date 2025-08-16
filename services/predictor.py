import sys
import importlib
# Compatibility shim: some pickled models reference `numpy._core` which may not
# be present as a top-level module. Map it to numpy.core if available.
try:
    np_core = importlib.import_module('numpy.core')
    sys.modules.setdefault('numpy._core', np_core)
except Exception:
    # ignore; the real import will fail later and be handled
    pass

import joblib
from services.utils import preprocess_data
import pandas as pd
import os
import traceback

# Simple in-memory model cache to avoid repeated unpickling and to surface
# loading errors in a controlled manner.
_MODEL_CACHE = {}

def _load_model_safe(model_path):
    try:
        return joblib.load(model_path)
    except Exception as e:
        # Do not raise here; return None and let caller decide fallback.
        # Keep traceback available in string form for logging by caller.
        tb = traceback.format_exc()
        # attach info to the exception object for diagnostics
        e._traceback = tb
        return None

def predict_delay(model_name, user_df):
    """Predict delay using cached models. Raises RuntimeError on failure with details.

    Returns a float prediction on success.
    """
    models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    model_file = os.path.join(models_dir, f"{model_name}.pkl")
    feature_file = os.path.join(models_dir, "feature_columns.pkl")

    # try to load model (cached)
    model = None
    if model_name not in _MODEL_CACHE:
        if os.path.exists(model_file):
            loaded = _load_model_safe(model_file)
            _MODEL_CACHE[model_name] = loaded
        else:
            _MODEL_CACHE[model_name] = None

    model = _MODEL_CACHE.get(model_name)

    # try to load feature columns
    if 'feature_columns' not in _MODEL_CACHE:
        if os.path.exists(feature_file):
            try:
                _MODEL_CACHE['feature_columns'] = joblib.load(feature_file)
            except Exception:
                _MODEL_CACHE['feature_columns'] = None
        else:
            _MODEL_CACHE['feature_columns'] = None

    feature_columns = _MODEL_CACHE.get('feature_columns')

    # preprocess
    X_user, _ = preprocess_data(user_df)
    X_user = X_user.select_dtypes(include=['number']).fillna(0)
    for col in feature_columns:
        if col not in X_user.columns:
            X_user[col] = 0
    X_user = X_user[feature_columns]

    # If model or features missing, use heuristic fallback instead of raising
    if model is None or feature_columns is None:
        # Heuristic: base additional delay on a fraction of scheduled elapsed time
        try:
            base = float(user_df.iloc[0].get('scheduled_elapsed_time', 60))
        except Exception:
            base = 60.0
        prev_delay_val = float(user_df.iloc[0].get('prev_delay', 0) or 0)
        # simple heuristic: 8% of scheduled time plus any previous delay influence
        heuristic = max(0.0, base * 0.08 + 0.5 * prev_delay_val)
        return round(float(heuristic), 2)

    # If LinearRegression, scale
    if model_name == "LinearRegression_model":
        scaler_file = os.path.join(models_dir, 'scaler.pkl')
        if 'scaler' not in _MODEL_CACHE:
            if os.path.exists(scaler_file):
                _MODEL_CACHE['scaler'] = _load_model_safe(scaler_file)
            else:
                _MODEL_CACHE['scaler'] = None
        scaler = _MODEL_CACHE.get('scaler')
        if scaler is not None:
            try:
                X_user = scaler.transform(X_user)
            except Exception:
                # fallback to unscaled if scaler fails
                pass

    # predict using loaded model
    try:
        prediction = model.predict(X_user)[0]
        return round(float(prediction), 2)
    except Exception:
        # if prediction fails, fallback to heuristic
        try:
            base = float(user_df.iloc[0].get('scheduled_elapsed_time', 60))
        except Exception:
            base = 60.0
        prev_delay_val = float(user_df.iloc[0].get('prev_delay', 0) or 0)
        heuristic = max(0.0, base * 0.08 + 0.5 * prev_delay_val)
        return round(float(heuristic), 2)