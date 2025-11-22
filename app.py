from flask import Flask, render_template, request, jsonify, send_from_directory
import json
from functions import CarbonCalculator
from ml_model import CarbonMLModel
import logging
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Initialize calculator and ML model
calculator = CarbonCalculator()
ml_model = CarbonMLModel()
ml_model.load_model()  # Try to load pre-trained model

# Load averages data
with open('averages.json', 'r') as f:
    averages_data = json.load(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results')
def results():
    return render_template('results.html')

@app.route('/api/calc', methods=['POST'])
def calculate_footprint():
    try:
        data = request.get_json()
        
        # Calculate deterministic footprint
        result = calculator.calculate_total(data)
        
        # Get region average
        country = data.get('country', 'United States')
        region_avg = averages_data.get(country, {}).get('average_per_person_kgco2e', 8000)
        
        # Calculate comparison
        user_per_person = result['per_person_kg']
        diff = user_per_person - region_avg
        percent_diff = (diff / region_avg) * 100 if region_avg else 0
        
        # ML prediction
        ml_prediction = None
        top_features = []
        if ml_model.model:
            try:
                ml_features = ml_model.prepare_features(data)
                ml_prediction = ml_model.predict_footprint(ml_features)
                top_features = ml_model.get_feature_importance()[:3]
            except Exception as e:
                logging.error(f"ML prediction failed: {e}")
        
        # Generate recommendations
        recommendations = generate_recommendations(result, data)
        
        response = {
            'total_kg_co2e': round(result['total_kg_co2e'], 1),
            'per_person_kg': round(result['per_person_kg'], 1),
            'breakdown': result['breakdown'],
            'comparison': {
                'region_average': region_avg,
                'diff': round(diff, 1),
                'percent_diff': round(percent_diff, 1),
                'country': country
            },
            'ml_prediction': round(ml_prediction, 1) if ml_prediction else None,
            'top_features': top_features,
            'recommendations': recommendations
        }
        
        return jsonify(response)
    
    except Exception as e:
        logging.error(f"Calculation error: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/coefficients')
def get_coefficients():
    return jsonify(calculator.coefs)

@app.route('/api/averages')
def get_averages():
    return jsonify(averages_data)

# Add explicit static file routes for debugging
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

def generate_recommendations(result, inputs):
    """Generate personalized reduction recommendations"""
    recommendations = []
    
    # Electricity recommendations
    if inputs.get('electricity_kwh', 0) > 2000:
        savings = inputs.get('electricity_kwh', 0) * 0.233 * 0.1  # 10% reduction
        recommendations.append({
            'action': 'Reduce electricity usage by 10% through LED lighting and efficient appliances',
            'savings_kg': round(savings, 1),
            'category': 'electricity'
        })
    
    # Car recommendations
    if inputs.get('car_km', 0) > 5000:
        savings = (inputs.get('car_km', 0) * 0.1) * (inputs.get('car_fuel_efficiency', 8) / 100) * 2.31  # 10% less driving
        recommendations.append({
            'action': 'Reduce car travel by 10% using public transport or carpooling',
            'savings_kg': round(savings, 1),
            'category': 'transport'
        })
    
    # Diet recommendations
    if inputs.get('diet') == 'omnivore':
        current_diet_emissions = 2.5 * 365
        veg_emissions = 1.7 * 365
        savings = current_diet_emissions - veg_emissions
        recommendations.append({
            'action': 'Switch to vegetarian diet 2 days per week',
            'savings_kg': round(savings * 2/7, 1),
            'category': 'diet'
        })
    
    # Waste recommendations
    if inputs.get('recycling_rate_pct', 0) < 50:
        potential_savings = inputs.get('waste_kg', 300) * 0.5 * 0.3  # 30% more recycling
        recommendations.append({
            'action': 'Increase recycling rate by 30%',
            'savings_kg': round(potential_savings, 1),
            'category': 'waste'
        })
    
    # Renewable energy
    if inputs.get('renewable_pct', 0) < 50:
        savings = inputs.get('electricity_kwh', 0) * 0.233 * 0.5  # 50% renewable
        recommendations.append({
            'action': 'Switch to 50% renewable electricity',
            'savings_kg': round(savings, 1),
            'category': 'electricity'
        })
    
    # Flight recommendations
    if inputs.get('short_flights', 0) > 2 or inputs.get('long_flights', 0) > 1:
        savings = 500 * 0.18 * 1  # One less short flight
        recommendations.append({
            'action': 'Reduce one short-haul flight per year',
            'savings_kg': round(savings, 1),
            'category': 'flights'
        })
    
    # Sort by savings and return top 6
    recommendations.sort(key=lambda x: x['savings_kg'], reverse=True)
    return recommendations[:6]

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)