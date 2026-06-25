import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import psutil, os

# Konfigurasi Halaman - layout="wide" agar lega di desktop, tapi tetap adaptif di HP
st.set_page_config(
    page_title="Dashboard Potensi Desa Gianyar",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_db_connection():
    return sqlite3.connect("potensi_desa.db")


def load_data(tahun="Semua", kecamatan="Semua", kategori="Semua"):
    conn = get_db_connection()

    query = """
        SELECT 
            i.tahun,
            k.nama_kecamatan AS Kecamatan,
            d.nama_desa AS Desa,
            h.kategori_deskriptif AS Kategori,
            h.label_numerik AS Cluster,
            i.kepadatan_penduduk, i.jml_menara_bts, i.jml_bank_pemerintah, 
            i.jml_bank_swasta, i.jml_bpr, i.jml_kud, i.jml_kopinkra, 
            i.jml_kospin, i.jml_koperasi_lain, i.jml_kelompok_pertokoan, 
            i.jml_pasar_permanen, i.jml_pasar_semi_permanen, 
            i.jml_pasar_tanpa_bangunan, i.jml_minimarket, i.jml_hotel, 
            i.jml_penginapan, i.jml_restoran
        FROM INDIKATOR_TAHUNAN i
        JOIN DESA d ON i.id_desa = d.id_desa
        JOIN KECAMATAN k ON d.id_kecamatan = k.id_kecamatan
        JOIN HASIL_CLUSTERING h ON i.id_desa = h.id_desa AND i.tahun = h.tahun
        WHERE 1=1
    """

    if tahun != "Semua":
        query += f" AND i.tahun = {tahun}"
    if kecamatan != "Semua":
        query += f" AND k.nama_kecamatan = '{kecamatan}'"
    if kategori != "Semua":
        query += f" AND h.kategori_deskriptif = '{kategori}'"

    df = pd.read_sql(query, conn)
    conn.close()
    return df


# --- AMBIL DATA UNTUK FILTER ---
conn = get_db_connection()
list_kecamatan = ["Semua"] + [
    r[0] for r in conn.execute("SELECT nama_kecamatan FROM KECAMATAN").fetchall()
]
list_kategori = ["Semua"] + [
    r[0]
    for r in conn.execute(
        "SELECT DISTINCT kategori_deskriptif FROM HASIL_CLUSTERING"
    ).fetchall()
]
conn.close()


# --- SIDEBAR: FILTER DATA ---
with st.sidebar:
    # Optional: Tambahkan logo jika ada

    st.header("Filter Data")

    selected_tahun = st.selectbox("Pilih Tahun", ["Semua", 2021, 2022, 2023])
    selected_kec = st.selectbox("Pilih Kecamatan", list_kecamatan)
    selected_kat = st.selectbox("Pilih Kategori Potensi", list_kategori)

    st.markdown("---")
    st.caption("Dashboard Potensi Desa © 2026")
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / (1024 * 1024)
    st.caption(f"🧠 Memori saat ini: {mem_mb:.1f} MB")


# Load data berdasarkan filter
df_final = load_data(selected_tahun, selected_kec, selected_kat)


# --- MAIN CONTENT ---
st.title(" Dashboard Potensi Desa Kabupaten Gianyar")
st.markdown("---")

# --- 3 KARTU RINGKASAN ---
st.markdown("### Ringkasan Data")
card1, card2, card3 = st.columns(3)

if not df_final.empty:
    total_desa = len(df_final)
    jumlah_kategori = df_final["Kategori"].nunique()

    # Mencari kategori dominan (persentase terbesar)
    kategori_terbanyak = df_final["Kategori"].value_counts().index[0]
    persentase_terbanyak = (
        df_final["Kategori"].value_counts().iloc[0] / total_desa
    ) * 100
    teks_distribusi = f"{kategori_terbanyak} ({persentase_terbanyak:.1f}%)"
else:
    total_desa = 0
    jumlah_kategori = 0
    teks_distribusi = "Tidak ada data"

with card1:
    st.metric("Total Desa", total_desa)
with card2:
    st.metric("Jumlah Kategori Cluster", jumlah_kategori)
with card3:
    st.metric("Kategori Terbanyak", teks_distribusi)

st.markdown("---")


# --- GRAFIK (Responsive View - Satu Baris Masing-Masing) ---
if not df_final.empty:
    # 1. Grafik Donut (Pie Chart)
    st.subheader("Persentase Kategori Potensi")
    fig_pie = px.pie(df_final, names="Kategori", hole=0.3)

    # Menyesuaikan margin dan memindah legenda ke bawah agar bersahabat di layar HP
    fig_pie.update_layout(
        height=500,  # Dibuat sedikit lebih tinggi agar proporsional saat full width
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)  # Jarak antar grafik

    # 2. Grafik Batang (Bar Chart)
    st.subheader("Sebaran Kategori Potensi per Kecamatan")
    df_bar = (
        df_final.groupby(["Kecamatan", "Kategori"]).size().reset_index(name="Jumlah")
    )
    fig_bar = px.bar(
        df_bar,
        x="Kecamatan",
        y="Jumlah",
        color="Kategori",
        barmode="group",
        text_auto=True,
    )

    # Menyesuaikan margin dan memindah legenda ke bawah agar tidak memakan ruang chart
    fig_bar.update_layout(
        height=800,
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        xaxis_title=None,
    )
    st.plotly_chart(fig_bar, use_container_width=True)


st.markdown("---")


# --- TABEL DATA ---
st.subheader("Tabel Detail Data & Hasil Clustering")
search = st.text_input("Cari Nama Desa...", placeholder="Ketik nama desa...")

if search:
    df_display = df_final[df_final["Desa"].str.contains(search, case=False)].copy()
else:
    df_display = df_final.copy()

if not df_display.empty:
    df_display.index = range(1, len(df_display) + 1)

# Tabel akan otomatis ada scroll-bar horizontal di HP
st.dataframe(df_display, use_container_width=True)
st.markdown("---")


# --- BAGIAN CETAK LAPORAN ---
st.subheader("🖨️ Unduh Laporan")
st.write("Unduh laporan analisis lengkap di bawah ini.")

# Tombol download diubah menjadi kolom agar rapi di desktop dan bertumpuk di HP

pdf_path = "data/laporan.pdf"
try:
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()

    st.download_button(
        label="Download Laporan Analisis (PDF)",
        data=pdf_data,
        file_name="laporan_analisis_potensi_desa.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
except FileNotFoundError:
    st.error("File laporan.pdf tidak ditemukan di folder data.")


import time

start = time.time()
df_final = load_data(selected_tahun, selected_kec, selected_kat)
elapsed = time.time() - start

# Tampilkan sementara untuk testing, bisa dihapus setelah selesai
st.caption(f"⏱️ Data dimuat dalam {elapsed:.3f} detik")
