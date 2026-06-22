import os
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key")

DATABASE = "smart_retail.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_db_connection()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS produk(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_produk TEXT,
        harga_modal INTEGER,
        harga_jual INTEGER,
        stok INTEGER
    )
    """)
    conn.execute("""
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


def initialize_database():
    create_tables()

    conn = get_db_connection()
    default_users = [
        ("admin", "admin123", "admin"),
        ("karyawan1", "karyawan1", "kasir"),
        ("karyawan2", "karyawan2", "kasir"),
        ("karyawan3", "karyawan3", "kasir"),
    ]
    for username, password, role in default_users:
        existing = conn.execute(
            "SELECT id, password, role FROM users WHERE username = ?", (username,)
        ).fetchone()
        password_hash = generate_password_hash(password)
        if not existing:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password_hash, role),
            )
        else:
            current_password = existing["password"]
            is_password_valid = check_password_hash(current_password, password)
            if not is_password_valid or existing["role"] != role:
                conn.execute(
                    "UPDATE users SET password = ?, role = ? WHERE username = ?",
                    (password_hash, role, username),
                )

    # Jangan isi produk awal secara otomatis; biarkan admin menambahkan sendiri.

    conn.commit()
    conn.close()


def get_user():
    return {
        "username": session.get("username"),
        "role": session.get("role"),
    }


def require_login():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

def require_admin():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))


initialize_database()


@app.route("/", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            error = "Username dan password wajib diisi."
        else:
            conn = get_db_connection()
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            conn.close()

            if user and check_password_hash(user["password"], password):
                session["logged_in"] = True
                session["username"] = user["username"]
                session["role"] = user["role"]
                return redirect(url_for("dashboard"))

            error = "Akun tidak ditemukan atau password salah."

    return render_template("login.html", error=error)


@app.route("/dashboard")
def dashboard():
    redirect_result = require_login()
    if redirect_result:
        return redirect_result

    conn = get_db_connection()
    total_produk = conn.execute("SELECT COUNT(*) AS total FROM produk").fetchone()["total"]
    total_transaksi = conn.execute("SELECT COUNT(*) AS total FROM transaksi").fetchone()["total"]
    total_pendapatan = conn.execute("SELECT COALESCE(SUM(total), 0) AS total FROM transaksi").fetchone()["total"]
    conn.close()

    return render_template(
        "dashboard.html",
        user=get_user(),
        total_produk=total_produk,
        total_transaksi=total_transaksi,
        total_pendapatan=total_pendapatan,
    )


@app.route("/produk", methods=["GET", "POST"])
def produk():
    redirect_result = require_login()
    if redirect_result:
        return redirect_result

    conn = get_db_connection()
    error = None
    success = None
    query = request.args.get("q", "").strip()

    if request.method == "POST":
        if session.get("role") != "admin":
            conn.close()
            return redirect(url_for("produk"))

        nama_produk = request.form.get("nama_produk", "").strip()
        harga_modal = request.form.get("harga_modal", "0").strip()
        harga_jual = request.form.get("harga_jual", "0").strip()
        stok = request.form.get("stok", "0").strip()

        if not nama_produk:
            error = "Nama produk wajib diisi."
        else:
            try:
                harga_modal = int(harga_modal)
                harga_jual = int(harga_jual)
                stok = int(stok)
                conn.execute(
                    "INSERT INTO produk (nama_produk, harga_modal, harga_jual, stok) VALUES (?, ?, ?, ?)",
                    (nama_produk, harga_modal, harga_jual, stok),
                )
                conn.commit()
                success = "Produk berhasil ditambahkan."
            except ValueError:
                error = "Harga modal, harga jual, dan stok harus berupa angka."

    if query:
        if query.isdigit():
            produk_list = conn.execute(
                "SELECT * FROM produk WHERE id = ? ORDER BY id DESC", (int(query),)
            ).fetchall()
        else:
            produk_list = conn.execute(
                "SELECT * FROM produk WHERE nama_produk LIKE ? ORDER BY id DESC",
                (f"%{query}%",),
            ).fetchall()
    else:
        produk_list = conn.execute("SELECT * FROM produk ORDER BY id DESC").fetchall()

    conn.close()
    return render_template(
        "produk.html",
        produk=produk_list,
        error=error,
        success=success,
        query=query,
        user=get_user(),
    )


@app.route("/produk/hapus/<int:product_id>")
def hapus_produk(product_id):
    redirect_result = require_login()
    if redirect_result:
        return redirect_result
    redirect_result = require_admin()
    if redirect_result:
        return redirect_result

    conn = get_db_connection()
    conn.execute("DELETE FROM produk WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("produk"))


@app.route("/produk/ubah/<int:product_id>", methods=["GET", "POST"])
def ubah_produk(product_id):
    redirect_result = require_login()
    if redirect_result:
        return redirect_result
    redirect_result = require_admin()
    if redirect_result:
        return redirect_result

    conn = get_db_connection()
    produk_item = conn.execute("SELECT * FROM produk WHERE id = ?", (product_id,)).fetchone()
    if not produk_item:
        conn.close()
        return redirect(url_for("produk"))

    error = None
    success = None
    if request.method == "POST":
        nama_produk = request.form.get("nama_produk", "").strip()
        harga_modal = request.form.get("harga_modal", "0").strip()
        harga_jual = request.form.get("harga_jual", "0").strip()
        stok = request.form.get("stok", "0").strip()

        if not nama_produk:
            error = "Nama produk wajib diisi."
        else:
            try:
                harga_modal = int(harga_modal)
                harga_jual = int(harga_jual)
                stok = int(stok)
                conn.execute(
                    "UPDATE produk SET nama_produk = ?, harga_modal = ?, harga_jual = ?, stok = ? WHERE id = ?",
                    (nama_produk, harga_modal, harga_jual, stok, product_id),
                )
                conn.commit()
                success = "Produk berhasil diperbarui."
                produk_item = conn.execute("SELECT * FROM produk WHERE id = ?", (product_id,)).fetchone()
            except ValueError:
                error = "Harga modal, harga jual, dan stok harus berupa angka."

    conn.close()
    return render_template(
        "update_produk.html",
        produk=produk_item,
        error=error,
        success=success,
        user=get_user(),
    )


@app.route("/transaksi", methods=["GET", "POST"])
def transaksi():
    redirect_result = require_login()
    if redirect_result:
        return redirect_result

    conn = get_db_connection()
    error = None
    success = None

    produk_list = conn.execute("SELECT * FROM produk ORDER BY nama_produk").fetchall()
    transaksi_list = conn.execute(
        "SELECT t.*, p.nama_produk FROM transaksi t JOIN produk p ON p.id = t.produk_id ORDER BY t.created_at DESC"
    ).fetchall()

    if request.method == "POST":
        produk_id = request.form.get("produk_id")
        jumlah = request.form.get("jumlah", "0").strip()

        try:
            produk_id = int(produk_id)
            jumlah = int(jumlah)
        except (ValueError, TypeError):
            error = "Pilih produk dan masukkan jumlah yang valid."
            conn.close()
            return render_template(
                "transaksi.html",
                produk=produk_list,
                transaksi=transaksi_list,
                error=error,
                success=success,
                user=get_user(),
            )

        produk_baru = conn.execute("SELECT * FROM produk WHERE id = ?", (produk_id,)).fetchone()

        if not produk_baru:
            error = "Produk tidak ditemukan."
        elif jumlah <= 0:
            error = "Jumlah transaksi harus lebih dari 0."
        elif produk_baru["stok"] < jumlah:
            error = "Stok produk tidak mencukupi."
        else:
            total = produk_baru["harga_jual"] * jumlah
            conn.execute(
                "INSERT INTO transaksi (produk_id, jumlah, total, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (produk_id, jumlah, total),
            )
            conn.execute(
                "UPDATE produk SET stok = stok - ? WHERE id = ?", (jumlah, produk_id)
            )
            conn.commit()
            success = "Transaksi berhasil disimpan."
            produk_list = conn.execute("SELECT * FROM produk ORDER BY nama_produk").fetchall()
            transaksi_list = conn.execute(
                "SELECT t.*, p.nama_produk FROM transaksi t JOIN produk p ON p.id = t.produk_id ORDER BY t.created_at DESC"
            ).fetchall()

    conn.close()
    return render_template(
        "transaksi.html",
        produk=produk_list,
        transaksi=transaksi_list,
        error=error,
        success=success,
        user=get_user(),
    )


@app.route("/laporan")
def laporan():
    redirect_result = require_login()
    if redirect_result:
        return redirect_result
    redirect_result = require_admin()
    if redirect_result:
        return redirect_result

    conn = get_db_connection()
    total_transaksi = conn.execute("SELECT COUNT(*) AS total FROM transaksi").fetchone()["total"]
    total_pendapatan = conn.execute("SELECT COALESCE(SUM(total), 0) AS total FROM transaksi").fetchone()["total"]
    total_produk = conn.execute("SELECT COUNT(*) AS total FROM produk").fetchone()["total"]
    total_keuntungan = conn.execute(
        "SELECT COALESCE(SUM((p.harga_jual - p.harga_modal) * t.jumlah), 0) AS total FROM transaksi t JOIN produk p ON p.id = t.produk_id"
    ).fetchone()["total"]
    terlaris = conn.execute(
        "SELECT p.nama_produk, SUM(t.jumlah) AS jumlah_terjual, SUM(t.total) AS pendapatan "
        "FROM transaksi t JOIN produk p ON p.id = t.produk_id "
        "GROUP BY p.id ORDER BY jumlah_terjual DESC LIMIT 5"
    ).fetchall()
    stok_rendah = conn.execute("SELECT * FROM produk WHERE stok <= 5 ORDER BY stok ASC").fetchall()
    conn.close()

    return render_template(
        "laporan.html",
        total_transaksi=total_transaksi,
        total_pendapatan=total_pendapatan,
        total_keuntungan=total_keuntungan,
        total_produk=total_produk,
        terlaris=terlaris,
        stok_rendah=stok_rendah,
        user=get_user(),
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
