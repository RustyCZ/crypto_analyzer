#!/usr/bin/env python3
"""
Script to download historical price data (180 daily candles) for the top 100 coins.
Includes robust handling of API rate limits with exponential backoff.
"""
import os
import json
import time
import random
import pandas as pd
from datetime import datetime, timedelta
import requests
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("download_history.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create directory for historical data
HISTORICAL_DATA_DIR = Path('historical_data')
HISTORICAL_DATA_DIR.mkdir(exist_ok=True)

# Maximum number of retries for API requests
MAX_RETRIES = 5
# Initial delay between retries in seconds
INITIAL_RETRY_DELAY = 10
# Maximum delay between retries in seconds
MAX_RETRY_DELAY = 120

def load_top_coins():
    """
    Load the previously saved top coins data.
    
    Returns:
        list: List of coin data dictionaries
    """
    try:
        with open('top_coins.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Error: top_coins.json not found. Please run fetch_top_coins.py first.")
        return None

def get_with_retry(url, params, max_retries=MAX_RETRIES, initial_delay=INITIAL_RETRY_DELAY):
    """
    Make a GET request with exponential backoff retry logic.
    
    Args:
        url (str): URL to request
        params (dict): Query parameters
        max_retries (int): Maximum number of retry attempts
        initial_delay (int): Initial delay between retries in seconds
        
    Returns:
        dict: JSON response data or None if all retries failed
    """
    retry_count = 0
    delay = initial_delay
    
    while retry_count <= max_retries:
        try:
            response = requests.get(url, params=params)
            
            # If successful, return the data
            if response.status_code == 200:
                return response.json()
                
            # If rate limited, wait and retry
            if response.status_code == 429:
                retry_count += 1
                
                # Add jitter to avoid thundering herd problem
                jitter = random.uniform(0.8, 1.2)
                sleep_time = min(delay * jitter, MAX_RETRY_DELAY)
                
                logger.warning(f"Rate limited. Waiting {sleep_time:.2f}s before retry {retry_count}/{max_retries}")
                time.sleep(sleep_time)
                
                # Exponential backoff
                delay *= 2
            else:
                # Other error, raise exception
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            retry_count += 1
            
            if retry_count > max_retries:
                logger.error(f"Max retries exceeded: {e}")
                return None
                
            # Add jitter to avoid thundering herd problem
            jitter = random.uniform(0.8, 1.2)
            sleep_time = min(delay * jitter, MAX_RETRY_DELAY)
            
            logger.warning(f"Request error: {e}. Waiting {sleep_time:.2f}s before retry {retry_count}/{max_retries}")
            time.sleep(sleep_time)
            
            # Exponential backoff
            delay *= 2
    
    return None

def download_historical_data_coingecko(coins, days=180):
    """
    Download historical price data using CoinGecko API with rate limit handling.
    
    Args:
        coins (list): List of coin data dictionaries
        days (int): Number of days of historical data to fetch
        
    Returns:
        dict: Dictionary mapping coin symbols to their historical data DataFrames
    """
    logger.info(f"Downloading {days} days of historical data for {len(coins)} coins...")
    
    historical_data = {}
    
    # Check if we already have some data downloaded
    existing_coins = set()
    if HISTORICAL_DATA_DIR.exists():
        for file in HISTORICAL_DATA_DIR.glob("*_historical.csv"):
            symbol = file.name.split("_")[0]
            existing_coins.add(symbol)
    
    logger.info(f"Found {len(existing_coins)} coins with existing data")
    
    for i, coin in enumerate(coins):
        coin_id = coin['id']
        symbol = coin['symbol'].upper()
        name = coin['name']
        
        # Skip if we already have data for this coin
        if symbol in existing_coins:
            logger.info(f"[{i+1}/{len(coins)}] Skipping {name} ({symbol}) - data already exists")
            
            # Load existing data
            try:
                csv_file = HISTORICAL_DATA_DIR / f"{symbol}_historical.csv"
                df = pd.read_csv(csv_file)
                df['date'] = pd.to_datetime(df['date'])
                historical_data[symbol] = df
                logger.info(f"  ✓ Loaded existing data with {len(df)} days for {symbol}")
            except Exception as e:
                logger.error(f"  ✗ Error loading existing data for {symbol}: {e}")
            
            continue
        
        logger.info(f"[{i+1}/{len(coins)}] Downloading data for {name} ({symbol})...")
        
        # CoinGecko API endpoint for historical market data
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily'
        }
        
        # Get data with retry logic
        data = get_with_retry(url, params)
        
        if data:
            # Process price data
            prices = data.get('prices', [])
            volumes = data.get('total_volumes', [])
            market_caps = data.get('market_caps', [])
            
            # Create DataFrame
            df = pd.DataFrame()
            
            if prices:
                # Extract timestamps and prices
                timestamps = [entry[0] for entry in prices]
                price_values = [entry[1] for entry in prices]
                
                # Convert timestamps to datetime
                dates = [datetime.fromtimestamp(ts/1000) for ts in timestamps]
                
                df['date'] = dates
                df['price'] = price_values
                
                # Add volume and market cap if available
                if volumes and len(volumes) == len(prices):
                    df['volume'] = [entry[1] for entry in volumes]
                
                if market_caps and len(market_caps) == len(prices):
                    df['market_cap'] = [entry[1] for entry in market_caps]
                
                # Calculate daily returns
                df['daily_return'] = df['price'].pct_change()
                
                # Save to CSV
                csv_file = HISTORICAL_DATA_DIR / f"{symbol}_historical.csv"
                df.to_csv(csv_file, index=False)
                
                # Store in dictionary
                historical_data[symbol] = df
                
                logger.info(f"  ✓ Successfully downloaded {len(df)} days of data for {symbol}")
            else:
                logger.warning(f"  ✗ No price data available for {symbol}")
        else:
            logger.error(f"  ✗ Failed to download data for {symbol} after multiple retries")
        
        # Always sleep between requests to avoid rate limiting
        sleep_time = random.uniform(3.0, 5.0)
        logger.info(f"  Sleeping for {sleep_time:.2f}s before next request")
        time.sleep(sleep_time)
    
    return historical_data

def calculate_daily_candles(historical_data):
    """
    Calculate OHLC (Open, High, Low, Close) candles from price data.
    
    Args:
        historical_data (dict): Dictionary mapping coin symbols to their historical data DataFrames
        
    Returns:
        dict: Dictionary mapping coin symbols to their OHLC DataFrames
    """
    logger.info("Calculating daily candles from price data...")
    
    ohlc_data = {}
    
    for symbol, df in historical_data.items():
        if len(df) < 2:
            logger.warning(f"Insufficient data for {symbol}, skipping")
            continue
            
        # Ensure data is sorted by date
        df = df.sort_values('date')
        
        # Resample to daily frequency and calculate OHLC
        # Since we already have daily data, we'll simulate OHLC by using the same price
        # In a real scenario with intraday data, we would use proper resampling
        daily_df = pd.DataFrame()
        daily_df['date'] = df['date']
        daily_df['open'] = df['price']
        daily_df['high'] = df['price']
        daily_df['low'] = df['price']
        daily_df['close'] = df['price']
        daily_df['volume'] = df['volume'] if 'volume' in df.columns else None
        
        # Calculate daily returns
        daily_df['daily_return'] = daily_df['close'].pct_change()
        
        # Save to CSV
        csv_file = HISTORICAL_DATA_DIR / f"{symbol}_daily_candles.csv"
        daily_df.to_csv(csv_file, index=False)
        
        # Store in dictionary
        ohlc_data[symbol] = daily_df
        
    logger.info(f"Successfully calculated daily candles for {len(ohlc_data)} coins")
    return ohlc_data

def save_combined_data(historical_data):
    """
    Save a combined CSV with all coins' closing prices for easier correlation analysis.
    
    Args:
        historical_data (dict): Dictionary mapping coin symbols to their historical data DataFrames
    """
    logger.info("Creating combined price dataset for correlation analysis...")
    
    if not historical_data:
        logger.error("No historical data available to combine")
        return
    
    # Create a DataFrame with dates
    first_symbol = list(historical_data.keys())[0]
    combined_df = pd.DataFrame()
    combined_df['date'] = historical_data[first_symbol]['date']
    
    # Add closing prices for each coin
    for symbol, df in historical_data.items():
        if len(df) == len(combined_df):
            combined_df[symbol] = df['price']
    
    # Save to CSV
    combined_df.to_csv(HISTORICAL_DATA_DIR / 'combined_prices.csv', index=False)
    logger.info(f"Successfully saved combined price data for {len(historical_data)} coins")
    
    # Also save daily returns for correlation analysis
    combined_returns_df = pd.DataFrame()
    combined_returns_df['date'] = historical_data[first_symbol]['date']
    
    for symbol, df in historical_data.items():
        if len(df) == len(combined_returns_df) and 'daily_return' in df.columns:
            combined_returns_df[symbol] = df['daily_return']
    
    # Save to CSV
    combined_returns_df.to_csv(HISTORICAL_DATA_DIR / 'combined_returns.csv', index=False)
    logger.info(f"Successfully saved combined daily returns for {len(historical_data)} coins")

if __name__ == "__main__":
    # Create timestamp for this run
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Starting historical data download at {timestamp}")
    
    # Load top coins
    coins = load_top_coins()
    
    if coins:
        # Download historical data
        historical_data = download_historical_data_coingecko(coins, days=180)
        
        if historical_data:
            # Calculate daily candles
            ohlc_data = calculate_daily_candles(historical_data)
            
            # Save combined data for correlation analysis
            save_combined_data(historical_data)
            
            logger.info(f"Historical data download completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            logger.error("Failed to download historical data. Exiting.")
    else:
        logger.error("Failed to load top coins data. Exiting.")
