import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(layout="wide")

st.title("DCA Investment Simulator")

available_stocks = [
    "MSFT",
    "NVDA",
    "GOOGL",
    "AMZN",
    "META",
    "TSLA",
    "COST",
    "V"
]

monthly_amount = st.number_input(
    "Monthly Investment",
    min_value=100,
    value=1000
)

start_date = st.date_input(
    "Start Date",
    value=pd.Timestamp("2018-01-01")
)

end_date = st.date_input(
    "End Date",
    value=pd.Timestamp.today()
)

selected_stocks = st.multiselect(
    "Choose up to 4 stocks",
    available_stocks,
    default=["MSFT", "AMZN"],
    max_selections=4
)


def run_dca(ticker, amount, start_date, end_date):

    data = yf.download(
        ticker,
        start=start_date,
        end=end_date,
        auto_adjust=True,
        progress=False
    )

    close = data["Close"]

    if hasattr(close, "columns"):
        close = close.iloc[:, 0]

    monthly_prices = close.resample("MS").first()

    shares = 0
    invested = 0

    growth = []

    for date, price in monthly_prices.items():

        shares += amount / float(price)
        invested += amount

        growth.append({
            "Date": date,
            "Value": shares * float(price)
        })

    final_value = shares * float(close.iloc[-1])

    # make last graph point match final value
    growth[-1]["Value"] = final_value

    gain = final_value - invested
    return_pct = (gain / invested) * 100

    return {
        "invested": invested,
        "value": final_value,
        "gain": gain,
        "return_pct": return_pct,
        "growth": pd.DataFrame(growth)
    }


if st.button("Calculate"):

    qqq = run_dca(
        "QQQ",
        monthly_amount,
        start_date,
        end_date
    )

    spy = run_dca(
        "SPY",
        monthly_amount,
        start_date,
        end_date
    )

    allocation = monthly_amount / len(selected_stocks)

    custom_value = 0
    custom_invested = 0
    custom_gain = 0

    custom_growth = None

    for stock in selected_stocks:

        result = run_dca(
            stock,
            allocation,
            start_date,
            end_date
        )

        custom_value += result["value"]
        custom_invested += result["invested"]
        custom_gain += result["gain"]

        if custom_growth is None:
            custom_growth = result["growth"].copy()
        else:
            custom_growth["Value"] += result["growth"]["Value"]

    custom_return = (
        custom_gain / custom_invested
    ) * 100

    summary = pd.DataFrame([
        {
            "Portfolio": "QQQ",
            "Invested": round(qqq["invested"]),
            "Value": round(qqq["value"]),
            "Gain": round(qqq["gain"]),
            "Return %": round(
                qqq["return_pct"],
                1
            )
        },
        {
            "Portfolio": "SPY",
            "Invested": round(spy["invested"]),
            "Value": round(spy["value"]),
            "Gain": round(spy["gain"]),
            "Return %": round(
                spy["return_pct"],
                1
            )
        },
        {
            "Portfolio": "Custom",
            "Invested": round(custom_invested),
            "Value": round(custom_value),
            "Gain": round(custom_gain),
            "Return %": round(
                custom_return,
                1
            )
        }
    ])

    st.subheader("Performance Summary")
    st.dataframe(
        summary,
        use_container_width=True
    )

    custom_row = summary[
        summary["Portfolio"] == "Custom"
    ].iloc[0]

    qqq_row = summary[
        summary["Portfolio"] == "QQQ"
    ].iloc[0]

    spy_row = summary[
        summary["Portfolio"] == "SPY"
    ].iloc[0]

    beat_qqq = (
        custom_row["Value"]
        - qqq_row["Value"]
    )

    beat_spy = (
        custom_row["Value"]
        - spy_row["Value"]
    )

    if beat_qqq > 0:
        st.success(
            f"✅ Beat QQQ by ${beat_qqq:,.0f}"
        )
    else:
        st.error(
            f"❌ Underperformed QQQ by ${abs(beat_qqq):,.0f}"
        )

    if beat_spy > 0:
        st.success(
            f"✅ Beat SPY by ${beat_spy:,.0f}"
        )
    else:
        st.error(
            f"❌ Underperformed SPY by ${abs(beat_spy):,.0f}"
        )

    qqq_chart = qqq["growth"].copy()
    qqq_chart["Portfolio"] = "QQQ"

    spy_chart = spy["growth"].copy()
    spy_chart["Portfolio"] = "SPY"

    custom_chart = custom_growth.copy()
    custom_chart["Portfolio"] = "Custom"

    chart = pd.concat([
        qqq_chart,
        spy_chart,
        custom_chart
    ])

    fig = px.line(
        chart,
        x="Date",
        y="Value",
        color="Portfolio",
        title="Portfolio Growth Comparison",
        template="plotly_dark",
        line_shape="spline"
    )

    fig.update_traces(
        line=dict(width=4)
    )

    fig.update_layout(
        height=600,
        font=dict(size=16),
        legend_title=""
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )