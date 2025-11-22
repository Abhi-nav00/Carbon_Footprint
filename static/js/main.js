class CarbonCalculatorApp {
    constructor() {
        this.form = document.getElementById('carbon-form');
        this.liveSummary = document.getElementById('live-summary');
        this.totalEstimate = document.getElementById('total-estimate');
        this.perPersonEstimate = document.getElementById('per-person-estimate');
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.setupLiveUpdates();
    }
    
    bindEvents() {
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
            
            // Add input validation
            const numberInputs = this.form.querySelectorAll('input[type="number"]');
            numberInputs.forEach(input => {
                input.addEventListener('blur', () => this.validateInput(input));
            });
        }
    }
    
    setupLiveUpdates() {
        if (!this.form) return;
        
        // Debounce live updates to avoid excessive API calls
        let timeout;
        this.form.addEventListener('input', (e) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                this.updateLiveSummary();
            }, 500);
        });
    }
    
    validateInput(input) {
        const value = parseFloat(input.value);
        const min = parseFloat(input.min) || 0;
        
        if (input.value && value < min) {
            input.value = min;
            this.showValidationMessage(input, `Value must be at least ${min}`);
        }
    }
    
    showValidationMessage(input, message) {
        // Remove existing message
        const existingMessage = input.parentNode.querySelector('.validation-message');
        if (existingMessage) {
            existingMessage.remove();
        }
        
        // Add new message
        const messageEl = document.createElement('div');
        messageEl.className = 'validation-message';
        messageEl.style.color = '#E53E3E';
        messageEl.style.fontSize = '0.875rem';
        messageEl.style.marginTop = '0.25rem';
        messageEl.textContent = message;
        
        input.parentNode.appendChild(messageEl);
        
        // Remove message after 3 seconds
        setTimeout(() => {
            messageEl.remove();
        }, 3000);
    }
    
    async updateLiveSummary() {
        const formData = this.getFormData();
        
        // Only calculate if we have some data
        const hasData = Object.values(formData).some(val => 
            val !== undefined && val !== '' && val !== 0
        );
        
        if (!hasData) {
            this.liveSummary.classList.add('hidden');
            return;
        }
        
        try {
            const response = await fetch('/api/calc', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                const result = await response.json();
                this.displayLiveSummary(result);
            }
        } catch (error) {
            console.error('Error updating live summary:', error);
        }
    }
    
    displayLiveSummary(result) {
        this.totalEstimate.textContent = Math.round(result.total_kg_co2e).toLocaleString();
        this.perPersonEstimate.textContent = Math.round(result.per_person_kg).toLocaleString();
        this.liveSummary.classList.remove('hidden');
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        const submitBtn = this.form.querySelector('.calculate-btn');
        const originalText = submitBtn.textContent;
        
        try {
            submitBtn.textContent = 'Calculating...';
            submitBtn.disabled = true;
            
            const formData = this.getFormData();
            const response = await fetch('/api/calc', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showResults(result);
            } else {
                throw new Error('Calculation failed');
            }
            
        } catch (error) {
            this.showError('Failed to calculate footprint. Please try again.');
            console.error('Calculation error:', error);
        } finally {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    }
    
    getFormData() {
        const formData = new FormData(this.form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            if (value !== '') {
                // Convert numeric values
                if (key !== 'country' && key !== 'diet' && key !== 'car_fuel_type' && key !== 'natural_gas_unit') {
                    value = parseFloat(value);
                }
                data[key] = value;
            }
        }
        
        return data;
    }
    
    showResults(result) {
        // Store results in sessionStorage for results page
        sessionStorage.setItem('carbonResults', JSON.stringify(result));
        
        // Redirect to results page
        window.location.href = '/results';
    }
    
    showError(message) {
        // Remove existing error messages
        const existingErrors = document.querySelectorAll('.error-message');
        existingErrors.forEach(error => error.remove());
        
        // Create error message
        const errorEl = document.createElement('div');
        errorEl.className = 'error-message';
        errorEl.style.cssText = `
            background: #FED7D7;
            color: #C53030;
            padding: 1rem;
            border-radius: 6px;
            margin-bottom: 1rem;
            border: 1px solid #FEB2B2;
        `;
        errorEl.textContent = message;
        
        this.form.insertBefore(errorEl, this.form.firstChild);
        
        // Remove error after 5 seconds
        setTimeout(() => {
            errorEl.remove();
        }, 5000);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CarbonCalculatorApp();
});

// Results page functionality
if (window.location.pathname === '/results') {
    document.addEventListener('DOMContentLoaded', () => {
        const results = JSON.parse(sessionStorage.getItem('carbonResults'));
        if (results) {
            displayResults(results);
        } else {
            window.location.href = '/';
        }
    });
}

function displayResults(result) {
    displayTotalFootprint(result);
    displayComparison(result);
    displayBreakdownChart(result);
    displayComparisonChart(result);
    displayRecommendations(result);
    displayMLInfo(result);
}

function displayTotalFootprint(result) {
    const totalEl = document.getElementById('total-footprint');
    const perPersonEl = document.getElementById('per-person-result');
    
    if (totalEl) {
        totalEl.textContent = Math.round(result.total_kg_co2e).toLocaleString();
    }
    
    if (perPersonEl) {
        perPersonEl.textContent = Math.round(result.per_person_kg).toLocaleString();
    }
}

function displayComparison(result) {
    const comparison = result.comparison;
    const messageEl = document.getElementById('comparison-message');
    
    if (!messageEl) return;
    
    if (comparison.diff < 0) {
        messageEl.className = 'comparison-message comparison-good';
        messageEl.innerHTML = `
            <strong>Nice work!</strong> Your footprint is ${Math.abs(comparison.percent_diff).toFixed(1)}% 
            below the ${comparison.country} average. Keep it up! 🌱
        `;
    } else {
        messageEl.className = 'comparison-message';
        messageEl.innerHTML = `
            Your footprint is ${comparison.percent_diff.toFixed(1)}% above the ${comparison.country} average. 
            Check out the reduction steps below to improve!
        `;
    }
}

function displayBreakdownChart(result) {
    const ctx = document.getElementById('breakdown-chart');
    if (!ctx) return;
    
    const canvasCtx = ctx.getContext('2d');
    
    const categories = result.breakdown.map(item => 
        item.category.replace('_', ' ').toUpperCase()
    );
    const values = result.breakdown.map(item => item.value);
    const backgroundColors = [
        '#2F8F4F', '#4CAF50', '#8BC34A', '#CDDC39', 
        '#FFC107', '#FF9800', '#FF5722', '#795548'
    ];
    
    new Chart(canvasCtx, {
        type: 'doughnut',
        data: {
            labels: categories,
            datasets: [{
                data: values,
                backgroundColor: backgroundColors,
                borderWidth: 2,
                borderColor: '#FFFFFF'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${context.label}: ${value.toLocaleString()} kg (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function displayComparisonChart(result) {
    const ctx = document.getElementById('comparison-chart');
    if (!ctx) return;
    
    const canvasCtx = ctx.getContext('2d');
    const comparison = result.comparison;
    
    new Chart(canvasCtx, {
        type: 'bar',
        data: {
            labels: ['Your Footprint', 'Regional Average'],
            datasets: [{
                data: [result.per_person_kg, comparison.region_average],
                backgroundColor: [
                    result.per_person_kg < comparison.region_average ? '#2F8F4F' : '#E53E3E',
                    '#CBD5E0'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.y.toLocaleString()} kg CO₂e per person`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'kg CO₂e per person/year'
                    }
                }
            }
        }
    });
}

function displayRecommendations(result) {
    const container = document.getElementById('recommendations-list');
    if (!container) return;
    
    if (result.recommendations.length === 0) {
        container.innerHTML = '<p>Great job! Your footprint is already optimized.</p>';
        return;
    }
    
    container.innerHTML = result.recommendations.map(rec => `
        <div class="recommendation-item">
            <div class="recommendation-action">${rec.action}</div>
            <div class="recommendation-savings">Save ~${rec.savings_kg} kg</div>
        </div>
    `).join('');
}

function displayMLInfo(result) {
    const mlPredictionEl = document.getElementById('ml-prediction');
    const topFeaturesEl = document.getElementById('top-features');
    
    if (mlPredictionEl) {
        if (result.ml_prediction) {
            mlPredictionEl.textContent = 
                `Estimated: ${Math.round(result.ml_prediction).toLocaleString()} kg CO₂e/year`;
        } else {
            mlPredictionEl.textContent = 'ML estimate not available';
        }
    }
    
    if (topFeaturesEl) {
        if (result.top_features && result.top_features.length > 0) {
            topFeaturesEl.innerHTML = `
                <strong>Top contributors:</strong> 
                ${result.top_features.map(feat => `${feat[0]} (${(feat[1] * 100).toFixed(1)}%)`).join(', ')}
            `;
        } else {
            topFeaturesEl.textContent = '';
        }
    }
}