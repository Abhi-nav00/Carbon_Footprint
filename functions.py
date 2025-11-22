import json
import logging
from typing import Dict, Tuple, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CarbonCalculator:
    def __init__(self, coefficients_path: str = 'coefficients.json'):
        with open(coefficients_path, 'r') as f:
            self.coefs = json.load(f)
    
    def calc_electricity(self, kwh: float, renewable_pct: float = 0) -> Tuple[float, Dict]:
        """Calculate electricity emissions with optional renewable percentage"""
        base_emissions = kwh * self.coefs['electricity']['value']
        # Reduce emissions based on renewable percentage
        adjusted_emissions = base_emissions * (1 - renewable_pct / 100)
        
        breakdown = {
            'category': 'electricity',
            'value': adjusted_emissions,
            'units': 'kgCO2e',
            'details': f'{kwh} kWh × {self.coefs["electricity"]["value"]} kgCO2e/kWh'
        }
        logger.info(f"Electricity: {kwh} kWh → {adjusted_emissions:.1f} kgCO2e")
        return adjusted_emissions, breakdown
    
    def calc_natural_gas(self, volume: float, unit: str = 'm3') -> Tuple[float, Dict]:
        """Calculate natural gas emissions"""
        if unit == 'therms':
            coef = self.coefs['natural_gas']['value']
        else:  # m3
            coef = self.coefs['natural_gas_m3']['value']
        
        emissions = volume * coef
        breakdown = {
            'category': 'natural_gas',
            'value': emissions,
            'units': 'kgCO2e',
            'details': f'{volume} {unit} × {coef} kgCO2e/{unit}'
        }
        logger.info(f"Natural Gas: {volume} {unit} → {emissions:.1f} kgCO2e")
        return emissions, breakdown
    
    def calc_heating_oil(self, litres: float) -> Tuple[float, Dict]:
        """Calculate heating oil emissions"""
        emissions = litres * self.coefs['heating_oil']['value']
        breakdown = {
            'category': 'heating_oil',
            'value': emissions,
            'units': 'kgCO2e',
            'details': f'{litres} L × {self.coefs["heating_oil"]["value"]} kgCO2e/L'
        }
        return emissions, breakdown
    
    def calc_lpg(self, litres: float) -> Tuple[float, Dict]:
        """Calculate LPG emissions"""
        emissions = litres * self.coefs['lpg']['value']
        breakdown = {
            'category': 'lpg',
            'value': emissions,
            'units': 'kgCO2e',
            'details': f'{litres} L × {self.coefs["lpg"]["value"]} kgCO2e/L'
        }
        return emissions, breakdown
    
    def calc_car(self, distance_km: float, fuel_efficiency: float, fuel_type: str) -> Tuple[float, Dict]:
        """Calculate car emissions based on distance, fuel efficiency, and fuel type"""
        # Convert fuel efficiency to L/100km if needed
        if fuel_efficiency > 20:  # Assume it's in mpg if > 20
            fuel_efficiency = 235.21 / fuel_efficiency  # Convert mpg to L/100km
        
        # Calculate fuel consumption
        fuel_consumed = (fuel_efficiency / 100) * distance_km
        
        # Get appropriate coefficient
        if fuel_type.lower() == 'diesel':
            coef = self.coefs['car_diesel']['value']
        else:  # petrol/gasoline
            coef = self.coefs['car_petrol']['value']
        
        emissions = fuel_consumed * coef
        breakdown = {
            'category': 'car',
            'value': emissions,
            'units': 'kgCO2e',
            'details': f'{distance_km} km × {fuel_efficiency} L/100km × {coef} kgCO2e/L'
        }
        return emissions, breakdown
    
    def calc_bus(self, distance_km: float) -> Tuple[float, Dict]:
        """Calculate bus emissions"""
        emissions = distance_km * self.coefs['bus']['value']
        breakdown = {
            'category': 'bus',
            'value': emissions,
            'units': 'kgCO2e',
            'details': f'{distance_km} km × {self.coefs["bus"]["value"]} kgCO2e/km'
        }
        return emissions, breakdown
    
    def calc_train(self, distance_km: float) -> Tuple[float, Dict]:
        """Calculate train emissions"""
        emissions = distance_km * self.coefs['train']['value']
        breakdown = {
            'category': 'train',
            'value': emissions,
            'units': 'kgCO2e',
            'details': f'{distance_km} km × {self.coefs["train"]["value"]} kgCO2e/km'
        }
        return emissions, breakdown
    
    def calc_flights(self, short_count: int, long_count: int) -> Tuple[float, Dict]:
        """Calculate flight emissions"""
        # Average distances: short=500km, long=2500km
        short_km = short_count * 500
        long_km = long_count * 2500
        
        short_emissions = short_km * self.coefs['short_flight']['value']
        long_emissions = long_km * self.coefs['long_flight']['value']
        total_emissions = short_emissions + long_emissions
        
        breakdown = {
            'category': 'flights',
            'value': total_emissions,
            'units': 'kgCO2e',
            'details': f'{short_count} short + {long_count} long flights'
        }
        return total_emissions, breakdown
    
    def calc_diet(self, diet_type: str) -> Tuple[float, Dict]:
        """Calculate diet emissions based on diet type"""
        coef_key = f'diet_{diet_type.lower()}'
        daily_emissions = self.coefs[coef_key]['value']
        annual_emissions = daily_emissions * 365
        
        breakdown = {
            'category': 'diet',
            'value': annual_emissions,
            'units': 'kgCO2e',
            'details': f'{diet_type} diet × {daily_emissions} kgCO2e/day × 365 days'
        }
        return annual_emissions, breakdown
    
    def calc_waste(self, kg: float, recycling_rate_pct: float) -> Tuple[float, Dict]:
        """Calculate waste emissions considering recycling"""
        landfill_kg = kg * (1 - recycling_rate_pct / 100)
        recycled_kg = kg * (recycling_rate_pct / 100)
        
        landfill_emissions = landfill_kg * self.coefs['waste_landfill']['value']
        recycling_savings = recycled_kg * abs(self.coefs['waste_recycled']['value'])
        
        net_emissions = landfill_emissions - recycling_savings
        
        breakdown = {
            'category': 'waste',
            'value': net_emissions,
            'units': 'kgCO2e',
            'details': f'{landfill_kg} kg landfill + {recycled_kg} kg recycled'
        }
        return net_emissions, breakdown
    
    def calculate_total(self, inputs: Dict) -> Dict[str, Any]:
        """Calculate total carbon footprint from all inputs"""
        breakdowns = []
        total = 0
        
        # Energy calculations
        if inputs.get('electricity_kwh'):
            emissions, breakdown = self.calc_electricity(
                inputs['electricity_kwh'], 
                inputs.get('renewable_pct', 0)
            )
            total += emissions
            breakdowns.append(breakdown)
        
        if inputs.get('natural_gas_volume'):
            emissions, breakdown = self.calc_natural_gas(
                inputs['natural_gas_volume'],
                inputs.get('natural_gas_unit', 'm3')
            )
            total += emissions
            breakdowns.append(breakdown)
        
        if inputs.get('heating_oil_l'):
            emissions, breakdown = self.calc_heating_oil(inputs['heating_oil_l'])
            total += emissions
            breakdowns.append(breakdown)
        
        if inputs.get('lpg_l'):
            emissions, breakdown = self.calc_lpg(inputs['lpg_l'])
            total += emissions
            breakdowns.append(breakdown)
        
        # Transport calculations
        if inputs.get('car_km') and inputs.get('car_fuel_efficiency'):
            emissions, breakdown = self.calc_car(
                inputs['car_km'],
                inputs['car_fuel_efficiency'],
                inputs.get('car_fuel_type', 'petrol')
            )
            total += emissions
            breakdowns.append(breakdown)
        
        if inputs.get('bus_km'):
            emissions, breakdown = self.calc_bus(inputs['bus_km'])
            total += emissions
            breakdowns.append(breakdown)
        
        if inputs.get('train_km'):
            emissions, breakdown = self.calc_train(inputs['train_km'])
            total += emissions
            breakdowns.append(breakdown)
        
        if inputs.get('short_flights') or inputs.get('long_flights'):
            emissions, breakdown = self.calc_flights(
                inputs.get('short_flights', 0),
                inputs.get('long_flights', 0)
            )
            total += emissions
            breakdowns.append(breakdown)
        
        # Diet calculation
        if inputs.get('diet'):
            emissions, breakdown = self.calc_diet(inputs['diet'])
            total += emissions
            breakdowns.append(breakdown)
        
        # Waste calculation
        if inputs.get('waste_kg'):
            emissions, breakdown = self.calc_waste(
                inputs['waste_kg'],
                inputs.get('recycling_rate_pct', 0)
            )
            total += emissions
            breakdowns.append(breakdown)
        
        # Per person calculation
        household_size = inputs.get('household_size', 1)
        per_person = total / household_size
        
        return {
            'total_kg_co2e': total,
            'per_person_kg': per_person,
            'breakdown': breakdowns,
            'household_size': household_size
        }