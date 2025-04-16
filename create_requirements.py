#!/usr/bin/env python3
"""
Script to create a requirements.txt file for the Crypto Correlation Analyzer
"""

requirements = """pandas>=1.5.0
numpy>=1.20.0
matplotlib>=3.5.0
seaborn>=0.12.0
requests>=2.25.0
ccxt>=4.0.0
flask>=2.0.0
"""

def create_requirements():
    """Create requirements.txt file"""
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    print("requirements.txt created successfully")

if __name__ == "__main__":
    create_requirements()
