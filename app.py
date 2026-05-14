import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(page_title="Dashboard Potensi Desa Gianyar", layout="wide")


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


st.title("Dashboard Potensi Desa Kabupaten Gianyar")

# --- NAVBAR / HORIZONTAL FILTER ---
st.markdown("### Filter Data")
nav1, nav2, nav3 = st.columns(3)

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

with nav1:
    selected_tahun = st.selectbox("Pilih Tahun", ["Semua", 2021, 2022, 2023])
with nav2:
    selected_kec = st.selectbox("Pilih Kecamatan", list_kecamatan)
with nav3:
    selected_kat = st.selectbox("Pilih Kategori Potensi", list_kategori)

st.markdown("---")

# Load data berdasarkan filter
df_final = load_data(selected_tahun, selected_kec, selected_kat)


# --- 3 KARTU RINGKASAN ---
st.markdown("### Ringkasan Data")
card1, card2, card3 = st.columns(3)

if not df_final.empty:
    total_desa = len(df_final)
    jumlah_kategori = df_final["Kategori"].nunique()

    # Mencari kategori dominan (persentase terbesar) untuk ditampilkan di Card 3
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

# --- TABEL DATA ---
st.subheader("Tabel Detail Data dan Hasil Clustering")
search = st.text_input("Cari Nama Desa...")

if search:
    df_display = df_final[df_final["Desa"].str.contains(search, case=False)].copy()
else:
    df_display = df_final.copy()

if not df_display.empty:
    df_display.index = range(1, len(df_display) + 1)

st.dataframe(df_display, use_container_width=True)

# --- GRAFIK (Ukuran Besar & Full Width) ---
if not df_final.empty:
    # 1. Pie Chart
    st.subheader("Persentase Kategori Potensi Desa")
    fig_pie = px.pie(df_final, names="Kategori")
    fig_pie.update_layout(height=450)  # Memperbesar tinggi grafik
    st.plotly_chart(fig_pie, use_container_width=True)

    # Penjelasan di bawah grafik pie
    st.info(
        "💡 **Penjelasan Grafik:** Pie chart di atas menunjukkan persentase distribusi desa berdasarkan kategori potensinya. Ini membantu Anda melihat porsi kategori mana yang paling mendominasi di Kabupaten Gianyar (atau di area yang sedang Anda filter)."
    )

    st.markdown("<br>", unsafe_allow_html=True)  # Jarak kosong

    # 2. Bar Chart
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
    fig_bar.update_layout(height=500)  # Memperbesar tinggi grafik
    st.plotly_chart(fig_bar, use_container_width=True)

    # Penjelasan di bawah grafik bar
    st.info(
        "💡 **Penjelasan Grafik:** Grafik batang di atas membandingkan jumlah desa per kategori potensi di masing-masing kecamatan. Anda bisa menggunakannya untuk membandingkan kecamatan mana yang memiliki desa paling maju atau tertinggal."
    )

# --- BAGIAN CETAK LAPORAN (Tambahkan di bagian paling bawah sebelum st.markdown("---")) ---

# --- BAGIAN CETAK LAPORAN ---

st.subheader("🖨️ Cetak Laporan")
st.write("Unduh data hasil filter atau laporan analisis lengkap.")

# Layout kolom untuk tombol agar terlihat rapi
col1, col2 = st.columns(2)

with col1:
    if not df_final.empty:
        # Mengubah dataframe ke CSV
        csv = df_final.to_csv(index=False).encode("utf-8")

        # Membuat tombol download CSV
        st.download_button(
            label="📥 Download Data Filter (CSV)",
            data=csv,
            file_name=f"Laporan_Potensi_Desa_{selected_kec}_{selected_tahun}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.warning("Tidak ada data filter untuk diunduh.")

with col2:
    # Path ke file PDF
    pdf_path = "data/laporan.pdf"

    try:
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()

        # Membuat tombol download PDF
        st.download_button(
            label="📄 Download Laporan Analisis (PDF)",
            data=pdf_data,
            file_name="laporan_analisis_potensi_desa.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    except FileNotFoundError:
        st.error("File laporan.pdf tidak ditemukan di folder data.")

st.markdown("---")
