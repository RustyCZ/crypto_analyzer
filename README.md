# Crypto Correlation Analyzer

A Python application that identifies cryptocurrencies that do not follow the general altcoin market by analyzing price correlations and price distance.

This code was generated by manus AI with the following tasks.

## Overview

This application performs the following tasks:

1. Fetches the top 100 cryptocurrencies by market cap from CoinGecko
2. Downloads 180 days of historical price data for each coin
3. Calculates average percentage gain/loss for these coins
4. Creates a correlation matrix to identify coins that don't follow the general altcoin market
5. Analyzes coins that are out of 30% price distance from the overall market
6. Creates a web visualization showing market average vs. individual coin performance

## Requirements

- Python 3.10+
- Required Python packages:
  - pandas
  - numpy
  - matplotlib
  - seaborn
  - requests
  - ccxt
  - flask

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/crypto-correlation-analyzer.git
cd crypto-correlation-analyzer

# Install required packages
pip install -r requirements.txt
```

## Usage

You can run the entire pipeline with:

```bash
python main.py
```

Or run individual scripts:

```bash
# Step 1: Fetch top 100 coins by market cap
python fetch_top_coins.py

# Step 2: Download historical data (180 daily candles)
python download_historical_data.py

# Step 3: Analyze correlations and identify uncorrelated coins
python analyze_correlations.py

# Step 4: Analyze price distance from market average
python analyze_price_distance.py

# Step 5: Create web visualization
python create_web_visualization.py
```

## Web Visualization

To view the web visualization:

```bash
cd web_visualization
python app.py
```

Then open your browser and navigate to `http://localhost:5000`

## Output

The application generates several output files:

- `top_coins.csv` - List of top 100 coins by market cap
- `historical_data/` - Directory containing historical price data for each coin
- `analysis_results/` - Directory containing analysis results:
  - `average_returns.csv` - Average percentage changes for each coin
  - `correlation_matrix.csv` - Correlation matrix of all coins
  - `correlation_heatmap.png` - Visualization of the correlation matrix
  - `average_correlations.csv` - Average correlation of each coin with others
  - `uncorrelated_coins.csv` - List of coins that don't follow the general market
  - `average_correlations.png` - Visualization of average correlations
  - `price_distance.csv` - Price distance from market average for each coin
  - `out_of_threshold_coins.csv` - List of coins that are out of 30% price distance
  - `price_distance.png` - Visualization of price distance from market
  - `comparison_data.json` - Data for web visualization

## How It Works

1. **Data Collection**: The application uses the CoinGecko API to fetch the top 100 cryptocurrencies by market cap and their historical price data.

2. **Data Processing**: Daily returns are calculated for each coin, and a correlation matrix is created to measure how each coin's price movements correlate with others.

3. **Correlation Analysis**: Coins with low average correlation to the rest of the market are identified as those that don't follow the general altcoin market trends.

4. **Price Distance Analysis**: Coins that are out of 30% price distance from the overall market are identified as having abnormal price action.

5. **Web Visualization**: A web interface is created to visualize the market average vs. individual coin performance, allowing for interactive exploration of the results.

## Notes

- The application implements robust rate limiting handling to work within CoinGecko API constraints
- The correlation threshold for identifying uncorrelated coins is set to 0.3 by default
- The price distance threshold is set to 0.3 (30%) by default
