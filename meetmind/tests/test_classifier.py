"""
Tests for ML classifiers — feature extraction, model loading, predictions.
"""

import os
import sys
import pytest
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestFeatureExtraction:
    """Tests for features.py"""

    def test_feature_shape(self):
        """Feature extraction produces (N, 517) output."""
        from ml.classifier.features import extract_features
        sentences = ["Please send the report by Friday.", "That sounds good."]
        features = extract_features(sentences, training=False)
        assert features.shape == (2, 517), f"Expected (2, 517), got {features.shape}"

    def test_single_sentence(self):
        """Single sentence produces (1, 517) output."""
        from ml.classifier.features import extract_features
        features = extract_features(["Hello world"], training=False)
        assert features.shape == (1, 517)

    def test_modal_verb_detection(self):
        """Sentences with modal verbs have dim 512 = 1."""
        from ml.classifier.features import extract_features
        features = extract_features(["You should complete the task"], training=False)
        assert features[0, 512] == 1.0

    def test_deadline_detection(self):
        """Sentences with deadline words have dim 515 = 1."""
        from ml.classifier.features import extract_features
        features = extract_features(["Submit by Friday"], training=False)
        assert features[0, 515] == 1.0


class TestVectorizer:
    """Tests for TF-IDF vectorizer loading."""

    def test_vectorizer_exists(self):
        """Vectorizer .pkl file exists after training."""
        path = os.path.join('ml', 'classifier', 'models', 'tfidf_vectorizer.pkl')
        assert os.path.exists(path), f"Vectorizer not found at {path}"

    def test_vectorizer_loads(self):
        """Vectorizer can be loaded from disk."""
        from ml.classifier.features import load_vectorizer
        vec = load_vectorizer()
        assert vec is not None


class TestModels:
    """Tests for trained model loading and prediction."""

    def test_models_exist(self):
        """All model .pkl files exist."""
        models_dir = os.path.join('ml', 'classifier', 'models')
        for name in ['perceptron_classifier.pkl', 'knn_classifier.pkl', 'mlp_classifier.pkl']:
            path = os.path.join(models_dir, name)
            assert os.path.exists(path), f"Model not found: {path}"

    def test_mlp_predict(self):
        """MLP model returns valid label strings."""
        import joblib
        from ml.classifier.features import extract_features
        from ml.classifier.mlp_model import INT_TO_LABEL

        model = joblib.load('ml/classifier/models/mlp_classifier.pkl')
        features = extract_features(["Raj, please send the report by Friday."], training=False)
        # Wrapper .predict() returns label strings directly
        labels = model.predict(features)
        assert labels[0] in INT_TO_LABEL.values()

    def test_mlp_predict_proba(self):
        """MLP predict_proba returns valid probabilities."""
        import joblib
        from ml.classifier.features import extract_features

        model = joblib.load('ml/classifier/models/mlp_classifier.pkl')
        features = extract_features(["Let's discuss the budget"], training=False)
        proba = model.predict_proba(features)
        assert proba.shape[1] == 5
        assert abs(proba.sum() - 1.0) < 0.01
