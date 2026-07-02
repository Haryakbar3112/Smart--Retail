import sqlite3

conn = sqlite3.connect("smart_retail.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
<<<<<<< HEAD
    id INTEGER PRIMARY KEY,
=======
    id INTEGER PRIMARY KEY AUTOINCREMENT,
>>>>>>> c0a3f9e9eb619b49ca8fde9b933dc51890efacb8
    username TEXT,
    password TEXT,
    role TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS produk(
<<<<<<< HEAD
    id INTEGER PRIMARY KEY,
=======
    id INTEGER PRIMARY KEY AUTOINCREMENT,
>>>>>>> c0a3f9e9eb619b49ca8fde9b933dc51890efacb8
    nama_produk TEXT,
    harga_modal INTEGER,
    harga_jual INTEGER,
    stok INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transaksi(
<<<<<<< HEAD
    id INTEGER PRIMARY KEY,
=======
    id INTEGER PRIMARY KEY AUTOINCREMENT,
>>>>>>> c0a3f9e9eb619b49ca8fde9b933dc51890efacb8
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
