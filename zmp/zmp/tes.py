import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# === Pilih 1 file yang ingin dianalisis ===
label = "PID Controller"
filename = "zmp.csv"

setpoint = 2.5   # setpoint ZMP-X

try:
    data = pd.read_csv(filename)

    # Hitung error
    error = setpoint - data['zmp_x']

    # Hitung statistik error
    mae  = np.mean(np.abs(error))       
    rmse = np.sqrt(np.mean(error**2))  

    # Hitung nilai max dan min
    zmax = data['zmp_x'].max()
    zmin = data['zmp_x'].min()
    amplitude = zmax - zmin

    # Cetak hasil ke terminal
    print(f"=== {label} ===")
    print(f"  Max ZMP-X : {zmax:.4f}")
    print(f"  Min ZMP-X : {zmin:.4f}")
    print(f"  Amplitudo : {amplitude:.4f}")
    print(f"  MAE       : {mae:.4f}")
    print(f"  RMSE      : {rmse:.4f}\n")

    # === Plot grafik ===
    plt.figure(figsize=(10, 5))
    plt.plot(data['time (s)'], data['zmp_x'], linewidth=2)

    plt.title(label)
    plt.xlabel("Waktu (s)")
    plt.ylabel("ZMP-X")
    plt.grid(True)

    # Batas sumbu y
    plt.ylim(-1, 5)

    plt.tight_layout()
    plt.show()

except Exception as e:
    print(f"Error saat membaca file {filename}: {e}")
