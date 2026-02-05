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

        # --- 4. VISUALISASI (GRID LAYOUT) ---
        st.sidebar.header("Pengaturan Visualisasi")
        jumlah_top = st.sidebar.slider("Jumlah Top Game:", 10, 50, 10, 10)
        
        # Tinggi grafik dinamis
        h_chart = 200 + (jumlah_top * 30)

        st.markdown("### 1️⃣ Zona Mainstream (Owners > 200k)")
        st.caption("Game-game besar yang sering dibicarakan orang. Apakah kualitasnya sebanding dengan popularitasnya?")

        # Filter Data Mainstream
        mainstream_games = df_filtered[df_filtered['average_owners'] >= 200000].copy()

        if not mainstream_games.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"✅ Worth The Hype")
                # Top Rated di Mainstream
                top_hype = mainstream_games.nlargest(jumlah_top, 'positive_rate').sort_values('positive_rate', ascending=True)
                
                fig_hype = px.bar(top_hype, x='positive_rate', y='name', orientation='h',
                                color='average_owners', color_continuous_scale='Greens',
                                title="Populer & Dicintai Gamer", labels={'positive_rate': 'Rating (%)'},
                                height=h_chart)
                fig_hype.update_layout(bargap=0.2, margin=dict(l=150), yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_hype, use_container_width=True)

            with col2:
                st.subheader(f"❌ Overrated")
                # Lowest Rated di Mainstream (nsmallest)
                top_over = mainstream_games.nsmallest(jumlah_top, 'positive_rate').sort_values('positive_rate', ascending=True)
                
                fig_over = px.bar(top_over, x='positive_rate', y='name', orientation='h',
                                color='average_owners', color_continuous_scale='Reds',
                                title="Populer tapi Banyak Hate", labels={'positive_rate': 'Rating (%)'},
                                height=h_chart)
                fig_over.update_layout(bargap=0.2, margin=dict(l=150), yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_over, use_container_width=True)
        else:
            st.warning("Tidak ada game Mainstream (>200k owners) di genre ini.")

        st.write("---")
        st.markdown("### 2️⃣ Zona Penemuan Baru (Niche & Hidden Gems)")
        
        col3, col4 = st.columns(2)

        # Filter Data Niche (50k - 200k)
        niche_games = df_filtered[
            (df_filtered['average_owners'] >= 50000) & 
            (df_filtered['average_owners'] < 200000)
        ].copy()

        with col3:
            st.subheader(f"🎭 Niche Favorites")
            st.caption("Game 'Kelas Menengah' (50k-200k Owners). Punya komunitas setia.")
            
            if not niche_games.empty:
                top_niche = niche_games.nlargest(jumlah_top, 'positive_rate').sort_values('positive_rate', ascending=True)
                
                fig_niche = px.bar(top_niche, x='positive_rate', y='name', orientation='h',
                                color='total_ratings', color_continuous_scale='Teal',
                                title="Jagoan Komunitas", labels={'positive_rate': 'Rating (%)'},
                                height=h_chart)
                fig_niche.update_layout(bargap=0.2, margin=dict(l=150), yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_niche, use_container_width=True)
            else:
                st.info("Tidak ada game Niche di kategori ini.")

        # Filter Data Hidden Gems (< 50k)
        # Tetap pakai filter minimal 100 review agar tidak muncul game abal-abal
        hidden_games = df_filtered[
            (df_filtered['average_owners'] < 50000) & 
            (df_filtered['total_ratings'] > 100)
        ].copy()

        with col4:
            st.subheader(f"💎 Hidden Gems")
            st.caption("Game 'Bawah Tanah' (<50k Owners). Jarang terdengar tapi rating tinggi.")
            
            if not hidden_games.empty:
                top_hidden = hidden_games.nlargest(jumlah_top, 'positive_rate').sort_values('positive_rate', ascending=True)
                
                fig_hidden = px.bar(top_hidden, x='positive_rate', y='name', orientation='h',
                                color='total_ratings', color_continuous_scale='Viridis',
                                title="Harta Karun Tersembunyi", labels={'positive_rate': 'Rating (%)'},
                                height=h_chart)
                fig_hidden.update_layout(bargap=0.2, margin=dict(l=150), yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_hidden, use_container_width=True)
            else:
                st.info("Tidak ada Hidden Gems yang valid (>100 reviews) di kategori ini.")

        # --- 5. KESIMPULAN ---
        st.write("---")
        st.metric("Total Game Dianalisis", len(df_filtered))
        
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {e}")

