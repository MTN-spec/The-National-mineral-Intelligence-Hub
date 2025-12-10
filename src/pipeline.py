import os
import pandas as pd
from sklearn.model_selection import train_test_split
from .data_generator import generate_synthetic_data
from .model import MineralPredictor

DATA_DIR = os.path.join("mineral_prediction", "data")
PROCESSED_DATA_PATH = os.path.join(DATA_DIR, "processed", "all_data.csv")
MODEL_PATH = os.path.join("mineral_prediction", "model.joblib")

def ensure_dirs():
    os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)  

def load_or_create_data(n_samples=1000, new_batch=False):
    """
    Loads existing data or creates new synthetic data.
    If new_batch is True, generates new data and appends to existing.
    """
    ensure_dirs()
    
    if os.path.exists(PROCESSED_DATA_PATH) and new_batch:
        print("Loading existing data and appending new batch...")
        existing_df = pd.read_csv(PROCESSED_DATA_PATH)
        new_df = generate_synthetic_data(n_samples=n_samples)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df.to_csv(PROCESSED_DATA_PATH, index=False)
        return combined_df
    elif os.path.exists(PROCESSED_DATA_PATH) and not new_batch:
        print("Loading existing data...")
        return pd.read_csv(PROCESSED_DATA_PATH)
    else:
        print("Generating initial data...")
        df = generate_synthetic_data(n_samples=n_samples)
        df.to_csv(PROCESSED_DATA_PATH, index=False)
        return df

def run_pipeline(mode="initial", n_samples=1000):
    """
    Runs the training pipeline.
    mode: 'initial' (train from scratch) or 'update' (add data and retrain)
    """
    print(f"--- Running Pipeline: {mode.upper()} ---")
    
    # 1. Data Handling
    if mode == "update":
        df = load_or_create_data(n_samples=n_samples, new_batch=True)
    else:
        # For initial, we might want to clear old data or just load what's there if we want to restart
        if os.path.exists(PROCESSED_DATA_PATH):
            os.remove(PROCESSED_DATA_PATH)
        df = load_or_create_data(n_samples=n_samples, new_batch=False)
    
    X = df.drop('mineral_occurrence', axis=1)
    y = df['mineral_occurrence']
    
    # 2. Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 3. Model
    predictor = MineralPredictor()
    
    # If updating, we could technically load the old model, but for RF retraining is better
    # predictor.train will retrain a fresh RF on the accumulated dataset
    predictor.train(X_train, y_train)
    
    # 4. Evaluate
    metrics = predictor.evaluate(X_test, y_test)
    print("\nModel Evaluation:")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print("\nClassification Report:")
    print(metrics['report'])
    
    # 5. Save
    predictor.save(MODEL_PATH)
    
    return metrics

if __name__ == "__main__":
    # Example usage
    run_pipeline(mode="initial")
