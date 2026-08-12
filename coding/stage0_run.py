import numpy as np 
import pandas as pd 

df = pd.read_csv("fasit_attributter.csv")

#Columns
signal_data = df["signal"].values

noise_floor_rms = np.sqrt(np.mean(signal_data**2))

noise_floor_db = np.log10(noise_floor_rms)

print(f"RmS Noise Floor {noise_floor_rms}:.5f")


