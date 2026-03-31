import numpy as np
from sklearn.neural_network import MLPClassifier

LABEL_TO_INT = {'action_item': 0, 'decision': 1, 'topic': 2, 'deadline_mention': 3, 'general': 4}
INT_TO_LABEL = {v: k for k, v in LABEL_TO_INT.items()}

class MLPSentenceClassifier:
    """
    5-class sentence classifier. This is the PRIMARY production classifier.
    Architecture: 517 → Dense(256, relu) → Dense(128, relu) → Dense(5, softmax)
    """
    def __init__(self):
        self.model = MLPClassifier(
            hidden_layer_sizes=(256, 128),
            activation='relu',
            solver='adam',
            alpha=0.001,
            batch_size=32,
            learning_rate='adaptive',
            max_iter=500,
            early_stopping=True,
            validation_fraction=0.1,
            random_state=42,
            verbose=False
        )
    
    def train(self, X_train, y_train):
        self.model.fit(X_train, y_train)
    
    def predict(self, X) -> list[str]:
        int_preds = self.model.predict(X)
        return [INT_TO_LABEL[i] for i in int_preds]
    
    def predict_proba(self, X) -> np.ndarray:
        return self.model.predict_proba(X)
