import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG & JUDUL ---
st.set_page_config(page_title="Steam Paradox Analysis", layout="wide")

st.title("🎮 The Steam Paradox: Popularity vs Quality")
st.markdown("""
**Analisis Data Storytelling:** Banyak orang mengira game yang *Best-Seller* pasti bagus. Aplikasi ini membandingkan data **Game Terlaris** melawan **Game Dengan Rating Tertinggi** di Steam untuk membuktikan apakah hipotesis itu benar.
""")
st.write("---")

# --- 2. PREPARASI DATA ---
@st.cache_data
def load_data():
    # Membaca file steam.csv
    try:
        df = pd.read_csv('steam.csv')
    except FileNotFoundError:
        st.error("File 'steam.csv' belum diupload! Silakan upload ke panel kiri.")
        return pd.DataFrame()

    def parse_owners(x):
        if isinstance(x, str):
            low, high = x.split('-')
            return (int(low) + int(high)) / 2
        return 0
    
    df['average_owners'] = df['owners'].apply(parse_owners)
    df['total_ratings'] = df['positive_ratings'] + df['negative_ratings']
    
    # Filter minimal 100 review agar data valid
    df_clean = df[df['total_ratings'] > 100].copy()
    df_clean['positive_rate'] = (df_clean['positive_ratings'] / df_clean['total_ratings']) * 100
    return df_clean

df = load_data()

if not df.empty:
    # --- 3. SIDEBAR FILTER ---
    st.sidebar.header("Filter Data")
    # Mengambil daftar genre unik
    try:
        genre_list = df['genres'].str.split(';').explode().unique()
        selected_genre = st.sidebar.selectbox("Pilih Genre Game:", ["All Genres"] + sorted(list(genre_list)))

        if selected_genre != "All Genres":
            df_filtered = df[df['genres'].str.contains(selected_genre, na=False)]
        else:
            df_filtered = df

        # --- 4. VISUALISASI ---
        st.sidebar.header("Pengaturan Visualisasi")
        # Slider untuk mengatur jumlah data yang ditampilkan
        jumlah_top = st.sidebar.slider("Jumlah Top Game yang Ditampilkan:", min_value=10, max_value=100, value=10, step=10)

        # Hitung tinggi grafik agar tidak gepeng. 
        # Sedikit saya naikkan jadi 35 pixel per batang untuk ruang lebih lega.
        dynamic_height = 200 + (jumlah_top * 35)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader(f"💰 Top {jumlah_top} Paling Populer")
            # Ubah .nlargest(10) menjadi .nlargest(jumlah_top)
            top_popular = df_filtered.nlargest(jumlah_top, 'average_owners').sort_values('average_owners', ascending=True)
            
            fig_pop = px.bar(top_popular, x='average_owners', y='name', orientation='h',
                            color='positive_rate', color_continuous_scale='RdYlGn',
                            title=f"Populer: Apakah Ratingnya Bagus (Hijau)?",
                            height=dynamic_height) # <--- Set tinggi chart
            
            # [TAMBAHAN] Mengatur layout untuk membuat batang lebih tebal
            fig_pop.update_layout(
                bargap=0.2, # Mengurangi jarak antar batang (nilai 0 sampai 1)
                yaxis={'categoryorder':'total ascending'}, # Memastikan urutan benar
                margin=dict(l=150) # Memberi ruang lebih untuk nama game yang panjang
            )
            
            st.plotly_chart(fig_pop, use_container_width=True)

        with col2:
            st.subheader(f"⭐ Top {jumlah_top} Paling Disukai")
            # Ubah .nlargest(10) menjadi .nlargest(jumlah_top)
            top_quality = df_filtered.nlargest(jumlah_top, 'positive_rate').sort_values('positive_rate', ascending=True)
            
            fig_qual = px.bar(top_quality, x='positive_rate', y='name', orientation='h',
                            color='average_owners', color_continuous_scale='Blues',
                            title=f"Kualitas: Seberapa Populer (Biru Tua)?",
                            height=dynamic_height) # <--- Set tinggi chart
            
            # [TAMBAHAN] Mengatur layout untuk membuat batang lebih tebal
            fig_qual.update_layout(
                bargap=0.2, # Mengurangi jarak antar batang (nilai 0 sampai 1)
                yaxis={'categoryorder':'total ascending'}, # Memastikan urutan benar
                margin=dict(l=150) # Memberi ruang lebih untuk nama game yang panjang
            )
            
            st.plotly_chart(fig_qual, use_container_width=True)

        # --- 5. KESIMPULAN ---
        st.write("---")
        # Korelasi tetap dihitung dari SELURUH data yang difilter, bukan cuma Top 100 agar akurat
        correlation = df_filtered['average_owners'].corr(df_filtered['positive_rate'])
        st.metric("Korelasi Global (Popularitas vs Kualitas)", f"{correlation:.4f}")
        
        if correlation < 0.2:
            st.warning(f"**Paradoks Terbukti:** Korelasi sangat rendah ({correlation:.2f}). Game laris tidak menjamin kepuasan tinggi.")
        else:
            st.success("Ada hubungan positif antara popularitas dan kualitas.")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {e}")
