import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import pymysql  # Required for MySQL connection
import plotly.express as px

# -------------------------------------------
# Page Setup
st.set_page_config(page_title="IMDb 2024 Dashboard", layout="wide")
st.title("🎬 IMDb 2024 Movie Dashboard")

# -------------------------------------------
# MySQL Connection Setup
def get_connection():
    username = "root"
    password = "9618172007"
    host = "localhost"
    database = "imdb_movies"
    return create_engine(f"mysql+pymysql://{username}:{password}@{host}/{database}")

# -------------------------------------------
# Load Data Function
@st.cache_data(show_spinner=True)
def load_data():
    try:
        engine = get_connection()
        df = pd.read_sql("SELECT * FROM movies_2024", engine)

        # 🔧 Clean column names
        df.columns = df.columns.str.strip()  # Remove any extra whitespace

        # 🧠 Handle lowercase or misnamed 'genre' column
        if "genre" in df.columns:
            df.rename(columns={"genre": "Genre"}, inplace=True)

        # 🧹 Drop rows where Genre is missing
        if "Genre" not in df.columns:
            st.error("❌ 'Genre' column is missing from the database table.")
            return pd.DataFrame()

        # 🔢 Convert columns to numeric
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
        df['Votes'] = pd.to_numeric(df['Votes'], errors='coerce')
        df['Duration'] = pd.to_numeric(df['Duration'], errors='coerce')

        # 🧼 Drop nulls
        df = df.dropna(subset=['Title', 'Rating', 'Votes', 'Duration', 'Genre'])

        # ⏱️ Create Duration in hours (for optional use)
        df['Duration_hours'] = df['Duration'] / 60

        return df

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# -------------------------------------------
# Load Data
df = load_data()

# -------------------------------------------
# Sidebar Filters
if not df.empty:
    st.sidebar.header("🔍 Filter Options")

    genres = df["Genre"].unique().tolist()
    selected_genres = st.sidebar.multiselect("Select Genre(s):", genres, default=genres)

    min_rating, max_rating = st.sidebar.slider("Select Rating Range:", 0.0, 10.0, (5.0, 10.0), step=0.1)
    min_votes, max_votes = st.sidebar.slider("Select Vote Range:", int(df["Votes"].min()), int(df["Votes"].max()), (1000, int(df["Votes"].max())))
    min_duration, max_duration = st.sidebar.slider("Select Duration (in minutes):", int(df["Duration"].min()), int(df["Duration"].max()), (60, 180))

    # -------------------------------------------
    # Filter DataFrame
    filtered_df = df[
        (df["Genre"].isin(selected_genres)) &
        (df["Rating"] >= min_rating) &
        (df["Rating"] <= max_rating) &
        (df["Votes"] >= min_votes) &
        (df["Votes"] <= max_votes) &
        (df["Duration"] >= min_duration) &
        (df["Duration"] <= max_duration)
    ]

    if filtered_df.empty:
        st.warning("No movies match your filter criteria. Please try adjusting the filters.")
        st.stop()

    # -------------------------------------------
    # Tabs for Display
    tab1, tab2, tab3 = st.tabs(["📋 Overview", "📊 Visualizations", "🔍 Data View"])

    # Tab 1 - Overview
    with tab1:
        st.subheader("🎯 Top 10 Movies by Rating")
        top_movies = filtered_df.sort_values(by="Rating", ascending=False).head(10)
        st.dataframe(top_movies[["Title", "Genre", "Rating", "Votes", "Duration"]], use_container_width=True)

    # Tab 2 - Visualizations
    with tab2:
        st.subheader("🎥 Genre-wise Movie Count")
        genre_count = filtered_df["Genre"].value_counts().reset_index()
        genre_count.columns = ["Genre", "Count"]
        fig = px.bar(genre_count, x="Genre", y="Count", color="Genre", title="Movies per Genre")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("⭐ Rating Distribution")
        fig2 = px.histogram(filtered_df, x="Rating", nbins=20, title="Rating Histogram", color="Genre")
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("⏱️ Duration Distribution")
        fig3 = px.histogram(filtered_df, x="Duration", nbins=20, title="Duration Histogram", color="Genre")
        st.plotly_chart(fig3, use_container_width=True)

    # Tab 3 - Data Table
    with tab3:
        st.subheader("🗃️ Filtered Movie Data")
        st.dataframe(filtered_df, use_container_width=True)

        # Download Button
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, "filtered_movies.csv", "text/csv")

else:
    st.warning("⚠️ No data available. Please check your database or CSV load.")
