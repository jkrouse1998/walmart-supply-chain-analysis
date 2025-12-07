# walmart-supply-chain-analysis



# Walmart Supply-Chain Analysis Tool

## Overview
Command-line Python script demonstrating demand forecasting and inventory management concepts using Walmart weekly sales data.

## Key Features
- **Store Performance Summary** — aggregates sales metrics across locations
- **Holiday Impact Analysis** — quantifies demand spikes during holiday weeks
- **Demand Forecasting** — simple moving-average predictions for inventory planning
- **Safety Stock Calculation** — computes reorder points based on lead time and demand variability

## Tech Stack
- Python 3.11
- pandas (data manipulation)
- argparse (CLI)

## Setup
```bash
python -m venv .venv
.\.venv\Scripts\Activate  # Windows
pip install -r requirements.txt
```

## Usage Examples
```bash
# Store summary
python walmart_analysis.py --file Walmart.csv --summary

# Holiday impact
python walmart_analysis.py --file Walmart.csv --holiday-impact

# Forecast for store 1
python walmart_analysis.py --file Walmart.csv --forecast --store 1 --weeks 4

# Safety stock example
python walmart_analysis.py --file Walmart.csv --safety-stock --store 1 --lead 2
```

## Output
Results saved to `outputs/` folder as CSV files and printed to console.

## Learning Concepts
- Demand aggregation and groupby operations
- Time-series resampling and moving averages
- Basic inventory theory (safety stock, reorder point)
- Supply-chain metrics (demand variability, lead time)
