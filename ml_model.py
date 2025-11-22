import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import json
import os

class CarbonMLModel:
    def __init__(self):
        self.model = None
        self.feature_names = []
        
    def generate_sample_data(self, n_samples=1000):
        """Generate synthetic training data based on realistic patterns"""
        np.random.seed(42)
        
        data = {
            'household_size': np.random.randint(1, 6, n_samples),
            'electricity_kwh': np.random.normal(3000, 1000, n_samples).clip(500, 8000),
            'natural_gas_m3': np.random.normal(2000, 800, n_samples).clip(0, 5000),
            'car_km': np.random.normal(12000, 5000, n_samples).clip(0, 30000),
            'car_fuel_l_per_100km': np.random.normal(8, 2, n_samples).clip(4, 15),
            'bus_km': np.random.exponential(500, n_samples).clip(0, 3000),
            'train_km': np.random.exponential(300, n_samples).clip(0, 2000),
            'short_flights': np.random.poisson(1, n_samples),
            'long_flights': np.random.poisson(0.5, n_samples),
            'diet_code': np.random.choice([0, 1, 2, 3], n_samples, p=[0.6, 0.2, 0.1, 0.1]),  # 0:omnivore, 1:vegetarian, 2:vegan, 3:pescatarian
            'waste_kg': np.random.normal(300, 100, n_samples).clip(100, 600),
            'recycling_rate_pct': np.random.normal(30, 20, n_samples).clip(0, 80)
        }
        
        df = pd.DataFrame(data)
        
        # Calculate target using deterministic functions (simplified)
        targets = []
        for _, row in df.iterrows():
            # Simplified calculation for training data
            electricity = row['electricity_kwh'] * 0.233
            car_fuel = (row['car_km'] * row['car_fuel_l_per_100km'] / 100) * 2.31
            diet_base = [2.5, 1.7, 1.5, 1.9][int(row['diet_code'])] * 365
            total = electricity + car_fuel + diet_base + np.random.normal(1000, 500)
            targets.append(total)
        
        df['total_footprint'] = targets
        return df
    
    def train_model(self, df):
        """Train the ML model"""
        # Prepare features
        feature_cols = [col for col in df.columns if col != 'total_footprint']
        X = df[feature_cols]
        y = df['total_footprint']
        
        self.feature_names = feature_cols
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"Model trained - MSE: {mse:.2f}, R²: {r2:.2f}")
        
        return self.model
    
    def save_model(self, path='model.joblib'):
        """Save trained model"""
        if self.model:
            joblib.dump({
                'model': self.model,
                'feature_names': self.feature_names
            }, path)
            print(f"Model saved to {path}")
    
    def load_model(self, path='model.joblib'):
        """Load trained model"""
        if os.path.exists(path):
            loaded = joblib.load(path)
            self.model = loaded['model']
            self.feature_names = loaded['feature_names']
            print("Model loaded successfully")
        else:
            print("No saved model found")
    
    def predict_footprint(self, features):
        """Predict carbon footprint"""
        if not self.model:
            return None
        
        # Convert features to dataframe with correct columns
        feature_df = pd.DataFrame([features], columns=self.feature_names)
        return self.model.predict(feature_df)[0]
    
    def get_feature_importance(self):
        """Get feature importance scores"""
        if not self.model:
            return None
        
        importance = list(zip(self.feature_names, self.model.feature_importances_))
        return sorted(importance, key=lambda x: x[1], reverse=True)
    
    def prepare_features(self, user_inputs):
        """Prepare user inputs for ML prediction"""
        # Map diet to code
        diet_map = {'omnivore': 0, 'vegetarian': 1, 'vegan': 2, 'pescatarian': 3}
        
        features = {
            'household_size': user_inputs.get('household_size', 1),
            'electricity_kwh': user_inputs.get('electricity_kwh', 0),
            'natural_gas_m3': user_inputs.get('natural_gas_volume', 0) if user_inputs.get('natural_gas_unit') == 'm3' else 0,
            'car_km': user_inputs.get('car_km', 0),
            'car_fuel_l_per_100km': user_inputs.get('car_fuel_efficiency', 8),
            'bus_km': user_inputs.get('bus_km', 0),
            'train_km': user_inputs.get('train_km', 0),
            'short_flights': user_inputs.get('short_flights', 0),
            'long_flights': user_inputs.get('long_flights', 0),
            'diet_code': diet_map.get(user_inputs.get('diet', 'omnivore'), 0),
            'waste_kg': user_inputs.get('waste_kg', 0),
            'recycling_rate_pct': user_inputs.get('recycling_rate_pct', 0)
        }
        
        return features

def train_and_save_model():
    """Convenience function to train and save model"""
    ml_model = CarbonMLModel()
    df = ml_model.generate_sample_data(2000)
    ml_model.train_model(df)
    ml_model.save_model()
    print("Model training completed!")

if __name__ == "__main__":
    train_and_save_model()