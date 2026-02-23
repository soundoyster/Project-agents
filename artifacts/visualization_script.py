import os
import pandas as pd
import matplotlib.pyplot as plt

os.makedirs('artifacts/', exist_ok=True)

original_data = [
    ["2025-09-01", 542],
    ["2025-09-02", 489],
    ["2025-09-03", 563],
    ["2025-09-04", 512],
    ["2025-09-05", 0],
    ["2025-09-06", 598],
    ["2025-09-07", 621],
    ["2025-09-08", 505],
    ["2025-09-09", 0],
    ["2025-09-10", 534],
    ["2025-09-11", 511],
    ["2025-09-12", 490],
    ["2025-09-13", 523],
    ["2025-09-14", 514],
    ["2025-09-15", 2500],
    ["2025-09-16", 527],
    ["2025-09-17", 499],
    ["2025-09-18", 5545],
    ["2025-09-19", 488],
    ["2025-09-20", 531]
]

cleaned_data = [
    ["2025-09-01", 542],
    ["2025-09-02", 489],
    ["2025-09-03", 563],
    ["2025-09-04", 512],
    ["2025-09-06", 598],
    ["2025-09-07", 621],
    ["2025-09-08", 505],
    ["2025-09-10", 534],
    ["2025-09-11", 511],
    ["2025-09-12", 490],
    ["2025-09-13", 523],
    ["2025-09-14", 514],
    ["2025-09-16", 527],
    ["2025-09-17", 499],
    ["2025-09-19", 488],
    ["2025-09-20", 531]
]

df_original = pd.DataFrame(original_data, columns=['Date', 'Original'])
df_cleaned = pd.DataFrame(cleaned_data, columns=['Date', 'Cleaned'])

df_plot = pd.merge(df_original, df_cleaned, on='Date', how='outer')
df_plot = df_plot.sort_values('Date')

plt.figure(figsize=(10,6))
plt.plot(df_plot['Date'], df_plot['Original'], color='blue', label='Original')
plt.plot(df_plot['Date'], df_plot['Cleaned'], color='green', label='Cleaned')
plt.xlabel('Date')
plt.ylabel('Value')
plt.title('Original vs Cleaned Data')
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('artifacts/data_visualization.png')