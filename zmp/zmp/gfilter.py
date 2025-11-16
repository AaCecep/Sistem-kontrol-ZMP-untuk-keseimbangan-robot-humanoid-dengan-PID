import pandas as pd
import matplotlib.pyplot as plt

try:
    # === Baca file CSV ===
    data = pd.read_csv('diamfilter.csv')

    # === Plot grafik ===
    plt.figure(figsize=(10, 5))
    
    # Plot ZMP-X
    plt.plot(data['time (s)'], data['zmp_x'], 
             label='ZMP-X', linewidth=2)
    
    # Plot ZMP-X Lama 
    plt.plot(data['time (s)'], data['zmp_x_lama'], 
             label='ZMP-X Lama', linewidth=2)

    # === Label dan tampilan ===
    plt.title('Grafik Perbandingan ZMP-X dan ZMP-X Lama')
    plt.xlabel('Waktu (s)')
    plt.ylabel('ZMP (x)')
    plt.grid(True)
    plt.legend()

    # === Tampilkan grafik ===
    plt.show()

except FileNotFoundError:
    print("Error: File 'filter.csv' tidak ditemukan. Mohon upload atau pastikan path-nya benar.")
except KeyError as e:
    print(f"Error: Kolom {e} tidak ditemukan di file CSV. Cek kembali nama kolom yang tersedia.")
