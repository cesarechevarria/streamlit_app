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

FONT_FAMILY = (
    "Inter, system-ui, -apple-system, BlinkMacSystemFont, "
    "'Segoe UI', sans-serif"
)

COLORS = {
    "page": "#EAF2FF",
    "surface": "#F7FAFF",
    "text": "#172033",
    "muted": "#667085",
    "accent": "#3B5CCC",
    "border": "#D7E3F4",
    "grid": "#E9EDF4",
}


st.set_page_config(
    page_title="VIIRS-like Radiance",
    page_icon="🌃",
    layout="wide",
)


st.html(
    f"""
    <style>
        :root {{
            color-scheme: light;
        }}

        html,
        body,
        [data-testid="stAppViewContainer"] {{
            font-family: {FONT_FAMILY};
            color: {COLORS["text"]};
        }}

        [data-testid="stAppViewContainer"] {{
            background: {COLORS["page"]};
        }}

        [data-testid="stHeader"] {{
            background: rgba(234, 242, 255, 0.92);
        }}

        [data-testid="stMainBlockContainer"] {{
            max-width: 1380px;
            padding-top: 2.5rem;
            padding-bottom: 4rem;
        }}

        h1,
        h2,
        h3,
        p,
        label,
        input,
        button,
        textarea {{
            font-family: {FONT_FAMILY};
        }}

        h1 {{
            color: {COLORS["text"]};
            font-size: clamp(2.15rem, 3vw, 2.8rem);
            font-weight: 750;
            letter-spacing: -0.04em;
            line-height: 1.08;
            margin-bottom: 0.35rem;
        }}

        h2,
        h3 {{
            color: {COLORS["text"]};
            font-size: clamp(1.25rem, 1.8vw, 1.55rem);
            font-weight: 700;
            letter-spacing: -0.025em;
            line-height: 1.25;
            margin-top: 1.6rem;
        }}

        [data-testid="stCaptionContainer"] p {{
            color: {COLORS["muted"]};
            font-size: 0.9rem;
            line-height: 1.45;
        }}

        [data-testid="stSelectbox"] label p {{
            color: {COLORS["text"]};
            font-size: 0.95rem;
            font-weight: 650;
        }}

        [data-testid="stSelectbox"]
        [data-baseweb="select"] > div {{
            min-height: 3rem;
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 12px;
            box-shadow: 0 1px 2px rgba(23, 32, 51, 0.04);
            font-size: 0.98rem;
            transition:
                border-color 140ms ease,
                box-shadow 140ms ease;
        }}

        [data-testid="stSelectbox"]
        [data-baseweb="select"] > div:hover {{
            border-color: {COLORS["accent"]};
        }}

        [data-testid="stMetric"] {{
            min-height: 138px;
            padding: 1.2rem 1.3rem;
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]} !important;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(23, 32, 51, 0.055);
        }}

        [data-testid="stMetricLabel"] p {{
            color: {COLORS["muted"]};
            font-size: 0.88rem;
            font-weight: 650;
            letter-spacing: 0.005em;
        }}

        [data-testid="stMetricValue"] {{
            color: {COLORS["text"]};
            font-size: clamp(1.75rem, 2.5vw, 2.25rem);
            font-weight: 750;
            letter-spacing: -0.035em;
            line-height: 1.15;
        }}

        [data-testid="stPlotlyChart"] {{
            overflow: hidden;
            padding: 0.35rem 0.45rem 0;
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(23, 32, 51, 0.045);
        }}

        [data-testid="stAlert"] {{
            border-radius: 12px;
        }}

        @media (max-width: 768px) {{
            [data-testid="stMainBlockContainer"] {{
                padding-top: 1.5rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }}

            [data-testid="stMetric"] {{
                min-height: 124px;
            }}
        }}
    </style>
    """
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


def apply_chart_style(
    figure: go.Figure,
) -> go.Figure:
    """Apply the shared visual style to a Plotly chart."""
    figure.update_layout(
        font={
            "family": FONT_FAMILY,
            "size": 14,
            "color": COLORS["text"],
        },
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor=COLORS["surface"],
        hoverlabel={
            "bgcolor": COLORS["surface"],
            "bordercolor": COLORS["border"],
            "font": {
                "family": FONT_FAMILY,
                "size": 13,
                "color": COLORS["text"],
            },
        },
    )

    figure.update_xaxes(
        automargin=True,
        showline=True,
        linecolor=COLORS["border"],
        linewidth=1,
        ticks="outside",
        tickcolor=COLORS["border"],
        tickfont={
            "size": 12,
            "color": COLORS["muted"],
        },
        title_font={
            "size": 14,
            "color": COLORS["text"],
        },
        title_standoff=22,
    )

    figure.update_yaxes(
        automargin=True,
        showline=True,
        showgrid=False,
        zeroline=False,
        tickfont={
            "size": 12,
            "color": COLORS["muted"],
        },
        title_font={
            "size": 14,
            "color": COLORS["text"],
        },
        title_standoff=22,
    )

    return figure


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
                "color": COLORS["accent"],
                "width": 2.6,
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
            "l": 28,
            "r": 24,
            "t": 24,
            "b": 28,
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

    return apply_chart_style(figure)


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
                "color": COLORS["accent"],
                "width": 2.6,
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
            "l": 28,
            "r": 24,
            "t": 24,
            "b": 28,
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

    return apply_chart_style(figure)


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
    theme=None,
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
    theme=None,
    config={
        "displaylogo": False,
        "responsive": True,
    },
)
