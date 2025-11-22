import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from functions import CarbonCalculator

def test_electricity_calculation():
    calc = CarbonCalculator()
    emissions, breakdown = calc.calc_electricity(1000)
    expected = 1000 * 0.233
    assert abs(emissions - expected) < 0.1
    assert breakdown['category'] == 'electricity'

def test_electricity_with_renewables():
    calc = CarbonCalculator()
    emissions, _ = calc.calc_electricity(1000, 50)  # 50% renewable
    expected = 1000 * 0.233 * 0.5
    assert abs(emissions - expected) < 0.1

def test_natural_gas_calculation():
    calc = CarbonCalculator()
    emissions, breakdown = calc.calc_natural_gas(100, 'm3')
    expected = 100 * 2.21
    assert abs(emissions - expected) < 0.1
    assert breakdown['category'] == 'natural_gas'

def test_car_calculation():
    calc = CarbonCalculator()
    emissions, breakdown = calc.calc_car(100, 8, 'petrol')
    expected_fuel = (8 / 100) * 100  # litres consumed
    expected_emissions = expected_fuel * 2.31
    assert abs(emissions - expected_emissions) < 0.1
    assert breakdown['category'] == 'car'

def test_flight_calculation():
    calc = CarbonCalculator()
    emissions, breakdown = calc.calc_flights(2, 1)
    expected_short = 2 * 500 * 0.18
    expected_long = 1 * 2500 * 0.11
    expected_total = expected_short + expected_long
    assert abs(emissions - expected_total) < 0.1
    assert breakdown['category'] == 'flights'

def test_diet_calculation():
    calc = CarbonCalculator()
    emissions, breakdown = calc.calc_diet('vegan')
    expected = 1.5 * 365
    assert abs(emissions - expected) < 0.1
    assert breakdown['category'] == 'diet'

def test_waste_calculation():
    calc = CarbonCalculator()
    emissions, breakdown = calc.calc_waste(100, 30)  # 100kg waste, 30% recycling
    landfill_emissions = 70 * 0.5
    recycling_savings = 30 * 0.5
    expected = landfill_emissions - recycling_savings
    assert abs(emissions - expected) < 0.1
    assert breakdown['category'] == 'waste'

def test_total_calculation():
    calc = CarbonCalculator()
    inputs = {
        'household_size': 2,
        'electricity_kwh': 2000,
        'car_km': 10000,
        'car_fuel_efficiency': 8,
        'car_fuel_type': 'petrol',
        'diet': 'omnivore',
        'waste_kg': 200,
        'recycling_rate_pct': 25
    }
    
    result = calc.calculate_total(inputs)
    
    assert 'total_kg_co2e' in result
    assert 'per_person_kg' in result
    assert 'breakdown' in result
    assert result['total_kg_co2e'] > 0
    assert result['per_person_kg'] == result['total_kg_co2e'] / 2

def test_integration():
    """Test the complete calculation with sample data"""
    calc = CarbonCalculator()
    sample_inputs = {
        'household_size': 3,
        'country': 'India',
        'electricity_kwh': 3600,
        'natural_gas_m3': 0,
        'heating_oil_l': 0,
        'car_km': 12000,
        'car_fuel_efficiency': 6.5,
        'car_fuel_type': 'petrol',
        'bus_km': 800,
        'train_km': 400,
        'short_flights': 1,
        'long_flights': 0,
        'diet': 'omnivore',
        'waste_kg': 300,
        'recycling_rate_pct': 20
    }
    
    result = calc.calculate_total(sample_inputs)
    
    # Basic validation
    assert result['total_kg_co2e'] > 0
    assert result['per_person_kg'] > 0
    assert len(result['breakdown']) > 0
    
    # Check that per_person calculation is correct
    expected_per_person = result['total_kg_co2e'] / sample_inputs['household_size']
    assert abs(result['per_person_kg'] - expected_per_person) < 0.1

if __name__ == '__main__':
    pytest.main([__file__])