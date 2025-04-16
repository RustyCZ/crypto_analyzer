#!/usr/bin/env python3
"""
Script to analyze correlations and identify coins that don't follow the general altcoin market.
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
        logging.FileHandler("correlation_analysis.log"),
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

def calculate_average_changes(returns_df):
    """
    Calculate average percentage changes for each coin.
    
    Args:
        returns_df (DataFrame): DataFrame containing daily returns for all coins
        
    Returns:
        DataFrame: DataFrame with average percentage changes for each coin
    """
    logger.info("Calculating average percentage changes...")
    
    # Drop the date column for calculations
    returns_only = returns_df.drop(columns=['date'])
    
    # Calculate average daily return for each coin
    avg_daily_returns = returns_only.mean()
    
    # Calculate standard deviation of returns
    std_daily_returns = returns_only.std()
    
    # Calculate cumulative returns (total percentage change over the period)
    # Using formula: (1 + r1) * (1 + r2) * ... * (1 + rn) - 1
    cumulative_returns = (1 + returns_only).prod() - 1
    
    # Calculate annualized returns (assuming 365 days in a year)
    days_count = len(returns_df)
    annualized_returns = (1 + cumulative_returns) ** (365 / days_count) - 1
    
    # Calculate Sharpe ratio (assuming risk-free rate of 0)
    sharpe_ratio = avg_daily_returns / std_daily_returns * np.sqrt(365)
    
    # Create summary DataFrame
    summary_df = pd.DataFrame({
        'symbol': returns_only.columns,
        'avg_daily_return': avg_daily_returns.values,
        'std_daily_return': std_daily_returns.values,
        'cumulative_return': cumulative_returns.values,
        'annualized_return': annualized_returns.values,
        'sharpe_ratio': sharpe_ratio.values
    })
    
    # Sort by annualized return
    summary_df = summary_df.sort_values('annualized_return', ascending=False)
    
    # Save to CSV
    summary_df.to_csv(ANALYSIS_DIR / 'average_returns.csv', index=False)
    logger.info(f"Successfully calculated average returns for {len(summary_df)} coins")
    
    return summary_df

def create_correlation_matrix(returns_df):
    """
    Create correlation matrix for all coins.
    
    Args:
        returns_df (DataFrame): DataFrame containing daily returns for all coins
        
    Returns:
        DataFrame: Correlation matrix
    """
    logger.info("Creating correlation matrix...")
    
    # Drop the date column for calculations
    returns_only = returns_df.drop(columns=['date'])
    
    # Calculate correlation matrix
    corr_matrix = returns_only.corr()
    
    # Save to CSV
    corr_matrix.to_csv(ANALYSIS_DIR / 'correlation_matrix.csv')
    logger.info(f"Successfully created correlation matrix of size {corr_matrix.shape}")
    
    # Create heatmap visualization
    plt.figure(figsize=(20, 16))
    sns.heatmap(corr_matrix, annot=False, cmap='coolwarm', center=0)
    plt.title('Correlation Matrix of Cryptocurrency Returns', fontsize=16)
    plt.tight_layout()
    plt.savefig(ANALYSIS_DIR / 'correlation_heatmap.png', dpi=300)
    logger.info("Successfully created correlation heatmap visualization")
    
    return corr_matrix

def identify_uncorrelated_coins(corr_matrix, threshold=0.3):
    """
    Identify coins that do not follow the general altcoin market.
    
    Args:
        corr_matrix (DataFrame): Correlation matrix
        threshold (float): Correlation threshold to consider a coin as uncorrelated
        
    Returns:
        DataFrame: DataFrame with uncorrelated coins and their average correlation
    """
    logger.info(f"Identifying coins with correlation below {threshold}...")
    
    # Calculate average correlation for each coin (excluding self-correlation)
    avg_correlations = {}
    
    for coin in corr_matrix.columns:
        # Get all correlations for this coin, excluding self-correlation
        correlations = corr_matrix[coin].drop(coin)
        avg_correlations[coin] = correlations.mean()
    
    # Convert to DataFrame
    avg_corr_df = pd.DataFrame({
        'symbol': list(avg_correlations.keys()),
        'avg_correlation': list(avg_correlations.values())
    })
    
    # Sort by average correlation
    avg_corr_df = avg_corr_df.sort_values('avg_correlation')
    
    # Identify coins with average correlation below threshold
    uncorrelated_coins = avg_corr_df[avg_corr_df['avg_correlation'] < threshold]
    
    # Save to CSV
    avg_corr_df.to_csv(ANALYSIS_DIR / 'average_correlations.csv', index=False)
    uncorrelated_coins.to_csv(ANALYSIS_DIR / 'uncorrelated_coins.csv', index=False)
    
    logger.info(f"Found {len(uncorrelated_coins)} coins with average correlation below {threshold}")
    
    # Create visualization
    plt.figure(figsize=(12, 8))
    plt.bar(avg_corr_df['symbol'], avg_corr_df['avg_correlation'])
    plt.axhline(y=threshold, color='r', linestyle='-', label=f'Threshold ({threshold})')
    plt.xlabel('Coin')
    plt.ylabel('Average Correlation')
    plt.title('Average Correlation with Other Cryptocurrencies')
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.savefig(ANALYSIS_DIR / 'average_correlations.png', dpi=300)
    logger.info("Successfully created average correlation visualization")
    
    return uncorrelated_coins

if __name__ == "__main__":
    logger.info("Starting cryptocurrency correlation analysis...")
    
    # Load combined data
    price_df, returns_df = load_combined_data()
    
    if price_df is not None and returns_df is not None:
        # Calculate average percentage changes
        summary_df = calculate_average_changes(returns_df)
        
        # Create correlation matrix
        corr_matrix = create_correlation_matrix(returns_df)
        
        # Identify uncorrelated coins
        uncorrelated_coins = identify_uncorrelated_coins(corr_matrix)
        
        logger.info("Analysis completed successfully")
    else:
        logger.error("Failed to load combined data. Make sure to run download_historical_data.py first.")
