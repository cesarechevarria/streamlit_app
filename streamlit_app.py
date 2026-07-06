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
    page_title="VIIRS-like Radiance",
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
        raise ValueError(
            f"Dataset is missing required columns: {missing}"
        )

    df = df.copy()

    df["region_label"] = (
        df["NAME_ADMIN"]
        .fillna("Unknown")
        .astype(str)
    )

    numeric_columns = [
        "year",
        "month",
        "sum",
        "mean",
        "max",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(
        subset=[
            "year",
            "month",
            "mean",
        ]
    )

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

    return (
        df.sort_values(
            [
                "region_label",
                "date",
            ]
        )
        .reset_index(drop=True)
    )


def format_month(value: pd.Timestamp) -> str:
    """Format a date as a full month and year."""
    return value.strftime("%B %Y")


def build_monthly_chart(
    region_data: pd.DataFrame,
) -> go.Figure:
    """Create the monthly mean-radiance time-series chart."""
    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=region_data["date"],
            y=region_data["mean"],
            mode="lines",
            name="Monthly mean",
            line={
                "width": 2,
            },
            hovertemplate=(
                "<b>%{x|%B %Y}</b><br>"
                "Mean radiance: %{y:.3f}"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        title_text="",
        xaxis_title="Year",
        yaxis_title="Mean radiance",
        height=480,
        margin={
            "l": 20,
            "r": 20,
            "t": 20,
            "b": 20,
        },
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


def calculate_annual_mean(
    region_data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate the annual average of the available monthly
    mean-radiance observations.
    """
    annual_data = (
        region_data.groupby(
            "year",
            as_index=False,
        )
        .agg(
            annual_mean=("mean", "mean"),
            months_available=("month", "nunique"),
        )
        .sort_values("year")
        .reset_index(drop=True)
    )

    annual_data["date"] = pd.to_datetime(
        {
            "year": annual_data["year"],
            "month": 1,
            "day": 1,
        }
    )

    return annual_data


def build_annual_chart(
    annual_data: pd.DataFrame,
) -> go.Figure:
    """Create the annual mean-radiance time-series chart."""
    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=annual_data["date"],
            y=annual_data["annual_mean"],
            mode="lines",
            name="Annual mean",
            line={
                "width": 2,
            },
            customdata=annual_data[
                ["months_available"]
            ].to_numpy(),
            hovertemplate=(
                "Mean radiance: %{y:.3f}<br>"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        title_text="",
        xaxis_title="Year",
        yaxis_title="Mean radiance",
        height=480,
        margin={
            "l": 20,
            "r": 20,
            "t": 20,
            "b": 20,
        },
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


st.title("VIIRS-like radiance")

st.caption(
    "China ADM2 (Kummu et al., 2025), 1992–2022"
)


try:
    data = load_data(DATA_URL)

except Exception as exc:
    st.error(
        "The dataset could not be loaded or prepared."
    )
    st.exception(exc)
    st.stop()


regions = sorted(
    data["region_label"]
    .unique()
    .tolist()
)


if not regions:
    st.warning(
        "No regions were found in the dataset."
    )
    st.stop()


selected_region = st.selectbox(
    "Select region",
    options=regions,
    index=0,
)


region_data = (
    data.loc[
        data["region_label"] == selected_region
    ]
    .sort_values("date")
    .reset_index(drop=True)
)


if region_data.empty:
    st.warning(
        "No valid observations are available for this region."
    )
    st.stop()


minimum_row = region_data.loc[
    region_data["mean"].idxmin()
]

maximum_row = region_data.loc[
    region_data["mean"].idxmax()
]


minimum_column, maximum_column = st.columns(2)


with minimum_column:
    st.metric(
        label="Minimum monthly radiance",
        value=f"{minimum_row['mean']:.3f}",
        border=True,
    )

    st.caption(
        format_month(minimum_row["date"])
    )


with maximum_column:
    st.metric(
        label="Maximum monthly radiance",
        value=f"{maximum_row['mean']:.3f}",
        border=True,
    )

    st.caption(
        format_month(maximum_row["date"])
    )


st.subheader("Monthly mean radiance")

monthly_chart = build_monthly_chart(region_data)

st.plotly_chart(
    monthly_chart,
    width="stretch",
    config={
        "displaylogo": False,
        "responsive": True,
    },
)


annual_data = calculate_annual_mean(region_data)


st.subheader("Annual mean radiance")

annual_chart = build_annual_chart(annual_data)

st.plotly_chart(
    annual_chart,
    width="stretch",
    config={
        "displaylogo": False,
        "responsive": True,
    },
)
