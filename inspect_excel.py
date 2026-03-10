
import pandas as pd

df = pd.read_excel('d:/fish-price-forecast/historical_data.xlsx', engine='openpyxl')
print("Shape:", df.shape)
print("Columns:", df.columns.tolist())
print("Date range:", df['date'].min(), "to", df['date'].max())
print("\nFirst row (non-null check):")
print(df.dropna(how='all').head(1).to_string())
