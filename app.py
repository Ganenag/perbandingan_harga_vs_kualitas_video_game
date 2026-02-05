import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG & JUDUL ---
st.set_page_config(page_title="Steam Paradox Analysis", layout="wide")

st.title("🎮 The Steam Paradox: Popularity vs. Quality")
st.markdown("""
**Analisis Data Storytelling:** Banyak orang mengira game yang *Best-Seller* pasti bagus. 
Aplikasi ini membandingkan data **Game Terlaris** melawan **Game Dengan Rating Tertinggi** di Steam untuk membuktikan apakah hipotesis itu benar.
""")
st.write("---")

# --- 2. PREPARASI DATA ---
@st.cache_data
def load_data():
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
    
    # Filter Genre
    try:
        genre_list = df['genres'].str.split(';').explode().unique()
        selected_genre = st.sidebar.selectbox("Pilih Genre Game:", ["All Genres"] + sorted(list(genre_list)))

        if selected_genre != "All Genres":
            df_filtered = df[df['genres'].str.contains(selected_genre, na=False)]
        else:
            df_filtered = df
    except:
        df_filtered = df

    # Slider untuk jumlah data (berlaku untuk semua grafik)
    jumlah_top = st.sidebar.slider("Jumlah Game yang Ditampilkan:", min_value=10, max_value=100, value=10, step=10)
    
    # Hitung tinggi grafik dinamis
    dynamic_height = 200 + (jumlah_top * 30)

    # --- 4. VISUALISASI UTAMA: POPULARITAS VS KUALITAS ---
    st.header("📊 Analisis Utama: The Paradox")
    st.caption("Membandingkan langsung antara game yang paling banyak dibeli dengan game yang paling disukai user.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"💰 Top {jumlah_top} Paling Populer")
        # Diurutkan berdasarkan OWNERS
        top_popular = df_filtered.nlargest(jumlah_top, 'average_owners').sort_values('average_owners', ascending=True)
        
        fig_pop = px.bar(top_popular, x='average_owners', y='name', orientation='h',
                        color='positive_rate', color_continuous_scale='RdYlGn',
                        title="Populer: Apakah Ratingnya Bagus (Hijau)?",
                        height=dynamic_height)
        
        fig_pop.update_layout(bargap=0.2, margin=dict(l=150), yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_pop, use_container_width=True)

    with col2:
        st.subheader(f"⭐ Top {jumlah_top} Paling Disukai")
        # Diurutkan berdasarkan RATING
        top_quality = df_filtered.nlargest(jumlah_top, 'positive_rate').sort_values('positive_rate', ascending=True)
        
        fig_qual = px.bar(top_quality, x='positive_rate', y='name', orientation='h',
                        color='average_owners', color_continuous_scale='Blues',
                        title="Kualitas: Seberapa Populer (Biru Tua)?",
                        height=dynamic_height)
        
        fig_qual.update_layout(bargap=0.2, margin=dict(l=150), yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_qual, use_container_width=True)

    # --- KESIMPULAN PARADOKS ---
    correlation = df_filtered['average_owners'].corr(df_filtered['positive_rate'])
    st.metric("Skor Korelasi (Popularitas vs Kualitas)", f"{correlation:.4f}")
    
    if correlation < 0.2:
        st.warning(f"**Paradoks Terkonfirmasi:** Korelasi sangat rendah ({correlation:.2f}). Menjadi populer tidak menjamin game tersebut disukai (rating tinggi).")
    else:
        st.success("Paradoks tidak terbukti di genre ini. Ada hubungan positif antara popularitas dan kualitas.")

    st.write("---")

    # --- 5. FITUR EXTRA: SEGMENTASI PASAR (Deep Dive) ---
    # Menggunakan Expander agar tidak memenuhi layar jika user tidak ingin melihatnya
    with st.expander("🔍 Klik untuk melihat Analisis Detail (Underrated, Hype, & Overrated)", expanded=True):
        st.header("Analisis 4 Kuadran: Hype vs Hidden Gems")
        st.markdown("""
        Kami membagi game menjadi 3 kelas berdasarkan jumlah pemilik (*Owners*):
        - **Mainstream:** > 200.000 owners (Game Hype & Overrated ada di sini)
        - **Niche:** 50.000 - 200.000 owners (Game komunitas)
        - **Hidden Gems:** < 50.000 owners (Game bagus yang jarang diketahui)
        """)
        
        # --- ZONA MAINSTREAM ---
        st.subheader("1️⃣ Zona Mainstream (>200k Owners)")
        mainstream_games = df_filtered[df_filtered['average_owners'] >= 200000].copy()
        
        if not mainstream_games.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.caption("✅ Worth The Hype (Populer & Bagus)")
                top_hype = mainstream_games.nlargest(jumlah_top, 'positive_rate').sort_values('positive_rate', ascending=True)
                fig_hype = px.bar(top_hype, x='positive_rate', y='name', orientation='h',
                                color='average_owners', color_continuous_scale='Greens',
                                height=dynamic_height)
                fig_hype.update_layout(bargap=0.2, margin=dict(l=150), yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_hype, use_container_width=True)
            
            with c2:
                st.caption("❌ Overrated (Populer tapi Rating Rendah)")
                top_over = mainstream_games.nsmallest(jumlah_top, 'positive_rate').sort_values('positive_rate', ascending=True)
                fig_over = px.bar(top_over, x='positive_rate', y='name', orientation='h',
                                color='average_owners', color_continuous_scale='Reds',
                                height=dynamic_height)
                fig_over.update_layout(bargap=0.2, margin=dict(l=150), yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_over, use_container_width=True)
        else:
            st.info("Tidak ada data Mainstream di genre ini.")

        # --- ZONA NICHE & HIDDEN ---
        st.subheader("2️⃣ Zona Penemuan (Niche & Indie)")
        c3, c4 = st.columns(2)
        
        # Niche
        niche_games = df_filtered[(df_filtered['average_owners'] >= 50000) & (df_filtered['average_owners'] < 200000)].copy()
        with c3:
            st.caption("🎭 Niche Favorites (50k - 200k Owners)")
            if not niche_games.empty:
                top_niche = niche_games.nlargest(jumlah_top, 'positive_rate').sort_values('positive_rate', ascending=True)
                fig_niche = px.bar(top_niche, x='positive_rate', y='name', orientation='h',
                                color='total_ratings', color_continuous_scale='Teal',
                                height=dynamic_height)
                fig_niche.update_layout(bargap=0.2, margin=dict(l=150), yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_niche, use_container_width=True)
            else:
                st.info("Data kosong.")

        # Hidden Gems
        hidden_games = df_filtered[(df_filtered['average_owners'] < 50000) & (df_filtered['total_ratings'] > 100)].copy()
        with c4:
            st.caption("💎 Hidden Gems (< 50k Owners)")
            if not hidden_games.empty:
                top_hidden = hidden_games.nlargest(jumlah_top, 'positive_rate').sort_values('positive_rate', ascending=True)
                fig_hidden = px.bar(top_hidden, x='positive_rate', y='name', orientation='h',
                                color='total_ratings', color_continuous_scale='Viridis',
                                height=dynamic_height)
                fig_hidden.update_layout(bargap=0.2, margin=dict(l=150), yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_hidden, use_container_width=True)
            else:
                st.info("Data kosong.")

    st.write("---")
    st.caption(f"Total Database: {len(df)} Games | Filtered: {len(df_filtered)} Games")
