import pandas as pd
import numpy as np
import os
import joblib
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import train_test_split
from ml.classifier.features import extract_features
from ml.classifier.mlp_model import LABEL_TO_INT

def evaluate():
    print("Loading test data...")
    df = pd.read_csv('data/labelled/sentences.csv')
    df['label_int'] = df['label'].map(LABEL_TO_INT)
    
    X_str = df['sentence'].tolist()
    y = df['label_int'].values
    
    _, X_test_str, _, y_test = train_test_split(X_str, y, test_size=0.2, random_state=42)
    X_test = extract_features(X_test_str, training=False)
    
    perceptron = joblib.load('ml/classifier/models/perceptron_classifier.pkl')
    knn = joblib.load('ml/classifier/models/knn_classifier.pkl')
    mlp = joblib.load('ml/classifier/models/mlp_classifier.pkl')
    
    models = {
        'Perceptron': perceptron,
        'KNN (k=5)': knn,
        'MLP': mlp
    }
    
    print("\nModel        Accuracy   Precision   Recall     F1 (Macro)")
    print("-----------  ---------  ----------  ---------  ----------")
    
    os.makedirs('ml/classifier/plots', exist_ok=True)
    f1_scores = {}
    
    for name, model in models.items():
        if name == 'Perceptron':
            y_pred_bin = model.predict(X_test)
            y_true_bin = (y_test == 0).astype(int)
            acc = accuracy_score(y_true_bin, y_pred_bin)
            prec = precision_score(y_true_bin, y_pred_bin, average='macro', zero_division=0)
            rec = recall_score(y_true_bin, y_pred_bin, average='macro', zero_division=0)
            f1 = f1_score(y_true_bin, y_pred_bin, average='macro', zero_division=0)
            
            cm = confusion_matrix(y_true_bin, y_pred_bin)
            disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Not Action', 'Action'])
            disp.plot()
            plt.title(f"Confusion Matrix - {name}")
            plt.savefig(f"ml/classifier/plots/confusion_matrix_perceptron.png")
            plt.close()
            
        else:
            y_pred = model.model.predict(X_test) if name == 'MLP' else model.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, average='macro', zero_division=0)
            rec = recall_score(y_test, y_pred, average='macro', zero_division=0)
            f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)
            
            cm = confusion_matrix(y_test, y_pred, labels=[0,1,2,3,4])
            disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=list(LABEL_TO_INT.keys()))
            disp.plot(xticks_rotation=45)
            plt.title(f"Confusion Matrix - {name}")
            plot_name = name.replace(" ", "_").replace("(", "").replace(")", "").replace("=", "").lower()
            plt.savefig(f"ml/classifier/plots/confusion_matrix_{plot_name}.png")
            plt.close()
            
        f1_scores[name] = f1
        print(f"{name:<12} {acc:<10.2f} {prec:<11.2f} {rec:<10.2f} {f1:<10.2f}")
    
    plt.figure()
    plt.bar(f1_scores.keys(), f1_scores.values(), color=['blue', 'orange', 'green'])
    plt.title('Macro F1 Comparison')
    plt.ylabel('F1 Score')
    plt.ylim(0, 1.1)
    for i, v in enumerate(f1_scores.values()):
        plt.text(i, v + 0.02, f"{v:.2f}", ha='center')
    plt.savefig('ml/classifier/plots/f1_comparison.png')
    plt.close()

if __name__ == '__main__':
    evaluate()
