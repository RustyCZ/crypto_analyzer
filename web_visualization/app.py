#!/usr/bin/env python3

import os
import json
import pandas as pd
from flask import Flask, render_template, jsonify, send_from_directory
from pathlib import Path

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Directories - use os.path for Windows compatibility
parent_dir = os.path.dirname(current_dir)
analysis_dir = os.path.join(parent_dir, 'analysis_results')

# Create sample data if analysis_results directory doesn't exist or is empty
def create_sample_data():
    """Create sample data files for testing if they don't exist."""
    if not os.path.exists(analysis_dir):
        os.makedirs(analysis_dir)
        print(f"Created analysis directory at: {analysis_dir}")
    
    # Check if files exist
    files_exist = (
        os.path.exists(os.path.join(analysis_dir, 'comparison_data.json')) and
        os.path.exists(os.path.join(analysis_dir, 'uncorrelated_coins.csv')) and
        os.path.exists(os.path.join(analysis_dir, 'out_of_threshold_coins.csv')) and
        os.path.exists(os.path.join(analysis_dir, 'average_returns.csv'))
    )
    
    if not files_exist:
        print("Creating sample data files for testing...")
        
        # Sample comparison data
        comparison_data = {
            "dates": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "market_avg": [0.01, 0.02, 0.015],
            "coins": {
                "BTC": {
                    "name": "Bitcoin",
                    "data": [0.02, 0.03, 0.025],
                    "cumulative_return": 0.075,
                    "price_distance": 0.35,
                    "relative_distance": 1.2
                },
                "ETH": {
                    "name": "Ethereum",
                    "data": [0.015, 0.025, 0.02],
                    "cumulative_return": 0.06,
                    "price_distance": 0.32,
                    "relative_distance": 1.1
                }
            }
        }
        
        # Sample uncorrelated coins
        uncorrelated_data = [
            {"symbol": "USDT", "avg_correlation": 0.15, "cumulative_return": 0.001},
            {"symbol": "XRP", "avg_correlation": 0.25, "cumulative_return": 0.12}
        ]
        
        # Sample price distance coins
        price_distance_data = [
            {"symbol": "BTC", "price_distance": 0.35, "cumulative_return": 0.075, "market_return": 0.045},
            {"symbol": "ETH", "price_distance": 0.32, "cumulative_return": 0.06, "market_return": 0.045}
        ]
        
        # Sample average returns
        average_returns_data = [
            {"symbol": "BTC", "avg_daily_return": 0.0025, "std_daily_return": 0.02, 
             "cumulative_return": 0.075, "annualized_return": 0.25, "sharpe_ratio": 1.5},
            {"symbol": "ETH", "avg_daily_return": 0.002, "std_daily_return": 0.025, 
             "cumulative_return": 0.06, "annualized_return": 0.2, "sharpe_ratio": 1.2},
            {"symbol": "USDT", "avg_daily_return": 0.0001, "std_daily_return": 0.001, 
             "cumulative_return": 0.001, "annualized_return": 0.01, "sharpe_ratio": 0.5},
            {"symbol": "XRP", "avg_daily_return": 0.004, "std_daily_return": 0.03, 
             "cumulative_return": 0.12, "annualized_return": 0.3, "sharpe_ratio": 1.3}
        ]
        
        # Save sample data
        with open(os.path.join(analysis_dir, 'comparison_data.json'), 'w') as f:
            json.dump(comparison_data, f, indent=2)
            
        pd.DataFrame(uncorrelated_data).to_csv(os.path.join(analysis_dir, 'uncorrelated_coins.csv'), index=False)
        pd.DataFrame(price_distance_data).to_csv(os.path.join(analysis_dir, 'out_of_threshold_coins.csv'), index=False)
        pd.DataFrame(average_returns_data).to_csv(os.path.join(analysis_dir, 'average_returns.csv'), index=False)
        
        print("Sample data files created successfully.")
    else:
        print(f"Analysis files already exist in: {analysis_dir}")

# Create Flask app with absolute paths
app = Flask(__name__, 
            template_folder=os.path.join(current_dir, 'templates'),
            static_folder=os.path.join(current_dir, 'static'))

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/comparison-data')
def get_comparison_data():
    """Return comparison data for visualization."""
    try:
        comparison_file = os.path.join(analysis_dir, 'comparison_data.json')
        if not os.path.exists(comparison_file):
            return jsonify({'error': f'Comparison data not found at {comparison_file}'}), 404
            
        with open(comparison_file, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': f'Error loading comparison data: {str(e)}'}), 500

@app.route('/api/uncorrelated-coins')
def get_uncorrelated_coins():
    """Return uncorrelated coins data."""
    try:
        uncorrelated_file = os.path.join(analysis_dir, 'uncorrelated_coins.csv')
        if not os.path.exists(uncorrelated_file):
            return jsonify({'error': f'Uncorrelated coins data not found at {uncorrelated_file}'}), 404
            
        df = pd.read_csv(uncorrelated_file)
        return jsonify(df.to_dict('records'))
    except Exception as e:
        return jsonify({'error': f'Error loading uncorrelated coins data: {str(e)}'}), 500

@app.route('/api/price-distance-coins')
def get_price_distance_coins():
    """Return price distance coins data."""
    try:
        price_distance_file = os.path.join(analysis_dir, 'out_of_threshold_coins.csv')
        if not os.path.exists(price_distance_file):
            return jsonify({'error': f'Price distance coins data not found at {price_distance_file}'}), 404
            
        df = pd.read_csv(price_distance_file)
        return jsonify(df.to_dict('records'))
    except Exception as e:
        return jsonify({'error': f'Error loading price distance coins data: {str(e)}'}), 500

@app.route('/api/average-returns')
def get_average_returns():
    """Return average returns data."""
    try:
        returns_file = os.path.join(analysis_dir, 'average_returns.csv')
        if not os.path.exists(returns_file):
            return jsonify({'error': f'Average returns data not found at {returns_file}'}), 404

        df = pd.read_csv(returns_file)
        data = df.set_index('symbol').to_dict(orient='index')
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': f'Error loading average returns data: {str(e)}'}), 500

@app.route('/api/test')
def get_test_data():
    """Return test data to verify API is working."""
    return jsonify({
        "test": "data", 
        "paths": {
            "current_dir": current_dir,
            "parent_dir": parent_dir,
            "analysis_dir": analysis_dir,
            "analysis_dir_exists": os.path.exists(analysis_dir),
            "files_in_analysis_dir": os.listdir(analysis_dir) if os.path.exists(analysis_dir) else []
        }
    })

if __name__ == '__main__':
    # Create sample data if needed
    create_sample_data()
    
    print(f"Starting web server at http://localhost:5000")
    print(f"Analysis directory: {analysis_dir}")
    if os.path.exists(analysis_dir):
        print(f"Files in analysis directory: {os.listdir(analysis_dir)}")
        
    app.run(host='0.0.0.0', port=5000, debug=True)