import argparse                       # import library to parse command-line arguments
from pathlib import Path               # import Path for filesystem path handling
import pandas as pd                    # import pandas for data manipulation
import math                            # import math for sqrt used in safety stock calc

def load_data(path: Path) -> pd.DataFrame:  # function to load CSV into a DataFrame
    df = pd.read_csv(path, parse_dates=['Date'])  # read CSV and parse 'Date' column as datetime
    df.columns = df.columns.str.strip()           # strip whitespace from column names to normalize
    return df                                     # return the loaded DataFrame

def detect_holiday_col(df: pd.DataFrame):        # detect which column indicates holidays
    if 'IsHoliday' in df.columns:                # prefer 'IsHoliday' if present
        return 'IsHoliday'                       
    if 'Holiday_Flag' in df.columns:             # fallback to 'Holiday_Flag' if present
        return 'Holiday_Flag'
    found = next((c for c in df.columns if 'holiday' in c.lower()), None)  # find any column containing 'holiday'
    return found                                  # return found name or None

def summary_by_store(df: pd.DataFrame) -> pd.DataFrame:  # aggregate sales metrics per store
    agg = df.groupby('Store').agg(                      # group rows by 'Store'
        total_sales=pd.NamedAgg(column='Weekly_Sales', aggfunc='sum'),  # total sales per store
        avg_weekly=pd.NamedAgg(column='Weekly_Sales', aggfunc='mean'),  # average weekly sales
        std_weekly=pd.NamedAgg(column='Weekly_Sales', aggfunc='std'),   # standard deviation of weekly sales
        weeks=pd.NamedAgg(column='Weekly_Sales', aggfunc='count'),      # number of weeks (rows) per store
    ).reset_index()                                       # convert grouped index back to columns
    return agg.sort_values('total_sales', ascending=False) # sort stores by total sales descending

def holiday_impact(df: pd.DataFrame, holiday_col: str) -> pd.DataFrame:  # compare sales on holiday vs non-holiday
    df_h = df.copy()                                 # work on a copy to avoid mutating original DF
    df_h[holiday_col] = df_h[holiday_col].astype(str).str.lower().isin(['1','true','yes'])  # normalize flag to boolean
    return df_h.groupby(holiday_col)['Weekly_Sales'].agg(['mean','count','std']).reset_index()  # aggregate stats by holiday flag

def moving_average_forecast(df: pd.DataFrame, store: int, weeks: int = 4) -> float:  # simple MA forecast for a store
    s = df[df['Store'] == store].sort_values('Date')  # filter rows for the requested store and sort by date
    if s.empty:                                       # if no data for that store, raise an error
        raise KeyError(f"No data for store {store}")
    s = s.set_index('Date').resample('W').sum().fillna(0)  # resample weekly, summing sales and filling missing weeks with 0
    ma = s['Weekly_Sales'].rolling(window=weeks).mean()   # compute rolling mean over the specified window
    return float(ma.dropna().iloc[-1]) if not ma.dropna().empty else float(s['Weekly_Sales'].mean())  # return last MA or overall mean if insufficient data

def safety_stock_example(df: pd.DataFrame, store: int, lead_time_weeks: float = 2, service_factor: float = 1.65):  # compute safety stock example
    s = df[df['Store'] == store].groupby('Date')['Weekly_Sales'].sum()  # sum sales per date for the store
    if s.empty:                                # check for empty series and raise if absent
        raise KeyError(f"No data for store {store}")
    demand_mean = s.mean()                      # average weekly demand
    demand_std = s.std()                        # standard deviation of weekly demand
    safety_stock = service_factor * demand_std * math.sqrt(lead_time_weeks)  # safety stock formula (normal-approx)
    reorder_point = demand_mean * lead_time_weeks + safety_stock  # reorder point = demand during lead + safety stock
    return {                                    # return results as a simple dict of numeric values
        'store': store,
        'mean_weekly_demand': float(demand_mean),
        'std_weekly_demand': float(demand_std),
        'safety_stock': float(safety_stock),
        'reorder_point': float(reorder_point)
    }

def ensure_out(path: Path):                     # create output directory if missing
    path.mkdir(parents=True, exist_ok=True)     # make directories recursively and ignore if already exist

def main():                                     # main CLI entrypoint
    p = argparse.ArgumentParser(description="Simple Walmart supply-chain analyses")  # create argument parser with description
    p.add_argument('--file', required=True, help='Path to Walmart.csv')              # required CSV file path argument
    p.add_argument('--summary', action='store_true')                                # flag to run summary_by_store
    p.add_argument('--holiday-impact', action='store_true')                         # flag to run holiday_impact
    p.add_argument('--forecast', action='store_true')                                # flag to run moving_average_forecast
    p.add_argument('--safety-stock', action='store_true')                            # flag to run safety_stock_example
    p.add_argument('--store', type=int, default=1)                                   # store id to analyze (default 1)
    p.add_argument('--weeks', type=int, default=4)                                   # window size for moving average
    p.add_argument('--lead', type=float, default=2.0)                                # lead time in weeks for safety stock
    args = p.parse_args()                                                             # parse CLI args into 'args'

    path = Path(args.file)                 # convert file path string to a Path object
    df = load_data(path)                   # load the CSV into a DataFrame using helper
    out = Path('outputs')                  # define outputs directory
    ensure_out(out)                        # ensure outputs directory exists

    if args.summary:                       # if user requested summary
        s = summary_by_store(df)           # compute summary
        print(s.head(10).to_string(index=False))  # print top 10 stores to console
        s.to_csv(out / 'store_summary.csv', index=False)  # save summary to outputs CSV

    if args.holiday_impact:                # if user requested holiday impact analysis
        hcol = detect_holiday_col(df)      # detect holiday column name
        if not hcol:                       # if none found, notify available columns
            print("No holiday-like column found. Available:", df.columns.tolist())
        else:
            hi = holiday_impact(df, hcol)  # compute holiday impact stats
            print(hi.to_string(index=False))  # print results
            hi.to_csv(out / 'holiday_impact.csv', index=False)  # save to CSV

    if args.forecast:                      # if user requested forecast
        try:
            f = moving_average_forecast(df, args.store, weeks=args.weeks)  # compute MA forecast
            print(f"Store {args.store} {args.weeks}-week MA forecast: {f:.2f}")  # print formatted forecast
        except KeyError as e:
            print(e)                        # print error if store not found

    if args.safety_stock:                   # if user requested safety stock example
        try:
            ss = safety_stock_example(df, args.store, lead_time_weeks=args.lead)  # compute safety stock and reorder point
            print(ss)                      # print the resulting dict
            pd.DataFrame([ss]).to_csv(out / f'store_{args.store}_safety_stock.csv', index=False)  # save to CSV
        except KeyError as e:
            print(e)                        # print error if store not found

if __name__ == '__main__':                  # only run main when executed as script
    main()                                   # call main to run CLI behavior
