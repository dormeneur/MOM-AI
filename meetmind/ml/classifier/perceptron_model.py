from sklearn.linear_model import Perceptron

class PerceptronClassifier:
    """
    Binary classifier: action_item (1) vs not_action_item (0)
    Architecture: Single-layer perceptron with hinge loss
    Purpose: Baseline. Demonstrates linear decision boundary limitations.
    """
    def __init__(self):
        self.model = Perceptron(
            max_iter=1000,
            tol=1e-3,
            random_state=42,
            class_weight='balanced'
        )
    
    def train(self, X_train, y_train):
        y_binary = (y_train == 0).astype(int)
        self.model.fit(X_train, y_binary)
    
    def predict(self, X):
        return self.model.predict(X)
