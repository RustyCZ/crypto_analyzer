#!/usr/bin/env python3
"""
Script to analyze price distance from market average for cryptocurrencies.
"""
import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("price_distance_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Directories
HISTORICAL_DATA_DIR = Path('historical_data')
ANALYSIS_DIR = Path('analysis_results')
ANALYSIS_DIR.mkdir(exist_ok=True)

def load_combined_data():
    """
    Load the combined price and returns data.
    
    Returns:
        tuple: (price_df, returns_df) DataFrames containing combined price and returns data
    """
    try:
        # Load combined prices
        price_file = HISTORICAL_DATA_DIR / 'combined_prices.csv'
        price_df = pd.read_csv(price_file)
        price_df['date'] = pd.to_datetime(price_df['date'])
        
        # Load combined returns
        returns_file = HISTORICAL_DATA_DIR / 'combined_returns.csv'
        returns_df = pd.read_csv(returns_file)
        returns_df['date'] = pd.to_datetime(returns_df['date'])
        
        logger.info(f"Successfully loaded combined data with {len(price_df)} days and {len(price_df.columns)-1} coins")
        return price_df, returns_df
    
    except FileNotFoundError as e:
        logger.error(f"Error loading combined data: {e}")
        return None, None

def calculate_market_average(returns_df):
    """
    Calculate the average market return for each day.
    
    Args:
        returns_df (DataFrame): DataFrame containing daily returns for all coins
        
    Returns:
        Series: Series containing average market returns for each day
    """
    logger.info("Calculating average market returns...")
    
    # Drop the date column and any NaN values
    returns_only = returns_df.drop(columns=['date'])
    
    # Calculate average return across all coins for each day
    market_avg_returns = returns_only.mean(axis=1)
    
    # Create a DataFrame with date and market average
    market_df = pd.DataFrame({
        'date': returns_df['date'],
        'market_avg_return': market_avg_returns
    })
    
    # Save to CSV
    market_df.to_csv(ANALYSIS_DIR / 'market_average_returns.csv', index=False)
    logger.info(f"Successfully calculated market average returns for {len(market_df)} days")
    
    return market_df

def calculate_price_distance(returns_df, market_avg_df, threshold=0.3):
    """
    Calculate the price distance between each coin and the market average.
    Identify coins that are out of the specified threshold distance.
    
    Args:
        returns_df (DataFrame): DataFrame containing daily returns for all coins
        market_avg_df (DataFrame): DataFrame containing market average returns
        threshold (float): Threshold for price distance (default: 0.3 or 30%)
        
    Returns:
        DataFrame: DataFrame with price distance metrics for each coin
    """
    logger.info(f"Calculating price distance with threshold {threshold}...")
    
    # Drop the date column
    returns_only = returns_df.drop(columns=['date'])
    
    # Calculate cumulative returns for each coin
    cumulative_returns = {}
    for coin in returns_only.columns:
        # Calculate cumulative return using formula: (1 + r1) * (1 + r2) * ... * (1 + rn) - 1
        cumulative_returns[coin] = (1 + returns_only[coin].fillna(0)).cumprod() - 1
    
    # Create DataFrame with cumulative returns
    cum_returns_df = pd.DataFrame(cumulative_returns)
    cum_returns_df['date'] = returns_df['date']
    
    # Calculate cumulative market average return
    market_cum_return = (1 + market_avg_df['market_avg_return'].fillna(0)).cumprod() - 1
    
    # Calculate final cumulative returns
    final_cum_returns = cum_returns_df.iloc[-1].drop('date')
    final_market_return = market_cum_return.iloc[-1]
    
    # Calculate price distance from market
    price_distance = {}
    for coin in returns_only.columns:
        # Calculate absolute difference between coin and market returns
        price_distance[coin] = abs(final_cum_returns[coin] - final_market_return)
    
    # Create DataFrame with price distance metrics
    distance_df = pd.DataFrame({
        'symbol': list(price_distance.keys()),
        'cumulative_return': [final_cum_returns[coin] for coin in price_distance.keys()],
        'price_distance': list(price_distance.values()),
        'market_return': final_market_return
    })
    
    # Calculate relative distance (as percentage of market return)
    distance_df['relative_distance'] = distance_df['price_distance'] / abs(final_market_return)
    
    # Sort by price distance
    distance_df = distance_df.sort_values('price_distance', ascending=False)
    
    # Identify coins out of threshold
    out_of_threshold = distance_df[distance_df['price_distance'] > threshold]
    
    # Save to CSV
    distance_df.to_csv(ANALYSIS_DIR / 'price_distance.csv', index=False)
    out_of_threshold.to_csv(ANALYSIS_DIR / 'out_of_threshold_coins.csv', index=False)
    
    logger.info(f"Found {len(out_of_threshold)} coins with price distance > {threshold}")
    
    # Create visualization
    plt.figure(figsize=(12, 8))
    plt.bar(distance_df['symbol'], distance_df['price_distance'])
    plt.axhline(y=threshold, color='r', linestyle='-', label=f'Threshold ({threshold})')
    plt.xlabel('Coin')
    plt.ylabel('Price Distance from Market')
    plt.title('Price Distance from Market Average')
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.savefig(ANALYSIS_DIR / 'price_distance.png', dpi=300)
    logger.info("Successfully created price distance visualization")
    
    return distance_df, out_of_threshold, cum_returns_df, market_cum_return

def generate_comparison_data(cum_returns_df, market_cum_return, out_of_threshold):
    """
    Generate comparison data for web visualization.
    
    Args:
        cum_returns_df (DataFrame): DataFrame with cumulative returns for all coins
        market_cum_return (Series): Series with cumulative market returns
        out_of_threshold (DataFrame): DataFrame with coins out of threshold
        
    Returns:
        dict: Dictionary with comparison data for web visualization
    """
    logger.info("Generating comparison data for web visualization...")
    
    # Create a dictionary to store comparison data
    comparison_data = {
        'dates': cum_returns_df['date'].dt.strftime('%Y-%m-%d').tolist(),
        'market_avg': market_cum_return.tolist(),
        'coins': {}
    }
    
    # Add data for each out-of-threshold coin
    for _, row in out_of_threshold.iterrows():
        symbol = row['symbol']
        comparison_data['coins'][symbol] = {
            'name': symbol,
            'data': cum_returns_df[symbol].tolist(),
            'cumulative_return': row['cumulative_return'],
            'price_distance': row['price_distance'],
            'relative_distance': row['relative_distance']
        }
    
    # Save to JSON
    with open(ANALYSIS_DIR / 'comparison_data.json', 'w') as f:
        json.dump(comparison_data, f, indent=2)
    
    logger.info(f"Successfully generated comparison data for {len(comparison_data['coins'])} coins")
    
    return comparison_data

if __name__ == "__main__":
    logger.info("Starting price distance analysis...")
    
    # Load combined data
    price_df, returns_df = load_combined_data()
    
    if price_df is not None and returns_df is not None:
        # Calculate market average
        market_avg_df = calculate_market_average(returns_df)
        
        # Calculate price distance
        distance_df, out_of_threshold, cum_returns_df, market_cum_return = calculate_price_distance(
            returns_df, market_avg_df, threshold=0.3
        )
        
        # Generate comparison data for web visualization
        comparison_data = generate_comparison_data(
            cum_returns_df, market_cum_return, out_of_threshold
        )
        
        logger.info("Price distance analysis completed successfully")
    else:
        logger.error("Failed to load combined data. Make sure to run download_historical_data.py first.")
