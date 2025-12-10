import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import os

class MineralPredictor:
    def __init__(self, n_estimators=100, random_state=42):
        self.model = RandomForestClassifier(n_estimators=n_estimators, random_state=random_state)
        self.is_trained = False

    def train(self, X, y):
        """
        Trains the model on the provided data.
        """
        print(f"Training Random Forest with {len(X)} samples...")
        self.model.fit(X, y)
        self.is_trained = True

    def predict(self, X):
        if not self.is_trained:
            raise ValueError("Model is not trained yet.")
        return self.model.predict(X)

    def predict_proba(self, X):
        if not self.is_trained:
            raise ValueError("Model is not trained yet.")
        return self.model.predict_proba(X)

    def evaluate(self, X_test, y_test):
        if not self.is_trained:
            raise ValueError("Model is not trained yet.")
        
        y_pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred)
        cm = confusion_matrix(y_test, y_pred)
        
        return {
            "accuracy": acc,
            "report": report,
            "confusion_matrix": cm
        }

    def save(self, filepath):
        joblib.dump(self.model, filepath)
        print(f"Model saved to {filepath}")

    def load(self, filepath):
        if os.path.exists(filepath):
            self.model = joblib.load(filepath)
            self.is_trained = True
            print(f"Model loaded from {filepath}")
        else:
            print(f"Model file {filepath} not found.")
