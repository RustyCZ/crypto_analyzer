#!/usr/bin/env python3
"""
Script to fetch top 100 market cap coins from CoinGecko.
"""
import os
import json
import requests
import pandas as pd
from datetime import datetime

def fetch_top_coins(limit=100):
    """
    Fetch top market cap coins from CoinGecko.
    
    Args:
        limit (int): Number of top coins to fetch
        
    Returns:
        pandas.DataFrame: DataFrame containing coin data
    """
    print(f"Fetching top {limit} coins by market cap...")
    
    # Using CoinGecko API which is free and doesn't require authentication
    url = f"https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': limit,
        'page': 1,
        'sparkline': False
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()
        
        # Create DataFrame from response
        df = pd.DataFrame(data)
        
        # Select and rename relevant columns
        selected_columns = [
            'id', 'symbol', 'name', 'current_price', 'market_cap', 
            'market_cap_rank', 'total_volume', 'price_change_percentage_24h'
        ]
        
        df = df[selected_columns]
        
        # Save to CSV
        output_file = 'top_coins.csv'
        df.to_csv(output_file, index=False)
        print(f"Successfully saved {len(df)} coins to {output_file}")
        
        # Also save as JSON for easier processing
        with open('top_coins.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        return df
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from CoinGecko: {e}")
        return None

if __name__ == "__main__":
    # Create timestamp for this run
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Starting coin data collection at {timestamp}")
    
    # Fetch top 100 coins
    coins_df = fetch_top_coins(100)
    
    if coins_df is not None:
        print(f"Top 5 coins by market cap:")
        print(coins_df.head(5)[['market_cap_rank', 'name', 'symbol', 'market_cap']])
