#!/usr/bin/env python3
"""
Script to create a web visualization for cryptocurrency correlation analysis.
"""
import os
import json
import pandas as pd
from pathlib import Path
from flask import Flask, render_template, jsonify, send_from_directory
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("web_visualization.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Directories
ANALYSIS_DIR = Path('analysis_results')
WEB_DIR = Path('web_visualization')
WEB_DIR.mkdir(exist_ok=True)
STATIC_DIR = WEB_DIR / 'static'
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR = WEB_DIR / 'templates'
TEMPLATES_DIR.mkdir(exist_ok=True)

def create_html_template():
    """
    Create HTML template for web visualization.
    """
    logger.info("Creating HTML template...")
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Correlation Analyzer</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <header>
        <h1>Crypto Correlation Analyzer</h1>
        <p>Identifying cryptocurrencies that don't follow the general altcoin market</p>
    </header>
    
    <main>
        <section class="summary">
            <h2>Analysis Summary</h2>
            <div class="summary-cards">
                <div class="card">
                    <h3>Total Coins Analyzed</h3>
                    <p class="big-number" id="totalCoins">-</p>
                </div>
                <div class="card">
                    <h3>Uncorrelated Coins</h3>
                    <p class="big-number" id="uncorrelatedCoins">-</p>
                    <p>Correlation threshold: 0.3</p>
                </div>
                <div class="card">
                    <h3>Price Distance Outliers</h3>
                    <p class="big-number" id="priceDistanceCoins">-</p>
                    <p>Distance threshold: 30%</p>
                </div>
            </div>
        </section>
        
        <section class="charts">
            <h2>Market Average vs. Individual Coins</h2>
            <div class="chart-container">
                <canvas id="marketChart"></canvas>
            </div>
            
            <div class="coin-selector">
                <label for="coinSelect">Select Coin: </label>
                <select id="coinSelect">
                    <option value="">Select a coin...</option>
                </select>
            </div>
            
            <div class="chart-container">
                <canvas id="comparisonChart"></canvas>
            </div>
        </section>
        
        <section class="tables">
            <h2>Detailed Results</h2>
            
            <div class="tab-container">
                <div class="tabs">
                    <button class="tab-button active" data-tab="uncorrelated">Uncorrelated Coins</button>
                    <button class="tab-button" data-tab="price-distance">Price Distance Outliers</button>
                    <button class="tab-button" data-tab="all-coins">All Coins</button>
                </div>
                
                <div class="tab-content active" id="uncorrelated-tab">
                    <table id="uncorrelatedTable">
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Average Correlation</th>
                                <th>Cumulative Return</th>
                            </tr>
                        </thead>
                        <tbody>
                            <!-- Will be populated by JavaScript -->
                        </tbody>
                    </table>
                </div>
                
                <div class="tab-content" id="price-distance-tab">
                    <table id="priceDistanceTable">
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Price Distance</th>
                                <th>Cumulative Return</th>
                                <th>Market Return</th>
                            </tr>
                        </thead>
                        <tbody>
                            <!-- Will be populated by JavaScript -->
                        </tbody>
                    </table>
                </div>
                
                <div class="tab-content" id="all-coins-tab">
                    <table id="allCoinsTable">
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Avg Daily Return</th>
                                <th>Cumulative Return</th>
                                <th>Correlation</th>
                                <th>Price Distance</th>
                            </tr>
                        </thead>
                        <tbody>
                            <!-- Will be populated by JavaScript -->
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
    </main>
    
    <footer>
        <p>Crypto Correlation Analyzer - Data from CoinGecko API</p>
    </footer>
    
    <script src="{{ url_for('static', filename='app.js') }}"></script>
</body>
</html>
"""
    
    with open(TEMPLATES_DIR / 'index.html', 'w') as f:
        f.write(html_content)
    
    logger.info("Successfully created HTML template")

def create_css_file():
    """
    Create CSS file for web visualization.
    """
    logger.info("Creating CSS file...")
    
    css_content = """* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f8f9fa;
}

header {
    background-color: #1a1a2e;
    color: white;
    text-align: center;
    padding: 2rem 1rem;
}

header h1 {
    margin-bottom: 0.5rem;
}

main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem 1rem;
}

section {
    margin-bottom: 3rem;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    padding: 2rem;
}

h2 {
    margin-bottom: 1.5rem;
    color: #1a1a2e;
    border-bottom: 2px solid #e6e6e6;
    padding-bottom: 0.5rem;
}

.summary-cards {
    display: flex;
    flex-wrap: wrap;
    gap: 1.5rem;
    justify-content: space-between;
}

.card {
    flex: 1;
    min-width: 250px;
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.big-number {
    font-size: 2.5rem;
    font-weight: bold;
    color: #16213e;
    margin: 1rem 0;
}

.chart-container {
    margin: 2rem 0;
    height: 400px;
}

.coin-selector {
    text-align: center;
    margin: 1.5rem 0;
}

select {
    padding: 0.5rem 1rem;
    border-radius: 4px;
    border: 1px solid #ddd;
    font-size: 1rem;
    min-width: 200px;
}

.tab-container {
    margin-top: 2rem;
}

.tabs {
    display: flex;
    border-bottom: 1px solid #ddd;
    margin-bottom: 1rem;
}

.tab-button {
    padding: 0.75rem 1.5rem;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1rem;
    color: #555;
}

.tab-button.active {
    color: #16213e;
    border-bottom: 3px solid #16213e;
    font-weight: bold;
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
}

th, td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

th {
    background-color: #f8f9fa;
    font-weight: bold;
}

tr:hover {
    background-color: #f8f9fa;
}

footer {
    text-align: center;
    padding: 2rem;
    background-color: #1a1a2e;
    color: white;
}

@media (max-width: 768px) {
    .summary-cards {
        flex-direction: column;
    }
    
    .tabs {
        flex-direction: column;
    }
    
    .tab-button {
        width: 100%;
        text-align: center;
    }
}
"""
    
    with open(STATIC_DIR / 'styles.css', 'w') as f:
        f.write(css_content)
    
    logger.info("Successfully created CSS file")

def create_js_file():
    """
    Create JavaScript file for web visualization.
    """
    logger.info("Creating JavaScript file...")
    
    js_content = """// Global variables
let comparisonData = null;
let uncorrelatedCoins = null;
let priceDistanceCoins = null;
let averageReturns = null;
let marketChart = null;
let comparisonChart = null;

// Fetch all data when page loads
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Fetch all required data
        comparisonData = await fetchJSON('/api/comparison-data');
        uncorrelatedCoins = await fetchJSON('/api/uncorrelated-coins');
        priceDistanceCoins = await fetchJSON('/api/price-distance-coins');
        averageReturns = await fetchJSON('/api/average-returns');
        
        // Update summary numbers
        updateSummaryNumbers();
        
        // Populate coin selector
        populateCoinSelector();
        
        // Initialize charts
        initializeMarketChart();
        initializeComparisonChart();
        
        // Populate tables
        populateUncorrelatedTable();
        populatePriceDistanceTable();
        populateAllCoinsTable();
        
        // Set up tab switching
        setupTabs();
        
    } catch (error) {
        console.error('Error loading data:', error);
        alert('Failed to load data. Please check the console for details.');
    }
});

// Fetch JSON data from API
async function fetchJSON(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

// Update summary numbers
function updateSummaryNumbers() {
    document.getElementById('totalCoins').textContent = Object.keys(averageReturns).length;
    document.getElementById('uncorrelatedCoins').textContent = uncorrelatedCoins.length;
    document.getElementById('priceDistanceCoins').textContent = priceDistanceCoins.length;
}

// Populate coin selector dropdown
function populateCoinSelector() {
    const select = document.getElementById('coinSelect');
    
    // Add all price distance outlier coins
    priceDistanceCoins.forEach(coin => {
        const option = document.createElement('option');
        option.value = coin.symbol;
        option.textContent = coin.symbol;
        select.appendChild(option);
    });
    
    // Add event listener for coin selection
    select.addEventListener('change', updateComparisonChart);
}

// Initialize market average chart
function initializeMarketChart() {
    const ctx = document.getElementById('marketChart').getContext('2d');
    
    marketChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: comparisonData.dates,
            datasets: [{
                label: 'Market Average',
                data: comparisonData.market_avg,
                borderColor: '#16213e',
                backgroundColor: 'rgba(22, 33, 62, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Market Average Cumulative Return',
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Cumulative Return'
                    },
                    ticks: {
                        callback: function(value) {
                            return (value * 100).toFixed(2) + '%';
                        }
                    }
                }
            }
        }
    });
}

// Initialize comparison chart
function initializeComparisonChart() {
    const ctx = document.getElementById('comparisonChart').getContext('2d');
    
    comparisonChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: comparisonData.dates,
            datasets: [{
                label: 'Market Average',
                data: comparisonData.market_avg,
                borderColor: '#16213e',
                backgroundColor: 'rgba(22, 33, 62, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Coin vs Market Comparison',
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Cumulative Return'
                    },
                    ticks: {
                        callback: function(value) {
                            return (value * 100).toFixed(2) + '%';
                        }
                    }
                }
            }
        }
    });
}

// Update comparison chart when coin is selected
function updateComparisonChart() {
    const select = document.getElementById('coinSelect');
    const selectedCoin = select.value;
    
    if (!selectedCoin) {
        // If no coin selected, show only market average
        comparisonChart.data.datasets = [{
            label: 'Market Average',
            data: comparisonData.market_avg,
            borderColor: '#16213e',
            backgroundColor: 'rgba(22, 33, 62, 0.1)',
            borderWidth: 2,
            fill: false,
            tension: 0.1
        }];
    } else {
        // If coin selected, show both market average and selected coin
        const coinData = comparisonData.coins[selectedCoin];
        
        comparisonChart.data.datasets = [
            {
                label: 'Market Average',
                data: comparisonData.market_avg,
                borderColor: '#16213e',
                backgroundColor: 'rgba(22, 33, 62, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.1
            },
            {
                label: selectedCoin,
                data: coinData.data,
                borderColor: '#e94560',
                backgroundColor: 'rgba(233, 69, 96, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.1
            }
        ];
        
        comparisonChart.options.plugins.title.text = `${selectedCoin} vs Market Comparison`;
    }
    
    comparisonChart.update();
}

// Populate uncorrelated coins table
function populateUncorrelatedTable() {
    const tbody = document.querySelector('#uncorrelatedTable tbody');
    tbody.innerHTML = '';
    
    uncorrelatedCoins.forEach(coin => {
        const tr = document.createElement('tr');
        
        tr.innerHTML = `
            <td>${coin.symbol}</td>
            <td>${coin.avg_correlation.toFixed(4)}</td>
            <td>${(averageReturns[coin.symbol]?.cumulative_return * 100).toFixed(2)}%</td>
        `;
        
        tbody.appendChild(tr);
    });
}

// Populate price distance coins table
function populatePriceDistanceTable() {
    const tbody = document.querySelector('#priceDistanceTable tbody');
    tbody.innerHTML = '';
    
    priceDistanceCoins.forEach(coin => {
        const tr = document.createElement('tr');
        
        tr.innerHTML = `
            <td>${coin.symbol}</td>
            <td>${(coin.price_distance * 100).toFixed(2)}%</td>
            <td>${(coin.cumulative_return * 100).toFixed(2)}%</td>
            <td>${(coin.market_return * 100).toFixed(2)}%</td>
        `;
        
        tbody.appendChild(tr);
    });
}

// Populate all coins table
function populateAllCoinsTable() {
    const tbody = document.querySelector('#allCoinsTable tbody');
    tbody.innerHTML = '';
    
    Object.entries(averageReturns).forEach(([symbol, data]) => {
        const tr = document.createElement('tr');
        
        // Find correlation data for this coin
        const correlationData = uncorrelatedCoins.find(c => c.symbol === symbol);
        const correlation = correlationData ? correlationData.avg_correlation : '-';
        
        // Find price distance data for this coin
        const distanceData = priceDistanceCoins.find(c => c.symbol === symbol);
        const priceDistance = distanceData ? distanceData.price_distance : '-';
        
        tr.innerHTML = `
            <td>${symbol}</td>
            <td>${(data.avg_daily_return * 100).toFixed(4)}%</td>
            <td>${(data.cumulative_return * 100).toFixed(2)}%</td>
            <td>${typeof correlation === 'number' ? correlation.toFixed(4) : correlation}</td>
            <td>${typeof priceDistance === 'number' ? (priceDistance * 100).toFixed(2) + '%' : priceDistance}</td>
        `;
        
        tbody.appendChild(tr);
    });
}

// Set up tab switching
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });
}
"""
    
    with open(STATIC_DIR / 'app.js', 'w') as f:
        f.write(js_content)
    
    logger.info("Successfully created JavaScript file")

def create_flask_app():
    """
    Create Flask application for web visualization.
    """
    logger.info("Creating Flask application...")
    
    app_content = """#!/usr/bin/env python3
"""
    app_content += '''
import os
import json
import pandas as pd
from flask import Flask, render_template, jsonify, send_from_directory
from pathlib import Path

# Directories
ANALYSIS_DIR = Path('analysis_results')

# Create Flask app
app = Flask(__name__, 
            template_folder=str(Path('web_visualization/templates')),
            static_folder=str(Path('web_visualization/static')))

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/comparison-data')
def get_comparison_data():
    """Return comparison data for visualization."""
    try:
        with open(ANALYSIS_DIR / 'comparison_data.json', 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({'error': 'Comparison data not found'}), 404

@app.route('/api/uncorrelated-coins')
def get_uncorrelated_coins():
    """Return uncorrelated coins data."""
    try:
        df = pd.read_csv(ANALYSIS_DIR / 'uncorrelated_coins.csv')
        return jsonify(df.to_dict('records'))
    except FileNotFoundError:
        return jsonify({'error': 'Uncorrelated coins data not found'}), 404

@app.route('/api/price-distance-coins')
def get_price_distance_coins():
    """Return price distance coins data."""
    try:
        df = pd.read_csv(ANALYSIS_DIR / 'out_of_threshold_coins.csv')
        return jsonify(df.to_dict('records'))
    except FileNotFoundError:
        return jsonify({'error': 'Price distance coins data not found'}), 404

@app.route('/api/average-returns')
def get_average_returns():
    """Return average returns data."""
    try:
        df = pd.read_csv(ANALYSIS_DIR / 'average_returns.csv')
        # Convert to dictionary with symbol as key
        data = {row['symbol']: row for _, row in df.iterrows()}
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({'error': 'Average returns data not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
'''
    
    with open(WEB_DIR / 'app.py', 'w') as f:
        f.write(app_content)
    
    logger.info("Successfully created Flask application")

def create_web_visualization():
    """
    Create all files for web visualization.
    """
    logger.info("Creating web visualization files...")
    
    # Create directories
    WEB_DIR.mkdir(exist_ok=True)
    STATIC_DIR.mkdir(exist_ok=True)
    TEMPLATES_DIR.mkdir(exist_ok=True)
    
    # Create files
    create_html_template()
    create_css_file()
    create_js_file()
    create_flask_app()
    
    logger.info("Web visualization files created successfully")

if __name__ == "__main__":
    logger.info("Starting web visualization creation...")
    create_web_visualization()
    logger.info("Web visualization creation completed successfully")
