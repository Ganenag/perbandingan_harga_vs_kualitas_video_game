import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIG & JUDUL ---
st.set_page_config(page_title="Steam Paradox Analysis", layout="wide")

st.title("🎮 The Steam Paradox: Popularity vs. Quality")
st.markdown("""
**Analisis Data Storytelling:** Apakah game populer selalu bagus? 
Aplikasi ini membedah hubungan **Popularitas (Owners)** vs **Kualitas (Rating)** dan mengelompokkan game ke dalam 4 kuadran psikologis.
""")
st.write("---")

# --- 2. PREPARASI DATA ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('games_selected.csv')
    except FileNotFoundError:
        st.error("File 'games_selected.csv' tidak ditemukan!")
        return pd.DataFrame()

    # --- A. Parsing Owners ---
    def parse_owners(x):
        if isinstance(x, str):
            parts = x.split('-')
            if len(parts) == 2:
                low = parts[0].replace(',', '').strip()
                high = parts[1].replace(',', '').strip()
                if low.isdigit() and high.isdigit():
                    return (int(low) + int(high)) / 2
        return 0
    
    df['average_owners'] = df['Owners'].apply(parse_owners)
    
    # --- B. Feature Engineering ---
    df['total_ratings'] = df['Positive'] + df['Negative']
    df['positive_rate'] = df.apply(
        lambda x: (x['Positive'] / x['total_ratings']) if x['total_ratings'] > 0 else 0, axis=1
    )
    
    # Filter Noise (Min 100 review)
    df_clean = df[df['total_ratings'] > 100].copy()

    # --- C. Klasifikasi Kategori (Logika Final) ---
    def classify_game(row):
        MILLION_BAR = 1000000  # 1 Juta
        MID_BAR = 50000        # 50 Ribu
        
        HIGH_SCORE = 0.85      # 85%
        SUPER_SCORE = 0.90     # 90%
        LOW_SCORE = 0.60       # 60%
        
        pos_rate = row['positive_rate']
        owners = row['average_owners']
        
        if owners >= MILLION_BAR:
            if pos_rate >= HIGH_SCORE:
                return "🔥 Worth the Hype"
            elif pos_rate <= LOW_SCORE:
                return "🥀 Overrated"
            else:
                return "Popular"
        elif owners >= MID_BAR:
            if pos_rate >= SUPER_SCORE:
                return "⭐ Underrated"
            else:
                return "Mainstream"
        else: # < 50k
            if pos_rate >= SUPER_SCORE:
                return "💎 Hidden Gem"
            else:
                return "Niche"

    df_clean['Category'] = df_clean.apply(classify_game, axis=1)
    
    # --- D. Parsing Genre (Untuk Filter) ---
    df_clean['Genres'] = df_clean['Genres'].fillna('')
    
    return df_clean

df = load_data()
if df.empty:
    st.stop()

# --- 3. SIDEBAR FILTER ---
st.sidebar.header("🔍 Filter & Pengaturan")

# A. Pengaturan Jumlah Data (FITUR BARU)
top_n = st.sidebar.slider("Jumlah Data Ditampilkan (Top N)", 5, 100, 10, step=5)

# B. Filter Genre
all_genres = set()
for genres_str in df['Genres']:
    if genres_str:
        for g in genres_str.split(','):
            all_genres.add(g.strip())
sorted_genres = sorted(list(all_genres))

selected_genres = st.sidebar.multiselect("Pilih Genre", sorted_genres, default=[])

# C. Filter Slider Data
min_owners = st.sidebar.slider("Minimal Owners", 0, 1000000, 10000, step=10000)
min_rating = st.sidebar.slider("Minimal Positive Rate", 0.0, 1.0, 0.5, step=0.05)

# --- LOGIKA FILTERING ---
df_filtered = df.copy()

if selected_genres:
    mask = df_filtered['Genres'].apply(lambda x: any(g in x for g in selected_genres))
    df_filtered = df_filtered[mask]

df_filtered = df_filtered[
    (df_filtered['average_owners'] >= min_owners) & 
    (df_filtered['positive_rate'] >= min_rating)
]

st.sidebar.markdown("---")
st.sidebar.write(f"**Total Data Tersaring:** {len(df_filtered)} Games")

# --- 4. VISUALISASI 1: TOP SELLERS vs TOP RATED (DIKEMBALIKAN) ---
st.subheader("1. The Popularity Paradox: Top Sellers vs Top Rated")
st.caption(f"Membandingkan {top_n} Game Terlaris vs {top_n} Game dengan Rating Tertinggi. Perhatikan perbedaan warnanya.")

c1, c2 = st.columns(2)

# Hitung tinggi chart dinamis agar tidak bertumpuk jika data banyak
dynamic_height = 400 + (top_n * 20)

# Chart 1: Top Sellers
with c1:
    st.markdown(f"**🏆 Top {top_n} Paling Laris (Owners)**")
    top_sellers = df_filtered.nlargest(top_n, 'average_owners').sort_values('average_owners', ascending=True)
    
    if not top_sellers.empty:
        fig_sellers = px.bar(
            top_sellers, x='average_owners', y='Name', orientation='h',
            color='positive_rate', color_continuous_scale='RdBu',
            range_color=[0.5, 1.0], # Merah (Jelek) ke Biru (Bagus)
            height=dynamic_height,
            title="Banyak Pemain Belum Tentu Bagus (Lihat Warna)"
        )
        st.plotly_chart(fig_sellers, use_container_width=True)
    else:
        st.warning("Data tidak cukup.")

# Chart 2: Top Rated
with c2:
    st.markdown(f"**❤️ Top {top_n} Rating Tertinggi (Quality)**")
    top_rated = df_filtered.nlargest(top_n, 'positive_rate').sort_values('positive_rate', ascending=True)
    
    if not top_rated.empty:
        fig_rated = px.bar(
            top_rated, x='positive_rate', y='Name', orientation='h',
            color='average_owners', color_continuous_scale='Viridis',
            height=dynamic_height,
            title="Game Terbaik Seringkali Kurang Populer (Lihat Warna)"
        )
        st.plotly_chart(fig_rated, use_container_width=True)
    else:
        st.warning("Data tidak cukup.")

st.write("---")

# --- 5. VISUALISASI 2: SCATTER PLOT (KUADRAN) ---
st.subheader("2. Peta Persebaran Game (Scatter Plot)")
st.caption("Lihat posisi game favoritmu berdasarkan filter Genre & Popularitas.")

if not df_filtered.empty:
    fig_scatter = px.scatter(
        df_filtered, 
        x="average_owners", 
        y="positive_rate", 
        color="Category",
        hover_name="Name",
        hover_data=["Genres"],
        log_x=True, 
        color_discrete_map={
            "🔥 Worth the Hype": "#FFD700",
            "🥀 Overrated": "#FF4B4B",
            "⭐ Underrated": "#00CC96",
            "💎 Hidden Gem": "#AB63FA",
            "Popular": "#7F7F7F",           
            "Mainstream": "#A0A0A0",
            "Niche": "#D3D3D3"
        },
        title=f"Analisis Kuadran {'(' + ', '.join(selected_genres) + ')' if selected_genres else '(Semua Genre)'}",
        height=600
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.warning("Tidak ada data yang cocok dengan filter ini.")

st.write("---")

# --- 6. TOP LIST PER KATEGORI (TABS) ---
st.subheader("3. Hall of Fame & Wall of Shame")
st.write(f"Jelajahi Top {top_n} game untuk setiap kategori psikologis berdasarkan filter genre di atas.")

tab1, tab2, tab3, tab4 = st.tabs([
    "🔥 Worth the Hype", 
    "🥀 Overrated (Terburuk)", 
    "⭐ Underrated", 
    "💎 Hidden Gem"
])

def show_top_table(dataframe, category_name, limit, sort_ascending=False):
    subset = dataframe[dataframe['Category'] == category_name]
    
    if subset.empty:
        st.info(f"Tidak ada game kategori '{category_name}' dengan filter saat ini.")
        return

    # Sorting & Limiting (menggunakan variabel limit/top_n)
    subset = subset.sort_values('positive_rate', ascending=sort_ascending).head(limit)

    st.dataframe(
        subset[['Name', 'Genres', 'positive_rate', 'average_owners', 'total_ratings']],
        column_config={
            "Name": "Nama Game",
            "positive_rate": st.column_config.ProgressColumn(
                "Quality Score", format="%.2f", min_value=0, max_value=1
            ),
            "average_owners": st.column_config.NumberColumn(
                "Est. Owners", format="%d"
            ),
            "total_ratings": st.column_config.NumberColumn("Total Reviews")
        },
        hide_index=True,
        use_container_width=True
    )

with tab1:
    st.caption(f"Top {top_n} Game Raksasa (>1 Juta Owners) dengan Rating > 85%.")
    show_top_table(df_filtered, "🔥 Worth the Hype", limit=top_n, sort_ascending=False)

with tab2:
    st.caption(f"Top {top_n} Game Raksasa dengan Rating Terendah (Diurutkan dari yang terburuk).")
    show_top_table(df_filtered, "🥀 Overrated", limit=top_n, sort_ascending=True)

with tab3:
    st.caption(f"Top {top_n} Game Menengah dengan Rating > 90%.")
    show_top_table(df_filtered, "⭐ Underrated", limit=top_n, sort_ascending=False)

with tab4:
    st.caption(f"Top {top_n} Game Kecil (<50k Owners) dengan Rating > 90%.")
    show_top_table(df_filtered, "💎 Hidden Gem", limit=top_n, sort_ascending=False)
