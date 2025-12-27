import streamlit as st
import pandas as pd
from pathlib import Path

# ======================================================
# KONFIGURASI HALAMAN
# ======================================================
st.set_page_config(
    page_title="Dashboard Harga Pangan Daerah",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================================
# SIDEBAR - PILIH WILAYAH & FILE
# ======================================================
st.sidebar.header("📍 Pilih Wilayah")

# Mapping nama wilayah ke nama file
data_files = {
    "DKI Jakarta": "data dki jkt.xlsx - data dki jkt.csv",
    "Jambi": "data jambi.xlsx - data jambi.csv",
    "Gorontalo": "data gorontalo.xlsx - data gorontalo.csv",
    "Aceh": "data aceh.xlsx - data aceh.csv"
}

selected_region = st.sidebar.selectbox(
    "Pilih Provinsi/Daerah:",
    options=list(data_files.keys())
)

file_path = data_files[selected_region]

# ======================================================
# JUDUL UTAMA (DINAMIS)
# ======================================================
st.title(f"📈 Dashboard Harga Komoditas Pangan Utama di {selected_region}")

st.markdown(f"""
Dashboard ini menggambarkan dinamika harga komoditas pangan strategis di **{selected_region}** selama periode yang tersedia. Visualisasi ini membantu memantau tren kenaikan atau penurunan harga 
komoditas seperti **beras, daging ayam, daging sapi, bawang merah, cabai rawit, minyak goreng, dan gula pasir**.
""")

# ======================================================
# FOTO DI ATAS NAMA ANGGOTA (Opsional)
# ======================================================
foto_path = Path("foto/foto.jpg")
if foto_path.exists():
    st.image(
        str(foto_path),
        caption="Ilustrasi Komoditas Pangan",
        use_container_width=True
    )

# ======================================================
# NAMA ANGGOTA
# ======================================================
with st.expander("👥 Lihat Anggota Kelompok"):
    anggota = [
        "Jibral Yusuf Nazar (021002301001)",
        "David Indra Setiawan (021002305021)",
        "Dimas Wahyu Saputra (021002302003)"
    ]
    col1, col2, col3 = st.columns(3)
    for idx, a in enumerate(anggota):
        with [col1, col2, col3][idx]:
            st.markdown(f"**{a}**")

st.divider()

# ======================================================
# LOAD DATA CSV
# ======================================================
try:
    if not Path(file_path).exists():
        st.error(f"❌ File '{file_path}' tidak ditemukan!")
        st.info("💡 Pastikan file CSV berada di folder yang sama dengan script ini.")
        st.stop()
    
    # Logika load data berbeda untuk Gorontalo karena format header
    if selected_region == "Gorontalo":
        # Gorontalo memiliki header di baris ke-2 (index 1)
        df = pd.read_csv(file_path, header=1)
        # Kolom tanggal bernama 'Komoditas (Rp)' di file Gorontalo
        date_col_name = 'Komoditas (Rp)'
    else:
        # Default load
        df = pd.read_csv(file_path)
        # Cek kemungkinan nama kolom tanggal (kadang ada spasi 'tahun ')
        date_col_name = 'tahun'
        if 'tahun ' in df.columns:
            date_col_name = 'tahun '
        elif 'tahun' in df.columns:
            date_col_name = 'tahun'
    
    # Validasi data tidak kosong
    if df.empty:
        st.error("❌ File CSV kosong!")
        st.stop()

    # Rename kolom tanggal menjadi standar 'tahun_raw' untuk diproses
    df = df.rename(columns={date_col_name: 'tahun_raw'})
    
    # Membersihkan nama kolom (strip spasi di awal/akhir nama kolom)
    df.columns = df.columns.str.strip()

    # Konversi kolom tahun menjadi datetime
    if "tahun_raw" in df.columns:
        # Bersihkan data tanggal (misal '01/ 2019' -> hilangkan spasi ekstra jika perlu)
        df["tahun_date"] = pd.to_datetime(
            df["tahun_raw"].astype(str).str.strip(), 
            errors="coerce"
        )
        
        # Hapus baris dengan tahun invalid (NaT)
        df = df.dropna(subset=["tahun_date"])
        
        # Sort berdasarkan tanggal
        df = df.sort_values("tahun_date")
    else:
        st.error(f"❌ Kolom tanggal tidak ditemukan dalam data {selected_region}!")
        st.stop()

    # ==================================================
    # SIDEBAR FILTER
    # ==================================================
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Pengaturan Tampilan")
    
    # Filter tahun
    if not df["tahun_date"].empty:
        min_year = int(df["tahun_date"].dt.year.min())
        max_year = int(df["tahun_date"].dt.year.max())
        
        year_range = st.sidebar.slider(
            "Pilih Rentang Tahun:",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year)
        )
        
        # Filter dataframe berdasarkan tahun
        df_filtered = df[
            (df["tahun_date"].dt.year >= year_range[0]) & 
            (df["tahun_date"].dt.year <= year_range[1])
        ]
    else:
        df_filtered = df
    
    show_table = st.sidebar.checkbox(
        "📊 Tampilkan Tabel Data",
        value=False
    )

    if show_table:
        st.subheader(f"📋 Data Lengkap: {selected_region}")
        st.dataframe(
            df_filtered.drop(columns=['tahun_date']).style.format(precision=0, thousands=".", decimal=","),
            use_container_width=True,
            height=300
        )

    # ==================================================
    # BAGIAN ANALISIS GRAFIK
    # ==================================================
    st.divider()
    st.header(f"📊 Analisis Harga Pangan di {selected_region}")
    
    target_komoditas = [
        "Beras",
        "Daging Ayam",
        "Daging Sapi",
        "Bawang Merah",
        "Cabai Rawit",
        "Minyak Goreng",
        "Gula Pasir"
    ]

    # Cari komoditas yang ada di data (match nama kolom)
    komoditas_plot = [
        col for col in target_komoditas
        if col in df_filtered.columns
    ]
    
    # Jika tidak ada match langsung, coba cari yang mirip (opsional, tapi data Anda cukup konsisten)
    if not komoditas_plot:
        # Fallback: ambil semua kolom numerik kecuali tahun
        numeric_cols = df_filtered.select_dtypes(include=['float64', 'int64']).columns.tolist()
        komoditas_plot = [c for c in numeric_cols if c not in ['tahun_raw', 'tahun_date']]

    if not komoditas_plot:
        st.error("❌ Tidak ada kolom komoditas yang dikenali dalam data!")
        st.stop()

    # Multiselect
    selected_commodities = st.multiselect(
        "🔍 Pilih Komoditas untuk Ditampilkan:",
        options=komoditas_plot,
        default=komoditas_plot,
    )

    if selected_commodities:
        # Buat chart data
        chart_data = df_filtered.set_index("tahun_date")[selected_commodities]
        
        # Hapus nilai NaN jika semua kolom NaN
        chart_data = chart_data.dropna(how='all')

        # Tampilkan grafik
        st.subheader("📈 Tren Harga Waktu ke Waktu")
        st.line_chart(chart_data, height=500)

        # Tampilkan statistik ringkas
        st.subheader("🔢 Statistik Harga (Periode Terpilih)")
        
        stats_data = []
        for commodity in selected_commodities:
            data = df_filtered[commodity].dropna()
            if not data.empty:
                current_price = data.iloc[-1]
                start_price = data.iloc[0]
                change = ((current_price - start_price) / start_price * 100)
                
                stats_data.append({
                    "Komoditas": commodity,
                    "Rata-rata": f"Rp {data.mean():,.0f}",
                    "Tertinggi": f"Rp {data.max():,.0f}",
                    "Terendah": f"Rp {data.min():,.0f}",
                    "Harga Awal": f"Rp {start_price:,.0f}",
                    "Harga Akhir": f"Rp {current_price:,.0f}",
                    "Perubahan": f"{change:+.2f}%"
                })
        
        if stats_data:
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(
                stats_df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "Perubahan": st.column_config.TextColumn(
                        "Perubahan (%)",
                        help="Perubahan harga dari awal periode terpilih ke akhir periode terpilih"
                    )
                }
            )

        # ==================================================
        # KESIMPULAN GENERIC (Karena data dinamis)
        # ==================================================
        st.divider()
        st.markdown(f"""
        ### 💡 Insight Data {selected_region}
        
        Berdasarkan grafik dan statistik di atas untuk periode **{year_range[0]} - {year_range[1]}**:
        
        * **Volatilitas:** Perhatikan komoditas dengan selisih harga tertinggi dan terendah yang besar (biasanya Cabai Rawit atau Bawang Merah), yang mengindikasikan sensitivitas terhadap musim atau pasokan.
        * **Tren:** Nilai perubahan positif (+) menunjukkan kenaikan harga selama periode yang dipilih, sedangkan negatif (-) menunjukkan penurunan.
        * **Stabilitas:** Komoditas dengan grafik mendatar cenderung memiliki pasokan dan kebijakan harga yang lebih stabil (misalnya seringkali Beras atau Minyak Goreng).
        
        _Catatan: Analisis mendalam dapat dilakukan dengan membandingkan pola kenaikan harga dengan kejadian ekonomi atau musim panen di {selected_region}._
        """)

    else:
        st.warning("⚠️ Silakan pilih setidaknya satu komoditas untuk menampilkan grafik.")

except Exception as e:
    st.error(f"❌ Terjadi kesalahan saat memuat data:")
    st.exception(e)
