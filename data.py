import sqlite3
import pandas as pd


def migrate_data():
    # 1. Load Data
    # Gabungkan semua file dulu
    all_files = ["data/2021.csv", "data/2022.csv", "data/2023.csv"]
    df_list = [pd.read_csv(f) for f in all_files]
    df = pd.concat(df_list, ignore_index=True)

    # Koneksi ke SQLite
    conn = sqlite3.connect("potensi_desa.db")
    cursor = conn.cursor()

    # 2. Buat Tabel sesuai ERD
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS KECAMATAN (
        id_kecamatan INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_kecamatan TEXT UNIQUE
    );

    CREATE TABLE IF NOT EXISTS DESA (
        id_desa INTEGER PRIMARY KEY AUTOINCREMENT,
        id_kecamatan INTEGER,
        nama_desa TEXT,
        UNIQUE(id_kecamatan, nama_desa),
        FOREIGN KEY (id_kecamatan) REFERENCES KECAMATAN (id_kecamatan)
    );

    CREATE TABLE IF NOT EXISTS INDIKATOR_TAHUNAN (
        id_indikator INTEGER PRIMARY KEY AUTOINCREMENT,
        id_desa INTEGER,
        tahun INTEGER,
        kepadatan_penduduk REAL,
        jml_menara_bts INTEGER,
        jml_bank_pemerintah INTEGER,
        jml_bank_swasta INTEGER,
        jml_bpr INTEGER,
        jml_kud INTEGER,
        jml_kopinkra INTEGER,
        jml_kospin INTEGER,
        jml_koperasi_lain INTEGER,
        jml_kelompok_pertokoan INTEGER,
        jml_pasar_permanen INTEGER,
        jml_pasar_semi_permanen INTEGER,
        jml_pasar_tanpa_bangunan INTEGER,
        jml_minimarket INTEGER,
        jml_hotel INTEGER,
        jml_penginapan INTEGER,
        jml_restoran INTEGER,
        FOREIGN KEY (id_desa) REFERENCES DESA (id_desa)
    );

    CREATE TABLE IF NOT EXISTS HASIL_CLUSTERING (
        id_hasil INTEGER PRIMARY KEY AUTOINCREMENT,
        id_desa INTEGER,
        tahun INTEGER,
        label_numerik INTEGER,
        kategori_deskriptif TEXT,
        FOREIGN KEY (id_desa) REFERENCES DESA (id_desa)
    );
    """)

    # 3. Insert Data Kecamatan
    kecamatans = df["Kecamatan"].unique()
    for kec in kecamatans:
        cursor.execute(
            "INSERT OR IGNORE INTO KECAMATAN (nama_kecamatan) VALUES (?)", (kec,)
        )

    # 4. Insert Data Desa (Amankan duplikat nama desa antar kecamatan)
    desa_unique = df.drop_duplicates(subset=["Kecamatan", "Desa"])
    for _, row in desa_unique.iterrows():
        cursor.execute(
            "SELECT id_kecamatan FROM KECAMATAN WHERE nama_kecamatan = ?",
            (row["Kecamatan"],),
        )
        kec_id = cursor.fetchone()[0]
        cursor.execute(
            """INSERT OR IGNORE INTO DESA (id_kecamatan, nama_desa) 
               VALUES (?, ?)""",
            (kec_id, row["Desa"]),
        )

    # 5. Insert Indikator Tahunan & Hasil Clustering
    for _, row in df.iterrows():
        # Cari ID berdasarkan Nama Desa DAN Nama Kecamatan agar tidak tertukar
        cursor.execute(
            """
            SELECT d.id_desa 
            FROM DESA d
            JOIN KECAMATAN k ON d.id_kecamatan = k.id_kecamatan
            WHERE d.nama_desa = ? AND k.nama_kecamatan = ?
        """,
            (row["Desa"], row["Kecamatan"]),
        )

        result = cursor.fetchone()
        if result is None:
            continue  # Lewati jika ada anomali data yang tidak ditemukan

        desa_id = result[0]

        # Indikator
        cursor.execute(
            """INSERT INTO INDIKATOR_TAHUNAN (id_desa, tahun, kepadatan_penduduk, jml_menara_bts, 
                          jml_bank_pemerintah, jml_bank_swasta, jml_bpr, jml_kud, jml_kopinkra, jml_kospin, jml_koperasi_lain,
                          jml_kelompok_pertokoan, jml_pasar_permanen, jml_pasar_semi_permanen, jml_pasar_tanpa_bangunan, jml_minimarket,
                          jml_hotel, jml_penginapan, jml_restoran)
                          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                desa_id,
                row["Tahun"],
                row["Kepadatan Penduduk"],
                row["Menara BTS"],
                row["Bank Pemerintah"],
                row["Bank Swasta"],
                row["BPR"],
                row["KUD"],
                row["Kopinkra"],
                row["Kospin"],
                row["Koperasi Lainnya"],
                row["Kelompok Pertokoan"],
                row["Pasar Bangunan Permanen"],
                row["Pasar Bangunan Semi Permanen"],
                row["Pasar Tanpa Bangunan"],
                row["Mini Market"],
                row["Hotel"],
                row["Penginapan"],
                row["Restoran"],
            ),
        )

        # Hasil Clustering
        cursor.execute(
            """INSERT INTO HASIL_CLUSTERING (id_desa, tahun, label_numerik, kategori_deskriptif)
               VALUES (?, ?, ?, ?)""",
            (desa_id, row["Tahun"], row["Cluster"], row["Kategori"]),
        )

    conn.commit()
    conn.close()
    print("Migrasi Berhasil: potensi_desa.db telah dibuat dengan data gabungan.")


if __name__ == "__main__":
    migrate_data()
