import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import numpy as np

# === Baca file CSV ===
data = pd.read_csv("cep.csv")  # ganti dengan nama file kamu
time = data["time (s)"]
zmp_x = data["zmp_x"]

# === Cari puncak (peak) pada sinyal ZMP-X ===
peaks, _ = find_peaks(zmp_x, prominence=0.05)  # prominence = sensitivitas
valleys, _ = find_peaks(-zmp_x, prominence=0.05)

# === Hitung periode osilasi (selisih waktu antar puncak) ===
if len(peaks) > 1:
    Pu_list = np.diff(time.iloc[peaks])
    Pu_mean = np.mean(Pu_list)
    print(f"Jumlah osilasi terdeteksi: {len(peaks)}")
    print(f"Pu rata-rata: {Pu_mean:.3f} detik")
else:
    print("⚠️ Tidak cukup puncak terdeteksi untuk menghitung Pu")

# === Plot grafik dan tandai puncak ===
plt.figure(figsize=(10, 5))
plt.plot(time, zmp_x, label="ZMP-X", color='blue')
plt.plot(time.iloc[peaks], zmp_x.iloc[peaks], "ro", label="Puncak (Peak)")
plt.plot(time.iloc[valleys], zmp_x.iloc[valleys], "go", label="Lembah (Valley)")

plt.title("Deteksi Osilasi ZMP-X dan Perhitungan Pu")
plt.xlabel("Waktu (s)")
plt.ylabel("ZMP-X")
plt.legend()
plt.grid(True)
plt.show()
