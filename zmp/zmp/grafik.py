import pandas as pd
import matplotlib.pyplot as plt

# === Baca file CSV ===
data = pd.read_csv('cep.csv')   # ubah nama file sesuai nama file kamu

# === Plot grafik ===
plt.figure(figsize=(10, 5))
plt.plot(data['time (s)'], data['zmp_x'], label='ZMP-X', linewidth=2)

# === Label dan tampilan ===
plt.title('Grafik ZMP terhadap Waktu')
plt.xlabel('Waktu (s)')
plt.ylabel('ZMP (x)')
plt.grid(True)
plt.legend()
plt.show()
