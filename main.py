import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ------------------------------------------------------------------------------
# Page setup
# ------------------------------------------------------------------------------
st.set_page_config(page_title="Climate Dashboard for COP32", layout="wide")
st.title("African Climate Trends - Interactive Dashboard")
st.markdown("*Data from NASA POWER | Jan 2015 - Mar 2026*")

# ------------------------------------------------------------------------------
# 1. Load data
# ------------------------------------------------------------------------------
@st.cache_data
def load_all_data():
    countries = ["ethiopia", "kenya", "sudan", "tanzania", "nigeria"]
    all_dfs = []

    for country in countries:
        df = pd.read_csv(f"data/{country}.csv")  # ✅ fixed path
        df.replace(-999, np.nan, inplace=True)

        df["Date"] = pd.to_datetime(
            df["YEAR"].astype(str) + df["DOY"].astype(str).str.zfill(3),
            format="%Y%j"
        )

        df["Country"] = country.capitalize()  # ✅ renamed column
        df["Year"] = df["Date"].dt.year

        all_dfs.append(df)

    return pd.concat(all_dfs, ignore_index=True)


data = load_all_data()

# ------------------------------------------------------------------------------
# 2. Sidebar filters
# ------------------------------------------------------------------------------
st.sidebar.header("Filter the data")

all_countries = sorted(data["Country"].unique())

selected_countries = st.sidebar.multiselect(
    "Select countries",
    options=all_countries,
    default=all_countries
)

min_year = int(data["Year"].min())
max_year = int(data["Year"].max())

year_range = st.sidebar.slider(
    "Select year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

variable = st.sidebar.selectbox(
    "Choose a variable",
    options=["T2M", "PRECTOTCORR", "RH2M", "WS2M"],
    index=0
)

st.sidebar.info("Data source: NASA POWER. Missing values appear as gaps.")

# ------------------------------------------------------------------------------
# 3. Filter data
# ------------------------------------------------------------------------------
filtered = data[
    (data["Country"].isin(selected_countries)) &
    (data["Year"] >= year_range[0]) &
    (data["Year"] <= year_range[1])
].copy()

# ------------------------------------------------------------------------------
# 4. Temperature trend
# ------------------------------------------------------------------------------
st.header("Temperature Trend Over Time")

filtered["YearMonth"] = filtered["Date"].dt.to_period("M").astype(str)

monthly = filtered.groupby(["Country", "YearMonth"])["T2M"].mean().reset_index()
monthly["Date"] = pd.to_datetime(monthly["YearMonth"])

fig_trend = px.line(
    monthly,
    x="Date",
    y="T2M",
    color="Country",
    title="Mean Monthly Temperature (°C)",
    labels={"T2M": "Temperature (°C)", "Date": ""},
    template="plotly_white"
)

st.plotly_chart(fig_trend, use_container_width=True)

# ------------------------------------------------------------------------------
# 5. Precipitation boxplot
# ------------------------------------------------------------------------------
st.header("Precipitation Distribution by Country")

fig_box = px.box(
    filtered,
    x="Country",
    y="PRECTOTCORR",
    color="Country",
    title="Daily Precipitation (mm/day)",
    labels={"PRECTOTCORR": "Precipitation (mm/day)", "Country": ""},
    template="plotly_white"
)

st.plotly_chart(fig_box, use_container_width=True)

# ------------------------------------------------------------------------------
# 6. Selected variable trend
# ------------------------------------------------------------------------------
st.header(f"Trend for Selected Variable: {variable}")

if variable in filtered.columns:
    fig_var = px.line(
        filtered.sort_values("Date"),
        x="Date",
        y=variable,
        color="Country",
        title=f"{variable} Over Time",
        labels={variable: variable, "Date": ""},
        template="plotly_white"
    )
    st.plotly_chart(fig_var, use_container_width=True)
else:
    st.warning(f"Column '{variable}' not found in the dataset.")

# ------------------------------------------------------------------------------
# 7. Extreme heat days
# ------------------------------------------------------------------------------
st.header("Extreme Heat Days (T2M_MAX > 35°C)")

if "T2M_MAX" in filtered.columns:
    heat_days = filtered[filtered["T2M_MAX"] > 35] \
        .groupby("Country") \
        .size() \
        .reset_index(name="Days")

    if not heat_days.empty:
        fig_heat = px.bar(
            heat_days,
            x="Country",
            y="Days",
            color="Country",
            title="Days Above 35°C",
            template="plotly_white"
        )
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("No extreme heat days in selected range.")
else:
    st.warning("Column 'T2M_MAX' not found.")

# ------------------------------------------------------------------------------
# 8. Footer
# ------------------------------------------------------------------------------
st.markdown("---")
st.caption(
    f"Countries: {len(selected_countries)} | "
    f"Years: {year_range[0]}–{year_range[1]} | "
    f"Records: {len(filtered):,}"
)
