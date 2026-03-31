import numpy as np
import re
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer_path = os.path.join(os.path.dirname(__file__), 'models', 'tfidf_vectorizer.pkl')

def extract_features(sentences: list[str], training=False) -> np.ndarray:
    """
    Input:  list of N sentences
    Output: np.ndarray of shape (N, 517)
    
    Feature breakdown:
    - dims 0–511:   TF-IDF vector (max_features=512, sublinear_tf=True, ngram_range=(1,2))
    - dim 512:      has_modal_verb
    - dim 513:      has_person_name
    - dim 514:      is_imperative
    - dim 515:      has_deadline
    - dim 516:      sentence_length_norm
    """
    if training:
        vectorizer = TfidfVectorizer(max_features=512, sublinear_tf=True, ngram_range=(1,2))
        tfidf_features = vectorizer.fit_transform(sentences).toarray()
        if tfidf_features.shape[1] < 512:
            pad = np.zeros((tfidf_features.shape[0], 512 - tfidf_features.shape[1]))
            tfidf_features = np.hstack((tfidf_features, pad))
        
        os.makedirs(os.path.dirname(vectorizer_path), exist_ok=True)
        joblib.dump(vectorizer, vectorizer_path)
    else:
        if not os.path.exists(vectorizer_path):
            raise FileNotFoundError(f"TF-IDF vectoriser not found at {vectorizer_path}. Must train first.")
        vectorizer = joblib.load(vectorizer_path)
        tfidf_features = vectorizer.transform(sentences).toarray()
        if tfidf_features.shape[1] < 512:
            pad = np.zeros((tfidf_features.shape[0], 512 - tfidf_features.shape[1]))
            tfidf_features = np.hstack((tfidf_features, pad))

    manual_features = []
    modals = r'\b(will|shall|should|must|need to|going to)\b'
    deadlines = r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|by|before|until|eod|eow|tomorrow|today|next week)\b'
    verbs = {'let', 'please', 'make', 'do', 'send', 'finish', 'email', 'review', 'create', 'update', 'schedule', 'book', 'call', 'tell', 'ask', 'get', 'give', 'take', 'start', 'stop', 'try', 'use', 'find', 'check', 'write', 'read'}
    
    for s in sentences:
        f1 = 1 if re.search(modals, s, re.IGNORECASE) else 0
        
        tokens = s.split()
        f2 = 0
        if len(tokens) > 1:
            for t in tokens[1:]:
                tc = re.sub(r'[^\w\s]', '', t)
                if tc.istitle():
                    f2 = 1
                    break
                    
        f3 = 0
        if tokens:
            first_word = re.sub(r'[^\w\s]', '', tokens[0]).lower()
            if first_word in verbs:
                f3 = 1
                
        f4 = 1 if re.search(deadlines, s, re.IGNORECASE) else 0
        f5 = min(len(tokens) / 50.0, 1.0)
        
        manual_features.append([f1, f2, f3, f4, f5])
        
    manual_arr = np.array(manual_features)
    final_features = np.hstack((tfidf_features, manual_arr))
    return final_features

def load_vectorizer():
    if not os.path.exists(vectorizer_path):
        raise FileNotFoundError(f"TF-IDF vectoriser not found at {vectorizer_path}. Must train first.")
    return joblib.load(vectorizer_path)
