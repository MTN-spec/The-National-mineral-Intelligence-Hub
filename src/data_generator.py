import numpy as np
import pandas as pd

def generate_synthetic_data(n_samples=1000, random_state=42):
    """
    Generates synthetic GIS/RS data for mineral occurrence prediction.
    
    Features:
    - Clay Index (0-1)
    - Iron Oxide (0-1)
    - Ferrous Iron (0-1)
    - NDVI (Vegetation, -1 to 1)
    - NDWI (Water, -1 to 1)
    - Soil Moisture (0-100)
    - Elevation (0-5000m)
    - Slope (0-90 degrees)
    - Fault Distance (0-10000m)
    
    Target:
    - Mineral Occurrence (0 or 1)
    """
    np.random.seed(random_state)
    
    data = {
        'clay_index': np.random.beta(2, 5, n_samples),
        'iron_oxide': np.random.beta(2, 5, n_samples),
        'ferrous_iron': np.random.beta(2, 5, n_samples),
        'ndvi': np.random.uniform(-0.2, 0.8, n_samples),
        'ndwi': np.random.uniform(-0.5, 0.5, n_samples),
        'soil_moisture': np.random.uniform(10, 60, n_samples),
        'elevation': np.random.uniform(100, 3000, n_samples),
        'slope': np.random.gamma(2, 10, n_samples),
        'fault_distance': np.random.exponential(2000, n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Generate target based on some logical rules (probabilistic)
    # Higher probability if:
    # - High Iron Oxide/Clay (Alteration zones)
    # - Low NDVI (Vegetation stress)
    # - Close to faults
    
    prob = np.zeros(n_samples)
    
    # Base probability
    prob += 0.1
    
    # Mineral indices influence
    prob += df['iron_oxide'] * 0.4
    prob += df['clay_index'] * 0.3
    
    # Structural influence (closer to faults is better)
    prob += np.exp(-df['fault_distance'] / 1000) * 0.3
    
    # Vegetation stress (lower NDVI might indicate mineralization)
    prob += (1 - (df['ndvi'] + 1)/2) * 0.1
    
    # Add some noise
    prob += np.random.normal(0, 0.05, n_samples)
    
    # Sigmoid to clip to 0-1
    prob = 1 / (1 + np.exp(-5 * (prob - 0.5)))
    
    # Threshold for occurrence
    df['mineral_occurrence'] = (prob > np.random.uniform(0, 1, n_samples)).astype(int)
    
    return df

if __name__ == "__main__":
    print("Generating synthetic data...")
    df = generate_synthetic_data(n_samples=100)
    print(df.head())
    print("\nClass distribution:")
    print(df['mineral_occurrence'].value_counts())
