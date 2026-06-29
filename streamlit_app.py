import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_URL = (
    "https://www.dropbox.com/scl/fi/"
    "murzdd6px690kfmylcwme/"
    "HKU_VIIRS_Monthly_China_Admin_Stats_1992_2022.csv"
    "?rlkey=qor03kmj22bviafaik7xr43s3&st=xazi7d6c&dl=1"
)

REQUIRED_COLUMNS = {
    "NAME_ADMIN",
    "year",
    "month",
    "sum",
    "mean",
    "max",
}


st.set_page_config(
    page_title="Monthly VIIRS-like Radiance",
    page_icon="🌃",
    layout="wide",
)


@st.cache_data(ttl="6h", show_spinner="Loading VIIRS data...")
def load_data(url: str) -> pd.DataFrame:
    """Download, validate, and prepare the monthly VIIRS dataset."""
    df = pd.read_csv(url)

    missing_columns = REQUIRED_COLUMNS.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Dataset is missing required columns: {missing}")

    df = df.copy()
    df["region_label"] = df["NAME_ADMIN"].fillna("Unknown").astype(str)

    for column in ["year", "month", "sum", "mean", "max"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["year", "month", "mean"])
    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)

    valid_months = df["month"].between(1, 12)
    df = df.loc[valid_months].copy()

    df["date"] = pd.to_datetime(
        {
            "year": df["year"],
            "month": df["month"],
            "day": 1,
        },
        errors="coerce",
    )
    df = df.dropna(subset=["date"])

    return df.sort_values(["region_label", "date"]).reset_index(drop=True)


def format_month(value: pd.Timestamp) -> str:
    return value.strftime("%B %Y")


def build_chart(region_data: pd.DataFrame, region: str) -> go.Figure:
    """Create the interactive monthly mean-radiance chart."""
    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=region_data["date"],
            y=region_data["mean"],
            mode="lines",
            name="Monthly mean",
            line={"width": 2},
            hovertemplate=(
                "<b>%{x|%B %Y}</b><br>"
                "%{y:.3f}"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        title=None,
        title_text="",
        xaxis_title="Year",
        yaxis_title="Mean radiance",
        height=480,
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        hovermode="x unified",
        showlegend=False,
    )

    figure.update_xaxes(
        showgrid=False,
        tickformat="%Y",
        dtick="M12",
        tickangle=-45,
    )
    figure.update_yaxes(
        showgrid=False,
        tickformat=".3f",
    )

    return figure


st.title("Monthly VIIRS-like")
st.caption("China ADM2 (Kummu et al., 2025), 1992–2022")

try:
    data = load_data(DATA_URL)
except Exception as exc:
    st.error("The dataset could not be loaded or prepared.")
    st.exception(exc)
    st.stop()

regions = sorted(data["region_label"].unique().tolist())

if not regions:
    st.warning("No regions were found in the dataset.")
    st.stop()

selected_region = st.selectbox(
    "Select region",
    options=regions,
    index=0,
)

region_data = (
    data.loc[data["region_label"] == selected_region]
    .sort_values("date")
    .reset_index(drop=True)
)

if region_data.empty:
    st.warning("No valid observations are available for this region.")
    st.stop()

minimum_row = region_data.loc[region_data["mean"].idxmin()]
maximum_row = region_data.loc[region_data["mean"].idxmax()]

minimum_column, maximum_column = st.columns(2)

with minimum_column:
    st.metric(
        label="Minimum radiance",
        value=f"{minimum_row['mean']:.3f}",
        border=True,
    )
    st.caption(format_month(minimum_row["date"]))

with maximum_column:
    st.metric(
        label="Maximum radiance",
        value=f"{maximum_row['mean']:.3f}",
        border=True,
    )
    st.caption(format_month(maximum_row["date"]))

st.subheader("Monthly mean radiance")
chart = build_chart(region_data, selected_region)
st.plotly_chart(
    chart,
    width="stretch",
    config={
        "displaylogo": False,
        "responsive": True,
    },
)
