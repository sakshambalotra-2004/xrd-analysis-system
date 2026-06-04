import pandas as pd
import numpy as np

# Generate 2500 points from 10 to 100 degrees
two_theta = np.linspace(10, 100, 2500)
# Create a base noise floor
intensity = np.random.normal(10, 2, 2500)

# Add the 6H SiC peaks
peaks = {34.11: 1200, 35.67: 1050, 38.15: 880, 41.44: 720, 59.98: 690}
for pos, amp in peaks.items():
    # Gaussian peak shapes
    intensity += amp * np.exp(-((two_theta - pos) ** 2) / (2 * 0.05**2))

df = pd.DataFrame({'two_theta': two_theta, 'intensity': intensity})
df.to_csv('test_sic_6h_full.csv', index=False)