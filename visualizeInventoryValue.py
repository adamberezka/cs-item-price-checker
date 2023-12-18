import pandas as pd
import matplotlib.pyplot as plt

totalsFileName = 'totals.csv'

df = pd.read_csv(totalsFileName)

df['DateTime'] = pd.to_datetime(df['DateTime'])

# Create a line plot
plt.figure(figsize=(12, 6))  # Set the figure size
plt.plot(df['DateTime'], df['Value'], marker='o', linestyle='-', color='b')

plt.title('CS:GO cases value')
plt.xlabel('Date and Time')
plt.ylabel('Inventory value (PLN)')
plt.grid(True)

plt.xticks(rotation=30)

plt.savefig('invPricePlot.jpg', format='jpg', bbox_inches='tight')

plt.tight_layout()
plt.show()
