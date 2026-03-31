import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from ml.classifier.features import extract_features
from ml.classifier.perceptron_model import PerceptronClassifier
from ml.classifier.knn_model import KNNClassifier
from ml.classifier.mlp_model import MLPSentenceClassifier, LABEL_TO_INT

def train_all():
    print("Loading data...")
    df = pd.read_csv('data/labelled/sentences.csv')
    df['label_int'] = df['label'].map(LABEL_TO_INT)
    
    X_str = df['sentence'].tolist()
    y = df['label_int'].values
    
    X_train_str, X_test_str, y_train, y_test = train_test_split(X_str, y, test_size=0.2, random_state=42)
    
    print("Extracting features...")
    X_train = extract_features(X_train_str, training=True)
    X_test = extract_features(X_test_str, training=False)
    
    os.makedirs('ml/classifier/models', exist_ok=True)
    
    print("Training Perceptron...")
    perceptron = PerceptronClassifier()
    perceptron.train(X_train, y_train)
    joblib.dump(perceptron, 'ml/classifier/models/perceptron_classifier.pkl')
    
    print("Training KNN...")
    knn = KNNClassifier(k=5)
    knn.train(X_train, y_train)
    joblib.dump(knn, 'ml/classifier/models/knn_classifier.pkl')
    
    print("Training MLP...")
    mlp = MLPSentenceClassifier()
    mlp.train(X_train, y_train)
    joblib.dump(mlp, 'ml/classifier/models/mlp_classifier.pkl')
    
    print("Training complete! Run ml.classifier.evaluate for full metrics.")

if __name__ == '__main__':
    train_all()
