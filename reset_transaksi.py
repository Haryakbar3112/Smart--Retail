import sqlite3

conn = sqlite3.connect("smart_retail.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM produk")
cursor.execute("DELETE FROM transaksi")
cursor.execute("DELETE FROM transaksi")

conn.commit()
conn.close()

print("Data transaksi berhasil direset")