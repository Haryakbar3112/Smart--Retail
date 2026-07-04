import sqlite3

conn = sqlite3.connect("smart_retail.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    role TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS produk(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_produk TEXT,
    harga_modal INTEGER,
    harga_jual INTEGER,
    stok INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transaksi(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produk_id INTEGER,
    jumlah INTEGER,
    total INTEGER,
    created_at TEXT,
    FOREIGN KEY (produk_id) REFERENCES produk(id)
)
""")

conn.commit()
conn.close()

print("Database berhasil dibuat")
