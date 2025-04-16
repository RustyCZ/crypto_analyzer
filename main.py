#!/usr/bin/env python3
"""
Main script to run the entire cryptocurrency correlation analysis pipeline.
"""
import os
import sys
import time
import logging
from pathlib import Path
import subprocess

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crypto_analyzer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_script(script_name):
    """
    Run a Python script and wait for it to complete.
    
    Args:
        script_name (str): Name of the script to run
        
    Returns:
        bool: True if script executed successfully, False otherwise
    """
    logger.info(f"Running {script_name}...")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Successfully completed {script_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {script_name}: {e}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return False

def main():
    """
    Run the entire cryptocurrency correlation analysis pipeline.
    """
    logger.info("Starting cryptocurrency correlation analysis pipeline...")
    
    # Step 1: Fetch top 100 coins
    if not run_script("fetch_top_coins.py"):
        logger.error("Failed to fetch top coins. Exiting.")
        return
    
    # Step 2: Download historical data
    if not run_script("download_historical_data.py"):
        logger.error("Failed to download historical data. Exiting.")
        return
    
    # Step 3: Analyze correlations
    if not run_script("analyze_correlations.py"):
        logger.error("Failed to analyze correlations. Exiting.")
        return
    
    # Step 4: Analyze price distance
    if not run_script("analyze_price_distance.py"):
        logger.error("Failed to analyze price distance. Exiting.")
        return
    
    # Step 5: Create web visualization
    if not run_script("create_web_visualization.py"):
        logger.error("Failed to create web visualization. Exiting.")
        return
    
    logger.info("Cryptocurrency correlation analysis pipeline completed successfully!")

if __name__ == "__main__":
    main()
