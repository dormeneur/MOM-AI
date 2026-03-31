from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import normalize

class KNNClassifier:
    """
    5-class classifier (all five label types)
    k=5, metric=cosine (normalise vectors first, then use euclidean which == cosine on unit vectors)
    Purpose: Instance-based learning demo. Slower than MLP. Shows curse of dimensionality.
    """
    def __init__(self, k=5):
        self.model = KNeighborsClassifier(
            n_neighbors=k,
            metric='cosine',
            algorithm='brute',
            n_jobs=-1
        )
    
    def train(self, X_train, y_train):
        self.model.fit(X_train, y_train)
    
    def predict(self, X):
        return self.model.predict(X)
    
    def predict_proba(self, X):
        return self.model.predict_proba(X)
