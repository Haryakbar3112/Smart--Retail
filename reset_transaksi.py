import sqlite3

conn = sqlite3.connect("smart_retail.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM produk")

conn.commit()
conn.close()

print("Data transaksi berhasil direset")