import streamlit as st
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# Strategy Descriptions
STRATEGIES = {
    "Long Call": {
        "description": "A Long Call is an options strategy where you buy a call option because you believe the price of the stock will go up, "
                       " By buying the call, you get the right to buy the stock at a specific price (called the strike price) by a certain date (the expiration date).",
        "max_profit": "The stock price can rise infinitely, and your profit will grow as the stock price rises above the strike price, minus the premium paid.",
        "max_loss": "The premium paid for the call option, This happens if the stock price ends up below the strike price at expiration (the option expires worthless).",
        "ideal_scenario": "You expect the stock price to rise and want to risk only the option premium instead of buying the stock.",
    },
    "Long Put": {
        "description": "A long put strategy involves buying a put option, which gives you the right (but not the obligation) to sell a stock at a specific price (the strike price) before the option expires.",
        "max_profit": "The maximum profit occurs if the stock price drops to zero.",
        "max_loss": "The premium paid for the put option.",
        "ideal_scenario": "Use a long put when you expect the stock price to drop significantly. It allows you to profit from falling prices while limiting your loss to the premium paid, or to hedge against potential losses in stocks you already own.",
    },
    "Covered Call": {
        "description": "A covered call is a strategy where you already own shares of a stock and then sell a call option on those shares. This lets you earn extra income from the option premium, but in exchange, you agree to sell your stock at a set price (the strike price) if the buyer exercises the option.",
        "max_profit": "Premium + Stock Appreciation (up to strike price)",
        "max_loss": "Stock Price - Premium Received",
        "ideal_scenario": "You believe the stock price will not rise too much beyond the strike price, but you still want to earn income from selling the call.",
    },
    "Protective Put": {
        "description": "A protective put is a strategy where you own shares of a stock and buy a put option for the same stock. This acts like insurance: if the stock price falls, the put option protects you by allowing you to sell the stock at a predetermined price (strike price), limiting your potential loss. At the same time, if the stock price rises, you still benefit from the upside, minus the cost of the put option (the premium).",
        "max_profit": "Unlimited, as the stock price can increase indefinitely, minus the cost of the put option (premium paid).",
        "max_loss": "Limited to the difference between the stock's purchase price and the put option's strike price, plus the premium paid for the option.",
        "ideal_scenario": "A protective put is best used when you own a stock and want to protect against potential short-term losses while still benefiting from any upside. It’s ideal in volatile markets or during uncertain events, like earnings announcements, where stock prices might swing sharply. This strategy acts as insurance, capping your maximum loss while allowing for potential gains.",
    },
    "Iron Condor": {
        "description": "An Iron Condor is an advanced options strategy that involves selling an out-of-the-money call and put (creating a short strangle) while simultaneously buying a further out-of-the-money call and put (creating wings for protection). This forms a combination of two vertical spreads, limiting risk on both ends.",
        "max_profit": "The max profit is the net premium received if the stock price stays within the two short strikes at expiration.",
        "max_loss": "The max loss is the difference between strike prices in the spread minus the net premium, occurring if the stock moves beyond the long strikes.",
        "ideal_scenario": "The Iron Condor is ideal in neutral or low-volatility markets, where you expect the stock price to stay within a specific range. It’s used when you anticipate stability and want to profit from time decay and minimal price movement.",
    },
    "Bull Put Spread": {
        "description": "A **Bull Put Spread** is an options strategy where you sell a put option at a higher strike price and buy another put option at a lower strike price. This approach generates income from the net premium received while limiting potential losses. It's ideal for a moderately bullish outlook, as it profits if the stock price stays above the higher strike price.",
        "max_profit": "The net premium received when entering the trade.",
        "max_loss": "The difference between the strike prices minus the net premium received.",
        "ideal_scenario": "A **Bull Put Spread** is ideal in a moderately bullish market when you expect the stock price to rise or remain steady. It offers limited risk and reward, making it suitable for traders seeking defined profit and loss boundaries. This strategy generates income through the net premium received while effectively managing downside risk.",
    },
    "Bear Call Spread": {
        "description": "A Bear Call Spread is an options strategy where you sell a call option at a lower strike price and buy a call option at a higher strike price. It is ideal for a bearish to neutral market outlook, where you expect the stock price to stay below the lower strike price by expiration, allowing you to profit from the net premium received.",
        "max_profit": "The maximum profit is the net premium received if the stock price stays below the lower strike price.",
        "max_loss": "The maximum loss is the difference between the two strike prices minus the premium received, which happens if the stock price goes above the higher strike price.",
        "ideal_scenario": "Use a Bear Call Spread when you expect the stock price to stay stable or drop slightly. It’s ideal for traders seeking limited risk and clearly defined profit and loss boundaries.",
    },
    "Long Straddle": {
        "description": "A Long Straddle is an options strategy where you purchase both a call option and a put option with the same strike price and expiration date. This approach allows you to profit from significant price movement in either direction, making it ideal for uncertain or highly volatile markets.",
        "max_profit": "The profit grows as the stock price moves significantly either above or below the strike price.",
        "max_loss": "Limited to the total premium paid if the stock price remains exactly at the strike price at expiration, as both options would expire worthless.",
        "ideal_scenario": " Ideal for uncertain or volatile markets where you expect significant price movement but are unsure of the direction. It allows you to profit from large price swings in either direction.",
    },
    "Short Straddle": {
        "description": "A Short Straddle is an options strategy where you sell a call option and a put option at the same strike price and expiration date. This strategy profits from minimal price movement in the stock, as it works best when the stock price remains near the strike price at expiration.",
        "max_profit": "The maximum profit is the net premium received from selling both options, achieved if the stock price equals the strike price at expiration.",
        "max_loss": "The potential loss is unlimited if the stock price moves significantly above the strike price and substantial if it drops far below the strike price.",
        "ideal_scenario": "It is ideal for stable markets with low volatility, where you expect the stock price to stay close to the strike price until expiration.",
    },
    "Long Strangle": {
        "description": "A Long Strangle is an options strategy where you buy an out-of-the-money call and an out-of-the-money put, both with the same expiration date, to profit from big price moves in either direction.",
        "max_profit": "If the stock price moves significantly above the call strike price or below the put strike price, profits increase as there’s no cap on gains.",
        "max_loss": "If the stock price stays between the strike prices at expiration, both options expire worthless, and the loss is limited to the net premium paid for the options.",
        "ideal_scenario": "Ideal when you expect the stock price to move significantly in either direction, especially during high volatility events like earnings reports or major news.",
    },
    "Short Strangle": {
        "description": "A **Short Strangle** is an options strategy where you sell both an out-of-the-money call and put option with the same expiration date, aiming to profit from minimal stock price movement within the range of the strike prices.",
        "max_profit": "Limited to the Net Premium Received if the stock price stays between the strike prices at expiration, making both options expire worthless.",
        "max_loss": "Unlimited on the Upside and Significant on the Downside: If the stock price moves significantly above the call strike price or below the put strike price, losses can be substantial.",
        "ideal_scenario": "Ideal when the stock price is expected to stay stable in low-volatility markets, allowing the options to expire worthless and earn a profit.",
    },
    "Butterfly Spread": {
        "description": "A Butterfly Spread is an options strategy designed to profit from minimal stock price movement. It involves buying one in-the-money call, selling two at-the-money calls, and buying one out-of-the-money call, all with the same expiration date. This setup balances risk and reward, making it ideal for stable markets.",
        "max_profit": "The maximum profit of a butterfly spread occurs when the stock price is at the middle strike price (the at-the-money strike) at expiration. This happens because the two sold options expire worthless while the bought options provide the maximum value.",
        "max_loss": "The maximum loss of a butterfly spread is the **net premium paid** to enter the trade. This occurs if the stock price ends up outside the range of the outer strikes (either below the lowest strike or above the highest strike) at expiration.",
        "ideal_scenario": "The butterfly spread is ideal when you expect the stock price to **stay near the middle strike price** (at-the-money) by expiration. This strategy works best in **low-volatility markets** or when the stock is expected to remain relatively stable within a narrow price range.",
    },
    "Iron Butterfly": {
        "description": "An Iron Butterfly is an options strategy for low-volatility markets. It involves selling an at-the-money (ATM) call and put and buying out-of-the-money (OTM) call and put options for protection, creating a defined range of profit and loss.",
        "max_profit": "The maximum profit occurs if the stock price matches the strike price of the short options at expiration. It equals the net premium received, which is the premium from the short options minus the cost of the protective options.",
        "max_loss": "The maximum loss happens if the stock price moves far beyond the range of the protective options. It is calculated as the difference between the strike prices of the long and short options, minus the net premium received.",
        "ideal_scenario": "Ideal in low-volatility markets where the stock price is expected to remain stable around the strike price of the short options. This strategy works best if the stock price does not move much before expiration.",
    },
    "Collar": {
        "description": "A Collar is an options strategy to protect against large losses while limiting gains. It involves owning the stock, buying a put option for downside protection, and selling a call option to reduce the cost of the put.",
        "max_profit": "The maximum profit occurs if the stock price rises to the call option's strike price. ",
        "max_loss": "The maximum loss happens if the stock price falls to or below the put option's strike price.",
        "ideal_scenario": "This strategy is ideal for managing risk by protecting against large stock price drops while allowing for some moderate gains. It works best when you expect the stock price to stay relatively stable.",
    },

}

def fetch_option_data(ticker):
    stock = yf.Ticker(ticker)
    expiration_dates = stock.options
    current_price = round(stock.history(period="1d")['Close'].iloc[-1], 2)  # Round to 2 decimal places
    return stock, expiration_dates, current_price

def calculate_payoff(strategy, stock_prices, strike_prices, premiums, positions, avg_stock_price=None):
    payoff = np.zeros_like(stock_prices)
    if strategy in ["Iron Condor", "Iron Butterfly"] and len(strike_prices) < 4:
        raise ValueError(f"{strategy} requires 4 strike prices and 4 premiums.")
    elif strategy in ["Bull Put Spread", "Bear Call Spread", "Collar"] and len(strike_prices) < 2:
        raise ValueError(f"{strategy} requires 2 strike prices and 2 premiums.")
    elif strategy in ["Long Straddle", "Short Straddle", "Long Strangle", "Short Strangle"] and len(strike_prices) < 2:
        raise ValueError(f"{strategy} requires 2 strike prices and 2 premiums.")
    for i, strike_price in enumerate(strike_prices):
        if positions[i] == "Call":
            payoff += np.maximum(stock_prices - strike_price, 0) - premiums[i]
        elif positions[i] == "Put":
            payoff += np.maximum(strike_price - stock_prices, 0) - premiums[i]
    # Adjust for strategies requiring avg_stock_price
    if strategy == "Covered Call" and avg_stock_price is not None:
        # Stock payoff
        stock_payoff = stock_prices - avg_stock_price
        # Short call payoff
        short_call_payoff = np.minimum(0, strike_prices[0] - stock_prices)
        # Total payoff
        payoff = stock_payoff + short_call_payoff + premiums[0]
    elif strategy == "Protective Put" and avg_stock_price is not None:
        # Stock payoff
        stock_payoff = stock_prices - avg_stock_price
        # Put option payoff
        put_payoff = np.maximum(strike_prices[0] - stock_prices, 0)
        # Total payoff
        payoff = stock_payoff + put_payoff - premiums[0]
    elif strategy == "Iron Condor":
        # Short call payoff (negative payoff for the seller if price > short call strike)
        short_call_payoff = -np.maximum(0, stock_prices - strike_prices[0]) + premiums[0]
        # Long call payoff (positive payoff for the buyer if price > long call strike)
        long_call_payoff = np.maximum(0, stock_prices - strike_prices[1]) - premiums[1]
        # Short put payoff (negative payoff for the seller if price < short put strike)
        short_put_payoff = -np.maximum(0, strike_prices[2] - stock_prices) + premiums[2]
        # Long put payoff (positive payoff for the buyer if price < long put strike)
        long_put_payoff = np.maximum(0, strike_prices[3] - stock_prices) - premiums[3]
        # Total payoff
        payoff = short_call_payoff + long_call_payoff + short_put_payoff + long_put_payoff
    elif strategy == "Bull Put Spread":
        # Short put payoff
        short_put_payoff = np.maximum(0, strike_prices[0] - stock_prices) - premiums[0]
        # Long put payoff
        long_put_payoff = np.maximum(0, strike_prices[1] - stock_prices) - premiums[1]
        # Total payoff
        payoff = long_put_payoff - short_put_payoff
    elif strategy == "Bear Call Spread":
        short_call_payoff = np.minimum(0, strike_prices[0] - stock_prices) + premiums[0]
        long_call_payoff = np.maximum(0, stock_prices - strike_prices[1]) - premiums[1]
        payoff = long_call_payoff  + short_call_payoff
    elif strategy == "Long Straddle":
        # Long call and long put with the same strike price
        long_call_payoff = np.maximum(stock_prices - strike_prices[0], 0) - premiums[0]
        long_put_payoff = np.maximum(strike_prices[0] - stock_prices, 0) - premiums[1]
        # Total payoff
        payoff = long_call_payoff + long_put_payoff
    elif strategy == "Short Straddle":
        # Short call and short put with the same strike price
        short_call_payoff = np.minimum(0, stock_prices - strike_prices[0]) + premiums[0]
        short_put_payoff = np.minimum(0, strike_prices[0] - stock_prices) + premiums[1]
        # Total payoff
        payoff = short_call_payoff + short_put_payoff
    elif strategy == "Long Strangle":
        # Long OTM call and long OTM put with different strike prices
        long_call_payoff = np.maximum(stock_prices - strike_prices[0], 0) - premiums[0]
        long_put_payoff = np.maximum(strike_prices[1] - stock_prices, 0) - premiums[1]
        # Total payoff
        payoff = long_call_payoff + long_put_payoff
    elif strategy == "Short Strangle":
        # Short OTM call and short OTM put with different strike prices
        # Short Call Payoff
        short_call_payoff = -(np.maximum(0, stock_prices - strike_prices[0])) + premiums[0]
        # Short Put Payoff
        short_put_payoff = -(np.maximum(0, strike_prices[1] - stock_prices)) + premiums[1]
        # Total payoff
        payoff = short_call_payoff + short_put_payoff
    elif strategy == "Iron Butterfly":
        # Long Put Payoff
        long_put_payoff = np.maximum(0, strike_prices[0] - stock_prices) - premiums[0]
        # Short Put Payoff (negative impact if exercised)
        short_put_payoff = -(np.maximum(0, strike_prices[1] - stock_prices)) + premiums[1]
        # Short Call Payoff (negative impact if exercised)
        short_call_payoff = -(np.maximum(0, stock_prices - strike_prices[2])) + premiums[2]
        # Long Call Payoff
        long_call_payoff = np.maximum(0, stock_prices - strike_prices[3]) - premiums[3]
        payoff = short_call_payoff + short_put_payoff + long_call_payoff + long_put_payoff
    elif strategy == "Butterfly Spread":
        itm_call_payoff = np.maximum(stock_prices - strike_prices[0], 0) - premiums[0]
        atm_call_payoff = 2 * (np.minimum(0, strike_prices[1] - stock_prices) + premiums[1])
        otm_call_payoff = np.maximum(stock_prices - strike_prices[2], 0) - premiums[2]
        payoff = itm_call_payoff + atm_call_payoff + otm_call_payoff
    elif strategy == "Collar" and avg_stock_price is not None:
        stock_payoff = stock_prices - avg_stock_price
        put_payoff = np.maximum(0,strike_prices[0]- stock_prices) - premiums[0]
        call_payoff = -np.maximum(0, stock_prices - strike_prices[1] ) + premiums[1]
        payoff = stock_payoff + put_payoff + call_payoff
    return payoff

# Calculate break-even points
def calculate_break_even(strategy, strike_prices, premiums, avg_stock_price=None):
    if strategy == "Long Call":
        # Strike Price + Premium
        return [strike_prices[0] + premiums[0]]
    elif strategy == "Long Put":
        # Strike Price - Premium
        return [strike_prices[0] - premiums[0]]
    elif strategy == "Covered Call":
        if avg_stock_price is not None:
            # Avg Stock Price + Premium Received
            return [avg_stock_price + premiums[0]]
        return ["Avg Stock Price Required"]
    elif strategy == "Protective Put":
        if avg_stock_price is not None:
            # Avg Stock Price - Premium Paid
            return [avg_stock_price - premiums[0]]
        return ["Avg Stock Price Required"]
    elif strategy == "Iron Condor":
        # Calculate Net Credit Received
        net_credit = (premiums[0] + premiums[2]) - (premiums[1] + premiums[3])
        # Break-even points
        lower_bep = strike_prices[2] - net_credit  # Short Put Strike - Net Credit
        upper_bep = strike_prices[0] + net_credit  # Short Call Strike + Net Credit
        return [lower_bep, upper_bep]
    elif strategy == "Bull Put Spread":
        # Net Credit Received
        net_credit = premiums[0] - premiums[1]
        # Break-even point (only one)
        break_even_point = strike_prices[0] - net_credit
        # Return the single break-even point
        return [break_even_point]
    elif strategy == "Bear Call Spread":
        if strategy == "Bear Call Spread":
            if len(premiums) < 2:
                raise ValueError("Bear Call Spread requires exactly two premiums (short call and long call).")
            # Calculate Net Premium Received
            net_premium = premiums[0] - premiums[1]
            # Break-even point
            break_even_point = strike_prices[0] + net_premium
            return [break_even_point]
    elif strategy == "Long Straddle":
        # Two break-even points: lower and upper
        total_premium = premiums[0] + premiums[1]
        lower_bep = strike_prices[0] - total_premium
        upper_bep = strike_prices[0] + total_premium
        return [lower_bep, upper_bep]
    elif strategy == "Short Straddle":
        # Two break-even points: lower and upper
        total_premium = premiums[0] + premiums[1]
        lower_bep = strike_prices[0] - total_premium
        upper_bep = strike_prices[0] + total_premium
        return [lower_bep, upper_bep]
    elif strategy == "Long Strangle":
        # Two break-even points: lower and upper
        total_premium = premiums[0] + premiums[1]
        lower_bep = strike_prices[1] - total_premium
        upper_bep = strike_prices[0] + total_premium
        return [lower_bep, upper_bep]
    elif strategy == "Short Strangle":
        # Two break-even points: lower and upper
        total_premium = premiums[0] + premiums[1]
        lower_bep = strike_prices[1] - total_premium
        upper_bep = strike_prices[0] + total_premium
        return [lower_bep, upper_bep]
    elif strategy == "Butterfly Spread":
        # Two break-even points: lower and upper
        net_premium = premiums[0] - (2 * premiums[1]) + premiums[2]
        lower_bep = strike_prices[0] + net_premium
        upper_bep = strike_prices[2] - net_premium
        return [lower_bep, upper_bep]
    elif strategy == "Iron Butterfly":
        # Two break-even points: lower and upper
        total_premium = premiums[0] - premiums[1] - premiums[2] + premiums[3]
        lower_bep = strike_prices[1] - total_premium
        upper_bep = strike_prices[1] + total_premium
        return [lower_bep, upper_bep]
    elif strategy == "Collar":
        if avg_stock_price is not None:
            # Two break-even points: lower and upper
            lower_bep = avg_stock_price - premiums[0]
            upper_bep = avg_stock_price + premiums[1]
            return [lower_bep, upper_bep]
        return ["Avg Stock Price Required"]
    else:
        return ["N/A"]

def create_interactive_payoff_chart(stock_prices, payoff, strategy_name, break_even_points=None):
    with st.container():
        st.write("Adjust Price Range:")
        col1, col2 = st.columns([1,1])
        with col1:
            x_min = st.number_input("Min:", value=float(min(stock_prices)), format="%.2f")
        with col2:
            x_max = st.number_input("Max:", value=float(max(stock_prices)), format="%.2f")
    fig = go.Figure()
    # Add the payoff line
    fig.add_trace(go.Scatter(
        x=stock_prices,
        y=payoff,
        mode='lines+markers',
        name='Payoff',
        hovertemplate='Stock Price: %{x:.2f}<br>Payoff: %{y:.2f}',
        line=dict(color='blue', width=2),
        marker=dict(size=1)
    ))
    # Add vertical dashed lines for break-even points, if any
    if break_even_points:
        for i, point in enumerate(break_even_points):
            annotation_position = "top right" if i % 2 == 0 else "bottom right"
            fig.add_vline(
                x=point,
                line_width=2,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Break-Even: {point:.2f}",
                annotation_position=annotation_position,
                annotation_font_size=10
            )
    fig.update_layout(
        title=f"Payoff Diagram for {strategy_name}",
        xaxis_title="Price",
        yaxis_title="Profit / Loss",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=40, b=40),
        height=500,
        width=800
    )
    # Ensure exact range and disable autoranging
    fig.update_xaxes(
        range=[x_min, x_max],
        autorange=False
    )
    return fig


# Streamlit App
st.title("Options Trading Strategy Backtester")
# Sidebar Inputs
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL):", "AAPL")
strategy = st.sidebar.selectbox("Select Option Strategy:", list(STRATEGIES.keys()))
st.sidebar.write("Selected Strategy:", strategy)


if ticker:
    stock, expiration_dates, current_price = fetch_option_data(ticker)
    expiry = st.sidebar.selectbox("Select Expiration Date:", expiration_dates)
    option_chain = stock.option_chain(expiry)
    calls, puts = option_chain.calls, option_chain.puts

    if strategy in STRATEGIES:
        # Display strategy name and description
        st.write(f"### {strategy}")
        st.markdown(STRATEGIES[strategy]['description'])
        with st.expander("Learn More"):
            st.markdown(f"**Max Profit**: {STRATEGIES[strategy]['max_profit']}")
            st.markdown(f"**Max Loss**: {STRATEGIES[strategy]['max_loss']}")
            st.markdown(f"**Ideal Scenario**: {STRATEGIES[strategy]['ideal_scenario']}")
        # Correct calculation for payoff based on strategy
        if strategy in ["Long Call", "Long Put"]:
            # Default to ATM strike for calls/puts
            if strategy == "Long Call":
                atm_call_strike = calls.loc[(calls["strike"] - current_price).abs().idxmin(), "strike"]
                cmp_atm_call = calls.loc[calls["strike"] == atm_call_strike, "lastPrice"].iloc[0]
                # Limit the range of strikes around the ATM for a shorter dropdown
                strike_range = 10  # Number of strikes above and below the ATM to display
                atm_index = calls["strike"].tolist().index(atm_call_strike)
                start_index = max(0, atm_index - strike_range)
                end_index = min(len(calls["strike"]), atm_index + strike_range + 1)
                available_strikes = sorted(calls["strike"].iloc[start_index:end_index])
                # Display Current CMP in a styled format
                st.markdown(
                    f"""
                    <style>
                        /* Card Container */
                        .modern-card {{
                            background: linear-gradient(135deg, #2c5364, #0f2027); /* Sophisticated teal-to-dark gradient */
                            border-radius: 15px; /* Rounded corners */
                            padding: 2px 25px;
                            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); /* Soft shadow for elevation */
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            margin: 15px auto;
                            max-width: 700px;
                            transition: transform 0.3s ease, box-shadow 0.3s ease;
                        }}

                        /* Hover Effect */
                        .modern-card:hover {{
                            transform: translateY(-5px);
                            box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5);
                        }}

                        /* Title */
                        .modern-title {{
                            font-size: 20px;
                            font-weight: bold;
                            font-family: 'Arial', sans-serif;
                            color: #d3dde6; /* Subtle pale blue for elegance */
                        }}
                        /* Price */
                        .modern-price {{
                            font-size: 26px;
                            font-weight: bold;
                            color: #f4a261; /* Warm amber-orange for a luxurious touch */
                            font-family: 'Courier New', monospace;
                            text-shadow: 0 2px 5px rgba(244, 162, 97, 0.8); /* Subtle glow effect */
                        }}
                        /* Icon */
                        .modern-icon {{
                            font-size: 30px;
                            color: #d3dde6; /* Matches title color */
                            margin-right: 10px;
                        }}
                    </style>

                    <div class="modern-card">
                        <div style="display: flex; align-items: center;">
                            <span class="modern-icon">📈</span>
                            <span class="modern-title">CMP of {ticker.upper()}:</span>
                        </div>
                        <div class="modern-price">${current_price:.2f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                # Styled dropdown with restricted strike range
                strike_price = st.selectbox(
                    "Select Strike Price (ATM range highlighted):",
                    available_strikes,
                    index=available_strikes.index(atm_call_strike),
                    help="Choose a strike price close to the current market price for better alignment with strategy."
                )
                # Fetch the corresponding market price for the selected strike
                cmp_selected_call = calls.loc[calls["strike"] == strike_price, "lastPrice"].iloc[0]
                # Display the Selected Strike Price and CMP
                st.markdown(
                    f"""
                    <div style="
                        background-color: #f2f2f2; 
                        padding: 12px; 
                        border-radius: 4px; 
                        font-family: Arial, sans-serif; 
                        font-size: 14px; 
                        color: #333;"
                    >
                        <div style="
                            font-size:18px; 
                            font-weight:bold; 
                            margin-bottom:10px; 
                            border-bottom:1px solid #ccc; 
                            padding-bottom:6px;"
                        >
                            Long Call Configuration
                        </div>
                        <div style="margin-bottom:6px;">
                            <strong>Selected Strike Price:</strong> {strike_price}
                        </div>
                        <div>
                            <strong>Call Option Price:</strong> ${cmp_selected_call:.2f}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                cmp_selected_call = calls.loc[calls["strike"] == strike_price, "lastPrice"].iloc[0]
                # Calculate payoff for Long Call
                stock_prices = np.linspace(0.5 * current_price, 1.5 * current_price, 1000)
                payoff = calculate_payoff("Long Call", stock_prices, [strike_price], [cmp_selected_call], ["Call"])
                # Calculate break-even points
                break_even_points = calculate_break_even(strategy, [strike_price], [cmp_selected_call])

            elif strategy == "Long Put":
                atm_put_strike = puts.loc[(puts["strike"] - current_price).abs().idxmin(), "strike"]
                cmp_atm_put = puts.loc[puts["strike"] == atm_put_strike, "lastPrice"].iloc[0]
                # Limit the range of strikes around the ATM for a shorter dropdown
                strike_range = 10  # Number of strikes above and below the ATM to display
                atm_index = puts["strike"].tolist().index(atm_put_strike)
                start_index = max(0, atm_index - strike_range)
                end_index = min(len(puts["strike"]), atm_index + strike_range + 1)
                available_strikes = sorted(puts["strike"].iloc[start_index:end_index])
                # Display Current CMP in a styled format
                st.markdown(
                    f"""
                    <style>
                        /* Card Container */
                        .modern-card {{
                            background: linear-gradient(135deg, #2c5364, #0f2027); /* Sophisticated teal-to-dark gradient */
                            border-radius: 15px; /* Rounded corners */
                            padding: 2px 25px;
                            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); /* Soft shadow for elevation */
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            margin: 15px auto;
                            max-width: 700px;
                            transition: transform 0.3s ease, box-shadow 0.3s ease;
                        }}

                        /* Hover Effect */
                        .modern-card:hover {{
                            transform: translateY(-5px);
                            box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5);
                        }}
                        /* Title */
                        .modern-title {{
                            font-size: 20px;
                            font-weight: bold;
                            font-family: 'Arial', sans-serif;
                            color: #d3dde6; /* Subtle pale blue for elegance */
                        }}
                        /* Price */
                        .modern-price {{
                            font-size: 26px;
                            font-weight: bold;
                            color: #f4a261; /* Warm amber-orange for a luxurious touch */
                            font-family: 'Courier New', monospace;
                            text-shadow: 0 2px 5px rgba(244, 162, 97, 0.8); /* Subtle glow effect */
                        }}
                        /* Icon */
                        .modern-icon {{
                            font-size: 30px;
                            color: #d3dde6; /* Matches title color */
                            margin-right: 10px;
                        }}
                    </style>

                    <div class="modern-card">
                        <div style="display: flex; align-items: center;">
                            <span class="modern-icon">📈</span>
                            <span class="modern-title">CMP of {ticker.upper()}:</span>
                        </div>
                        <div class="modern-price">${current_price:.2f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                # Styled dropdown with restricted strike range
                strike_price = st.selectbox(
                    "Select Strike Price (ATM range highlighted):",
                    available_strikes,
                    index=available_strikes.index(atm_put_strike),
                    help="Choose a strike price close to the current market price for better alignment with strategy."
                )
                # Fetch the corresponding market price for the selected strike
                cmp_selected_put = puts.loc[calls["strike"] == strike_price, "lastPrice"].iloc[0]
                # Display the Selected Strike Price and CMP
                st.markdown(
                    f"""
                    <div style="
                        background-color: #f2f2f2; 
                        padding: 12px; 
                        border-radius: 4px; 
                        font-family: Arial, sans-serif; 
                        font-size: 14px; 
                        color: #333;"
                    >
                        <div style="
                            font-size:18px; 
                            font-weight:bold; 
                            margin-bottom:10px; 
                            border-bottom:1px solid #ccc; 
                            padding-bottom:6px;"
                        >
                            Long Put Configuration
                        </div>
                        <div style="margin-bottom:6px;">
                            <strong>Selected Strike Price:</strong> {strike_price}
                        </div>
                        <div>
                            <strong>Put Option Price:</strong> ${cmp_selected_put:.2f}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                cmp_selected_call = calls.loc[calls["strike"] == strike_price, "lastPrice"].iloc[0]
                # Calculate payoff for Long Put
                stock_prices = np.linspace(0.5 * current_price, 1.5 * current_price, 10000)
                payoff = calculate_payoff("Long Put", stock_prices, [strike_price], [cmp_selected_put], ["Put"])
                # Calculate break-even points
                break_even_points = calculate_break_even("Long Put", [strike_price], [cmp_selected_put])

        elif strategy == "Covered Call":
            atm_call_strike = calls.loc[(calls["strike"] - current_price).abs().idxmin(), "strike"]
            cmp_atm_call = calls.loc[calls["strike"] == atm_call_strike, "lastPrice"].iloc[0]
            # Limit the range of strikes around the ATM for a shorter dropdown
            strike_range = 10  # Number of strikes above and below the ATM to display
            atm_index = calls["strike"].tolist().index(atm_call_strike)
            start_index = max(0, atm_index - strike_range)
            end_index = min(len(calls["strike"]), atm_index + strike_range + 1)
            available_strikes = sorted(calls["strike"].iloc[start_index:end_index])
            # Display Current CMP in a styled format
            st.markdown(
                f"""
                <style>
                    /* Card Container */
                    .modern-card {{
                        background: linear-gradient(135deg, #2c5364, #0f2027); /* Sophisticated teal-to-dark gradient */
                        border-radius: 15px; /* Rounded corners */
                        padding: 2px 25px;
                        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); /* Soft shadow for elevation */
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin: 15px auto;
                        max-width: 700px;
                        transition: transform 0.3s ease, box-shadow 0.3s ease;
                    }}
                    /* Hover Effect */
                    .modern-card:hover {{
                        transform: translateY(-5px);
                        box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5);
                    }}
                    /* Title */
                    .modern-title {{
                        font-size: 20px;
                        font-weight: bold;
                        font-family: 'Arial', sans-serif;
                        color: #d3dde6; /* Subtle pale blue for elegance */
                    }}
                    /* Price */
                    .modern-price {{
                        font-size: 26px;
                        font-weight: bold;
                        color: #f4a261; /* Warm amber-orange for a luxurious touch */
                        font-family: 'Courier New', monospace;
                        text-shadow: 0 2px 5px rgba(244, 162, 97, 0.8); /* Subtle glow effect */
                    }}
                    /* Icon */
                    .modern-icon {{
                        font-size: 30px;
                        color: #d3dde6; /* Matches title color */
                        margin-right: 10px;
                    }}
                </style>

                <div class="modern-card">
                    <div style="display: flex; align-items: center;">
                        <span class="modern-icon">📈</span>
                        <span class="modern-title">CMP of {ticker.upper()}:</span>
                    </div>
                    <div class="modern-price">${current_price:.2f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            avg_stock_price = st.number_input("Enter the average stock price you hold:", value=current_price)
            # Dropdown to select strike price with restricted range
            strike_price = st.selectbox(
                "Select Strike Price for Call (ATM range highlighted):",
                available_strikes,
                index=available_strikes.index(atm_call_strike),
                help="Choose a strike price close to the current market price for better alignment with strategy."
            )
            cmp_selected_call = calls.loc[calls["strike"] == strike_price, "lastPrice"].iloc[0]
            # Display the Selected Strike Price and CMP in a styled format
            st.markdown(
                f"""
                <div style="
                    background-color: #f2f2f2; 
                    padding: 12px; 
                    border-radius: 4px; 
                    font-family: Arial, sans-serif; 
                    font-size: 14px; 
                    color: #333;"
                >
                    <div style="
                        font-size:18px; 
                        font-weight:bold; 
                        margin-bottom:10px; 
                        border-bottom:1px solid #ccc; 
                        padding-bottom:6px;"
                    >
                        Covered Call Configuration
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>Average Stock Price:</strong> ${avg_stock_price:.2f}
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>Selected Strike Price:</strong> {strike_price}
                    </div>
                    <div>
                        <strong>Call Option Price:</strong> ${cmp_selected_call:.2f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Calculate payoff for Covered Call
            stock_prices = np.linspace(0.5 * current_price, 1.5 * current_price, 10000)
            payoff = calculate_payoff("Covered Call", stock_prices, [strike_price], [cmp_selected_call], ["Call"],
                                      avg_stock_price=avg_stock_price)
            max_gain = (strike_price - avg_stock_price) + cmp_selected_call
            # Calculate break-even points
            break_even_points = calculate_break_even(
                "Covered Call",
                [strike_price],
                [cmp_selected_call],
                avg_stock_price=avg_stock_price
            )
            # Format break-even points for display
            formatted_breakeven_points = [round(float(point), 2) for point in break_even_points]

        elif strategy == "Protective Put":
            atm_put_strike = puts.loc[(puts["strike"] - current_price).abs().idxmin(), "strike"]
            cmp_atm_put = puts.loc[puts["strike"] == atm_put_strike, "lastPrice"].iloc[0]
            # Limit the range of strikes around the ATM for a shorter dropdown
            strike_range = 10  # Number of strikes above and below the ATM to display
            atm_index = puts["strike"].tolist().index(atm_put_strike)
            start_index = max(0, atm_index - strike_range)
            end_index = min(len(puts["strike"]), atm_index + strike_range + 1)
            available_strikes = sorted(puts["strike"].iloc[start_index:end_index])
            # Display Current CMP in a styled format
            st.markdown(
                f"""
                <style>
                    /* Card Container */
                    .modern-card {{
                        background: linear-gradient(135deg, #2c5364, #0f2027); /* Sophisticated teal-to-dark gradient */
                        border-radius: 15px; /* Rounded corners */
                        padding: 2px 25px;
                        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); /* Soft shadow for elevation */
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin: 15px auto;
                        max-width: 700px;
                        transition: transform 0.3s ease, box-shadow 0.3s ease;
                    }}
                    /* Hover Effect */
                    .modern-card:hover {{
                        transform: translateY(-5px);
                        box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5);
                    }}
                    /* Title */
                    .modern-title {{
                        font-size: 20px;
                        font-weight: bold;
                        font-family: 'Arial', sans-serif;
                        color: #d3dde6; /* Subtle pale blue for elegance */
                    }}
                    /* Price */
                    .modern-price {{
                        font-size: 26px;
                        font-weight: bold;
                        color: #f4a261; /* Warm amber-orange for a luxurious touch */
                        font-family: 'Courier New', monospace;
                        text-shadow: 0 2px 5px rgba(244, 162, 97, 0.8); /* Subtle glow effect */
                    }}
                    /* Icon */
                    .modern-icon {{
                        font-size: 30px;
                        color: #d3dde6; /* Matches title color */
                        margin-right: 10px;
                    }}
                </style>

                <div class="modern-card">
                    <div style="display: flex; align-items: center;">
                        <span class="modern-icon">📈</span>
                        <span class="modern-title">CMP of {ticker.upper()}:</span>
                    </div>
                    <div class="modern-price">${current_price:.2f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            avg_stock_price = st.number_input("Enter the average stock price you hold:", value=current_price)
            # Dropdown to select strike price with restricted range
            strike_price = st.selectbox(
                "Select Strike Price for Put (ATM range highlighted):",
                available_strikes,
                index=available_strikes.index(atm_put_strike),
                help="Choose a strike price close to the current market price for better alignment with strategy."
            )
            # Fetch CMP for the selected strike price
            cmp_selected_put = puts.loc[puts["strike"] == strike_price, "lastPrice"].iloc[0]
            # Display the Selected Strike Price and CMP in a styled format
            st.markdown(
                f"""
                <div style="
                    background-color: #f2f2f2; 
                    padding: 12px; 
                    border-radius: 4px; 
                    font-family: Arial, sans-serif; 
                    font-size: 14px; 
                    color: #333;"
                >
                    <div style="
                        font-size:18px; 
                        font-weight:bold; 
                        margin-bottom:10px; 
                        border-bottom:1px solid #ccc; 
                        padding-bottom:6px;"
                    >
                        Protective Put Configuration
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>Average Stock Price:</strong> ${avg_stock_price:.2f}
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>Selected Strike Price:</strong> {strike_price}
                    </div>
                    <div>
                        <strong>Put Option Price:</strong> ${cmp_selected_put:.2f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Calculate payoff for Protective Put
            stock_prices = np.linspace(0.5 * current_price, 1.5 * current_price, 10000)
            payoff = calculate_payoff(
                "Protective Put",
                stock_prices,
                [strike_price],
                [cmp_selected_put],
                ["Put"],
                avg_stock_price=avg_stock_price
            )
            # Calculate break-even points
            break_even_points = calculate_break_even(
                "Protective Put",
                [strike_price],
                [cmp_selected_put],
                avg_stock_price=avg_stock_price,
            )
            # Format break-even points for display
            formatted_breakeven_points = [round(float(point), 2) for point in break_even_points]

        elif strategy == "Iron Condor":
            # Select strike prices dynamically from the options chain
            # Display Current CMP in a styled format
            st.markdown(
                f"""
                <style>
                    /* Card Container */
                    .modern-card {{
                        background: linear-gradient(135deg, #2c5364, #0f2027); /* Sophisticated teal-to-dark gradient */
                        border-radius: 15px; /* Rounded corners */
                        padding: 2px 25px;
                        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); /* Soft shadow for elevation */
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin: 15px auto;
                        max-width: 700px;
                        transition: transform 0.3s ease, box-shadow 0.3s ease;
                    }}
                    /* Hover Effect */
                    .modern-card:hover {{
                        transform: translateY(-5px);
                        box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5);
                    }}
                    /* Title */
                    .modern-title {{
                        font-size: 20px;
                        font-weight: bold;
                        font-family: 'Arial', sans-serif;
                        color: #d3dde6; /* Subtle pale blue for elegance */
                    }}
                    /* Price */
                    .modern-price {{
                        font-size: 26px;
                        font-weight: bold;
                        color: #f4a261; /* Warm amber-orange for a luxurious touch */
                        font-family: 'Courier New', monospace;
                        text-shadow: 0 2px 5px rgba(244, 162, 97, 0.8); /* Subtle glow effect */
                    }}
                    /* Icon */
                    .modern-icon {{
                        font-size: 30px;
                        color: #d3dde6; /* Matches title color */
                        margin-right: 10px;
                    }}
                </style>

                <div class="modern-card">
                    <div style="display: flex; align-items: center;">
                        <span class="modern-icon">📈</span>
                        <span class="modern-title">CMP of {ticker.upper()}:</span>
                    </div>
                    <div class="modern-price">${current_price:.2f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Select strike prices with focused dropdowns
            short_call_strike = st.selectbox(
                "Select Short Call Strike Price:",
                sorted(calls["strike"]),
                index=(calls["strike"] - (current_price + 5.0)).abs().idxmin(),
                help="Choose the short call strike price for the Iron Condor strategy."
            )
            long_call_strike = st.selectbox(
                "Select Long Call Strike Price (higher than Short Call Strike):",
                sorted(calls["strike"]),
                index=(calls["strike"] - (current_price + 10.0)).abs().idxmin(),
                help="Choose the long call strike price for the Iron Condor strategy."
            )
            short_put_strike = st.selectbox(
                "Select Short Put Strike Price:",
                sorted(puts["strike"]),
                index=(puts["strike"] - (current_price - 5.0)).abs().idxmin(),
                help="Choose the short put strike price for the Iron Condor strategy."
            )
            long_put_strike = st.selectbox(
                "Select Long Put Strike Price (lower than Short Put Strike):",
                sorted(puts["strike"]),
                index=(puts["strike"] - (current_price - 10.0)).abs().idxmin(),
                help="Choose the long put strike price for the Iron Condor strategy."
            )
            # Fetch premiums dynamically from the options data
            short_call_premium = calls.loc[calls["strike"] == short_call_strike, "lastPrice"].iloc[0]
            long_call_premium = calls.loc[calls["strike"] == long_call_strike, "lastPrice"].iloc[0]
            short_put_premium = puts.loc[puts["strike"] == short_put_strike, "lastPrice"].iloc[0]
            long_put_premium = puts.loc[puts["strike"] == long_put_strike, "lastPrice"].iloc[0]
            # Display Iron Condor Configuration
            st.markdown(
                f"""
                <div style="
                    background-color: #f2f2f2; 
                    padding: 12px; 
                    border-radius: 4px; 
                    font-family: Arial, sans-serif; 
                    font-size: 14px; 
                    color: #333;"
                >
                    <div style="
                        font-size:18px; 
                        font-weight:bold; 
                        margin-bottom:10px; 
                        border-bottom:1px solid #ccc; 
                        padding-bottom:6px;"
                    >
                        Iron Condor Conifiguration
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>Short Call Strike:</strong> {short_call_strike}, 
                        <strong>Premium:</strong> ${short_call_premium:.2f}
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>Long Call Strike:</strong> {long_call_strike}, 
                        <strong>Premium:</strong> ${long_call_premium:.2f}
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>Short Put Strike:</strong> {short_put_strike}, 
                        <strong>Premium:</strong> ${short_put_premium:.2f}
                    </div>
                    <div>
                        <strong>Long Put Strike:</strong> {long_put_strike}, 
                        <strong>Premium:</strong> ${long_put_premium:.2f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Stock prices for payoff calculation
            stock_prices = np.linspace(0.5 * current_price, 1.5 * current_price, 10000)
            # Calculate payoff for Iron Condor
            payoff = calculate_payoff(
                "Iron Condor",
                stock_prices,
                [short_call_strike, long_call_strike, short_put_strike, long_put_strike],
                [short_call_premium, long_call_premium, short_put_premium, long_put_premium],
                ["Call", "Call", "Put", "Put"]
            )
            # Calculate break-even points
            break_even_points = calculate_break_even(
                "Iron Condor",
                [short_call_strike, long_call_strike, short_put_strike, long_put_strike],
                [short_call_premium, long_call_premium, short_put_premium, long_put_premium]
            )
            # Format break-even points for display
            formatted_breakeven_points = [round(float(point), 2) for point in break_even_points]

        elif strategy == "Bull Put Spread":
            # Select strike prices dynamically from the options chain
            # Display Current CMP in a styled format
            st.markdown(
                f"""
                <style>
                    /* Card Container */
                    .modern-card {{
                        background: linear-gradient(135deg, #2c5364, #0f2027); /* Sophisticated teal-to-dark gradient */
                        border-radius: 15px; /* Rounded corners */
                        padding: 2px 25px;
                        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); /* Soft shadow for elevation */
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin: 15px auto;
                        max-width: 700px;
                        transition: transform 0.3s ease, box-shadow 0.3s ease;
                    }}
                    /* Hover Effect */
                    .modern-card:hover {{
                        transform: translateY(-5px);
                        box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5);
                    }}
                    /* Title */
                    .modern-title {{
                        font-size: 20px;
                        font-weight: bold;
                        font-family: 'Arial', sans-serif;
                        color: #d3dde6; /* Subtle pale blue for elegance */
                    }}
                    /* Price */
                    .modern-price {{
                        font-size: 26px;
                        font-weight: bold;
                        color: #f4a261; /* Warm amber-orange for a luxurious touch */
                        font-family: 'Courier New', monospace;
                        text-shadow: 0 2px 5px rgba(244, 162, 97, 0.8); /* Subtle glow effect */
                    }}
                    /* Icon */
                    .modern-icon {{
                        font-size: 30px;
                        color: #d3dde6; /* Matches title color */
                        margin-right: 10px;
                    }}
                </style>

                <div class="modern-card">
                    <div style="display: flex; align-items: center;">
                        <span class="modern-icon">📈</span>
                        <span class="modern-title">CMP of {ticker.upper()}:</span>
                    </div>
                    <div class="modern-price">${current_price:.2f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            short_put_strike = st.selectbox(
                "Select Short Put Strike Price (Higher Strike):",
                sorted(puts["strike"]),
                index=(puts["strike"] - (current_price - 5.0)).abs().idxmin(),
                help="Choose a higher strike price for the short put."
            )
            long_put_strike = st.selectbox(
                "Select Long Put Strike Price (Lower Strike):",
                sorted(puts["strike"]),
                index=(puts["strike"] - (current_price - 10.0)).abs().idxmin(),
                help="Choose a lower strike price for the long put."
            )
            # Fetch premiums dynamically from the options data
            short_put_premium = puts.loc[puts["strike"] == short_put_strike, "lastPrice"].iloc[0]
            long_put_premium = puts.loc[puts["strike"] == long_put_strike, "lastPrice"].iloc[0]
            # Display configuration with a styled box
            st.markdown(
                f"""
                <div style="
                    background-color: #f2f2f2; 
                    padding: 12px; 
                    border-radius: 4px; 
                    font-family: Arial, sans-serif; 
                    font-size: 14px; 
                    color: #333;"
                >
                    <div style="
                        font-size:18px; 
                        font-weight:bold; 
                        margin-bottom:10px; 
                        border-bottom:1px solid #ccc; 
                        padding-bottom:6px;"
                    >
                        Bull Put Spread Configuration
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>Short Put Strike:</strong> {short_put_strike}, 
                        <strong>Premium:</strong> ${short_put_premium:.2f}
                    </div>
                    <div>
                        <strong>Long Put Strike:</strong> {long_put_strike}, 
                        <strong>Premium:</strong> ${long_put_premium:.2f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Stock prices for payoff calculation
            stock_prices = np.linspace(0.5 * current_price, 1.5 * current_price, 10000)
            # Calculate payoff for Bull Put Spread
            payoff = calculate_payoff(
                "Bull Put Spread",
                stock_prices,
                [short_put_strike, long_put_strike],
                [short_put_premium, long_put_premium],
                ["Put", "Put"]
            )
            # Calculate break-even points
            strike_prices = [short_put_strike, long_put_strike]  # Define the strikes used
            premiums = [short_put_premium, long_put_premium]  # Define the premiums used
            break_even_points = calculate_break_even("Bull Put Spread", strike_prices, premiums)
            # Format break-even points for display
            formatted_breakeven_points = [round(float(point), 2) for point in break_even_points]

        elif strategy == "Bear Call Spread":
            # Display Current CMP in a styled format
            st.markdown(
                f"""
                <style>
                    /* Card Container */
                    .modern-card {{
                        background: linear-gradient(135deg, #2c5364, #0f2027); /* Sophisticated teal-to-dark gradient */
                        border-radius: 15px; /* Rounded corners */
                        padding: 2px 25px;
                        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); /* Soft shadow for elevation */
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin: 15px auto;
                        max-width: 700px;
                        transition: transform 0.3s ease, box-shadow 0.3s ease;
                    }}
                    /* Hover Effect */
                    .modern-card:hover {{
                        transform: translateY(-5px);
                        box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5);
                    }}
                    /* Title */
                    .modern-title {{
                        font-size: 20px;
                        font-weight: bold;
                        font-family: 'Arial', sans-serif;
                        color: #d3dde6; /* Subtle pale blue for elegance */
                    }}
                    /* Price */
                    .modern-price {{
                        font-size: 26px;
                        font-weight: bold;
                        color: #f4a261; /* Warm amber-orange for a luxurious touch */
                        font-family: 'Courier New', monospace;
                        text-shadow: 0 2px 5px rgba(244, 162, 97, 0.8); /* Subtle glow effect */
                    }}
                    /* Icon */
                    .modern-icon {{
                        font-size: 30px;
                        color: #d3dde6; /* Matches title color */
                        margin-right: 10px;
                    }}
                </style>

                <div class="modern-card">
                    <div style="display: flex; align-items: center;">
                        <span class="modern-icon">📈</span>
                        <span class="modern-title">CMP of {ticker.upper()}:</span>
                    </div>
                    <div class="modern-price">${current_price:.2f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            short_call_strike = st.selectbox(
                "Select Short Call Strike Price (Lower Strike):",
                sorted(calls["strike"]),
                index=(calls["strike"] - (current_price + 5.0)).abs().idxmin(),
            )
            long_call_strike = st.selectbox(
                "Select Long Call Strike Price (Higher Strike):",
                sorted(calls["strike"]),
                index=(calls["strike"] - (current_price + 10.0)).abs().idxmin(),
            )
            # Fetch premiums dynamically from the options data
            short_call_premium = calls.loc[calls["strike"] == short_call_strike, "lastPrice"].iloc[0]
            long_call_premium = calls.loc[calls["strike"] == long_call_strike, "lastPrice"].iloc[0]
            # Display the configuration in a styled card
            st.markdown(
                f"""
                <div style="
                    background-color: #f2f2f2; 
                    padding: 12px; 
                    border-radius: 4px; 
                    font-family: Arial, sans-serif; 
                    font-size: 14px; 
                    color: #333;"
                >
                    <div style="
                        font-size:18px; 
                        font-weight:bold; 
                        margin-bottom:10px; 
                        border-bottom:1px solid #ccc; 
                        padding-bottom:6px;"
                    >
                        Bear Call Spread Configuration
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>Short Call Strike:</strong> {short_call_strike}, 
                        <strong>Premium:</strong> ${short_call_premium:.2f}
                    </div>
                    <div>
                        <strong>Long Call Strike:</strong> {long_call_strike}, 
                        <strong>Premium:</strong> ${long_call_premium:.2f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Stock prices for payoff calculation
            stock_prices = np.linspace(0.5 * current_price, 1.5 * current_price, 10000)
            # Payoff calculation
            payoff = calculate_payoff(
                "Bear Call Spread",
                stock_prices,
                [short_call_strike, long_call_strike],
                [short_call_premium, long_call_premium],
                ["Call", "Call"],
            )
            # Calculate break-even points
            strike_prices = [short_call_strike, long_call_strike]  # Define the strikes used
            premiums = [short_call_premium, long_call_premium]  # Define the premiums used
            break_even_points = calculate_break_even("Bear Call Spread", strike_prices, premiums)
            # Format break-even points for display
            formatted_breakeven_points = [round(float(point), 2) for point in break_even_points]

        elif strategy == "Long Straddle":
            # Display Current CMP in a styled format
            st.markdown(
                f"""
                <style>
                    /* Card Container */
                    .modern-card {{
                        background: linear-gradient(135deg, #2c5364, #0f2027); /* Sophisticated teal-to-dark gradient */
                        border-radius: 15px; /* Rounded corners */
                        padding: 2px 25px;
                        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); /* Soft shadow for elevation */
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin: 15px auto;
                        max-width: 700px;
                        transition: transform 0.3s ease, box-shadow 0.3s ease;
                    }}
                    /* Hover Effect */
                    .modern-card:hover {{
                        transform: translateY(-5px);
                        box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5);
                    }}
                    /* Title */
                    .modern-title {{
                        font-size: 20px;
                        font-weight: bold;
                        font-family: 'Arial', sans-serif;
                        color: #d3dde6; /* Subtle pale blue for elegance */
                    }}
                    /* Price */
                    .modern-price {{
                        font-size: 26px;
                        font-weight: bold;
                        color: #f4a261; /* Warm amber-orange for a luxurious touch */
                        font-family: 'Courier New', monospace;
                        text-shadow: 0 2px 5px rgba(244, 162, 97, 0.8); /* Subtle glow effect */
                    }}
                    /* Icon */
                    .modern-icon {{
                        font-size: 30px;
                        color: #d3dde6; /* Matches title color */
                        margin-right: 10px;
                    }}
                </style>

                <div class="modern-card">
                    <div style="display: flex; align-items: center;">
                        <span class="modern-icon">📈</span>
                        <span class="modern-title">CMP of {ticker.upper()}:</span>
                    </div>
                    <div class="modern-price">${current_price:.2f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Dropdown for selecting call strike price
            call_strike = st.selectbox(
                "Select Call Strike Price:",
                sorted(calls["strike"]),
                index=(calls["strike"] - current_price).abs().idxmin(),  # Closest to current price
                help="Select the strike price for the call leg of the straddle."
            )
            # Dropdown for selecting put strike price
            put_strike = st.selectbox(
                "Select Put Strike Price:",
                sorted(puts["strike"]),
                index=(puts["strike"] - current_price).abs().idxmin(),  # Closest to current price
                help="Select the strike price for the put leg of the straddle."
            )
            # Fetch premiums dynamically based on selected strikes
            call_premium = calls.loc[calls["strike"] == call_strike, "lastPrice"].iloc[0]
            put_premium = puts.loc[puts["strike"] == put_strike, "lastPrice"].iloc[0]
            # Display the configuration details in a styled card
            st.markdown(
                f"""
                <div style="
                    background-color: #f2f2f2; 
                    padding: 12px; 
                    border-radius: 4px; 
                    font-family: Arial, sans-serif; 
                    font-size: 14px; 
                    color: #333;"
                >
                    <div style="
                        font-size:18px; 
                        font-weight:bold; 
                        margin-bottom:10px; 
                        border-bottom:1px solid #ccc; 
                        padding-bottom:6px;"
                    >
                        Long Straddle Configuration
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>Call Strike Price:</strong> {call_strike}, 
                        <strong>Premium:</strong> ${call_premium:.2f}
                    </div>
                    <div>
                        <strong>Put Strike Price:</strong> {put_strike}, 
                        <strong>Premium:</strong> ${put_premium:.2f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Stock prices for payoff calculation
            stock_prices = np.linspace(0.5 * current_price, 1.5 * current_price, 10000)
            # Calculate payoff for Long Straddle
            payoff = calculate_payoff(
                "Long Straddle",
                stock_prices,
                [call_strike, put_strike],  # Strikes for Call and Put
                [call_premium, put_premium],  # Premiums for Call and Put
                ["Call", "Put"],
            )
            # Calculate break-even points
            strike_prices = [call_strike, put_strike]
            premiums = [call_premium, put_premium]
            break_even_points = calculate_break_even("Long Straddle", strike_prices, premiums)
            # Format break-even points for display
            formatted_breakeven_points = [round(float(point), 2) for point in break_even_points]

        elif strategy == "Short Straddle":
            # Display Current CMP in a styled format
            st.markdown(
                f"""
                <style>
                    /* Card Container */
                    .modern-card {{
                        background: linear-gradient(135deg, #2c5364, #0f2027); /* Sophisticated teal-to-dark gradient */
                        border-radius: 15px; /* Rounded corners */
                        padding: 2px 25px;
                        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); /* Soft shadow for elevation */
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin: 15px auto;
                        max-width: 700px;
                        transition: transform 0.3s ease, box-shadow 0.3s ease;
                    }}

                    /* Hover Effect */
                    .modern-card:hover {{
                        transform: translateY(-5px);
                        box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5);
                    }}
                    /* Title */
                    .modern-title {{
                        font-size: 20px;
                        font-weight: bold;
                        font-family: 'Arial', sans-serif;
                        color: #d3dde6; /* Subtle pale blue for elegance */
                    }}
                    /* Price */
                    .modern-price {{
                        font-size: 26px;
                        font-weight: bold;
                        color: #f4a261; /* Warm amber-orange for a luxurious touch */
                        font-family: 'Courier New', monospace;
                        text-shadow: 0 2px 5px rgba(244, 162, 97, 0.8); /* Subtle glow effect */
                    }}
                    /* Icon */
                    .modern-icon {{
                        font-size: 30px;
                        color: #d3dde6; /* Matches title color */
                        margin-right: 10px;
                    }}
                </style>

                <div class="modern-card">
                    <div style="display: flex; align-items: center;">
                        <span class="modern-icon">📈</span>
                        <span class="modern-title">CMP of {ticker.upper()}:</span>
                    </div>
                    <div class="modern-price">${current_price:.2f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Dropdown for selecting call strike price
            call_strike = st.selectbox(
                "Select Call Strike Price:",
                sorted(calls["strike"]),
                index=(calls["strike"] - current_price).abs().idxmin(),  # Closest to current price
                help="Select the strike price for the call leg of the straddle."
            )
            # Dropdown for selecting put strike price
            put_strike = st.selectbox(
                "Select Put Strike Price:",
                sorted(puts["strike"]),
                index=(puts["strike"] - current_price).abs().idxmin(),  # Closest to current price
                help="Select the strike price for the put leg of the straddle."
            )
            # Fetch premiums dynamically based on selected strikes
            call_premium = calls.loc[calls["strike"] == call_strike, "lastPrice"].iloc[0]
            put_premium = puts.loc[puts["strike"] == put_strike, "lastPrice"].iloc[0]
            # Display the selected strike price and fetched premiums
            st.markdown(
                f"""
                <div style="
                    background-color: #f2f2f2; 
                    padding: 12px; 
                    border-radius: 4px; 
                    font-family: Arial, sans-serif; 
                    font-size: 14px; 
                    color: #333;"
                >
                    <div style="
                        font-size:18px; 
                        font-weight:bold; 
                        margin-bottom:10px; 
                        border-bottom:1px solid #ccc; 
                        padding-bottom:6px;"
                    >
                        Short Straddle Configuration
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>Call Strike Price:</strong> {call_strike}, 
                        <strong>Premium:</strong> ${call_premium:.2f}
                    </div>
                    <div>
                        <strong>Put Strike Price:</strong> {put_strike}, 
                        <strong>Premium:</strong> ${put_premium:.2f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Stock prices for payoff calculation
            stock_prices = np.linspace(0.5 * current_price, 1.5 * current_price, 10000)
            # Calculate payoff for Short Straddle
            payoff = calculate_payoff(
                "Short Straddle",
                stock_prices,
                [call_strike, put_strike],
                [call_premium, put_premium],
                ["Call", "Put"]
            )
            # Calculate break-even points
            strike_prices = [call_strike, put_strike]
            premiums = [call_premium, put_premium]
            break_even_points = calculate_break_even("Short Straddle", strike_prices, premiums)
            # Format break-even points for display
            formatted_breakeven_points = [round(float(point), 2) for point in break_even_points]

        elif strategy == "Long Strangle":
            # Display Current CMP in a styled format
            st.markdown(
                f"""
                <style>
                    /* Card Container */
                    .modern-card {{
                        background: linear-gradient(135deg, #2c5364, #0f2027); /* Sophisticated teal-to-dark gradient */
                        border-radius: 15px; /* Rounded corners */
                        padding: 2px 25px;
                        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); /* Soft shadow for elevation */
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin: 15px auto;
                        max-width: 700px;
                        transition: transform 0.3s ease, box-shadow 0.3s ease;
                    }}

                    /* Hover Effect */
                    .modern-card:hover {{
                        transform: translateY(-5px);
                        box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5);
                    }}

                    /* Title */
                    .modern-title {{
                        font-size: 20px;
                        font-weight: bold;
                        font-family: 'Arial', sans-serif;
                        color: #d3dde6; /* Subtle pale blue for elegance */
                    }}

                    /* Price */
                    .modern-price {{
                        font-size: 26px;
                        font-weight: bold;
                        color: #f4a261; /* Warm amber-orange for a luxurious touch */
                        font-family: 'Courier New', monospace;
                        text-shadow: 0 2px 5px rgba(244, 162, 97, 0.8); /* Subtle glow effect */
                    }}

                    /* Icon */
                    .modern-icon {{
                        font-size: 30px;
                        color: #d3dde6; /* Matches title color */
                        margin-right: 10px;
                    }}
                </style>

                <div class="modern-card">
                    <div style="display: flex; align-items: center;">
                        <span class="modern-icon">📈</span>
                        <span class="modern-title">CMP of {ticker.upper()}:</span>
                    </div>
                    <div class="modern-price">${current_price:.2f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Dropdown for selecting OTM call strike price
            otm_call_strike = st.selectbox(
                "Select OTM Call Strike Price:",
                sorted(calls["strike"]),
                index=(calls["strike"] - (current_price + 5.0)).abs().idxmin(),  # OTM Call Strike
                help="Select the strike price for the call leg of the strangle."
            )
            # Dropdown for selecting OTM put strike price
            otm_put_strike = st.selectbox(
                "Select OTM Put Strike Price:",
                sorted(puts["strike"]),
                index=(puts["strike"] - (current_price - 5.0)).abs().idxmin(),  # OTM Put Strike
                help="Select the strike price for the put leg of the strangle."
            )
            # Fetch premiums dynamically based on selected strikes
            cmp_call = calls.loc[calls["strike"] == otm_call_strike, "lastPrice"].iloc[0]
            cmp_put = puts.loc[puts["strike"] == otm_put_strike, "lastPrice"].iloc[0]
            # Display the selected strikes and fetched premiums
            st.markdown(
                f"""
                <div style="
                    background-color: #f2f2f2; 
                    padding: 12px; 
                    border-radius: 4px; 
                    font-family: Arial, sans-serif; 
                    font-size: 14px; 
                    color: #333;"
                >
                    <div style="
                        font-size:18px; 
                        font-weight:bold; 
                        margin-bottom:10px; 
                        border-bottom:1px solid #ccc; 
                        padding-bottom:6px;"
                    >
                        Long Strangle Configuration
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>Call Strike Price:</strong> {otm_call_strike}, 
                        <strong style="color: #cb4335;">Premium: ${cmp_call:.2f}</strong>
                    </div>
                    <div>
                        <strong>Put Strike Price:</strong> {otm_put_strike}, 
                        <strong style="color: #28b463;">Premium: ${cmp_put:.2f}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Stock prices for payoff calculation
            stock_prices = np.linspace(0.5 * current_price, 1.5 * current_price, 10000)
            # Calculate payoff for Long Strangle
            payoff = calculate_payoff(
                "Long Strangle",
                stock_prices,
                [otm_call_strike, otm_put_strike],  # Strikes for OTM Call and Put
                [cmp_call, cmp_put],  # Premiums for Call and Put
                ["Call", "Put"],
            )
            # Calculate break-even points
            strike_prices = [otm_call_strike, otm_put_strike]  # Define OTM call and put strike prices
            premiums = [cmp_call, cmp_put]  # Define premiums for call and put
            break_even_points = calculate_break_even("Long Strangle", strike_prices, premiums)
            # Format break-even points for display
            formatted_breakeven_points = [round(float(point), 2) for point in break_even_points]

        elif strategy == "Short Strangle":
            # Display Current CMP in a styled format
            st.markdown(
                f"""
                <style>
                    /* Card Container */
                    .modern-card {{
                        background: linear-gradient(135deg, #2c5364, #0f2027); /* Sophisticated teal-to-dark gradient */
                        border-radius: 15px; /* Rounded corners */
                        padding: 2px 25px;
                        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); /* Soft shadow for elevation */
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin: 15px auto;
                        max-width: 700px;
                        transition: transform 0.3s ease, box-shadow 0.3s ease;
                    }}
                    /* Hover Effect */
                    .modern-card:hover {{
                        transform: translateY(-5px);
                        box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5);
                    }}
                    /* Title */
                    .modern-title {{
                        font-size: 20px;
                        font-weight: bold;
                        font-family: 'Arial', sans-serif;
                        color: #d3dde6; /* Subtle pale blue for elegance */
                    }}
                    /* Price */
                    .modern-price {{
                        font-size: 26px;
                        font-weight: bold;
                        color: #f4a261; /* Warm amber-orange for a luxurious touch */
                        font-family: 'Courier New', monospace;
                        text-shadow: 0 2px 5px rgba(244, 162, 97, 0.8); /* Subtle glow effect */
                    }}
                    /* Icon */
                    .modern-icon {{
                        font-size: 30px;
                        color: #d3dde6; /* Matches title color */
                        margin-right: 10px;
                    }}
                </style>

                <div class="modern-card">
                    <div style="display: flex; align-items: center;">
                        <span class="modern-icon">📈</span>
                        <span class="modern-title">CMP of {ticker.upper()}:</span>
                    </div>
                    <div class="modern-price">${current_price:.2f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Dropdown for selecting OTM call strike price
            otm_call_strike = st.selectbox(
                "Select OTM Call Strike Price:",
                sorted(calls["strike"]),
                index=(calls["strike"] - (current_price + 5.0)).abs().idxmin(),  # OTM Call Strike
                help="Select the strike price for the call leg of the strangle."
            )
            # Dropdown for selecting OTM put strike price
            otm_put_strike = st.selectbox(
                "Select OTM Put Strike Price:",
                sorted(puts["strike"]),
                index=(puts["strike"] - (current_price - 5.0)).abs().idxmin(),  # OTM Put Strike
                help="Select the strike price for the put leg of the strangle."
            )
            # Fetch premiums dynamically based on selected strikes
            cmp_call = calls.loc[calls["strike"] == otm_call_strike, "lastPrice"].iloc[0]
            cmp_put = puts.loc[puts["strike"] == otm_put_strike, "lastPrice"].iloc[0]
            # Display the selected strikes and fetched premiums
            st.markdown(
                f"""
                <div style="
                    background-color: #f2f2f2; 
                    padding: 12px; 
                    border-radius: 4px; 
                    font-family: Arial, sans-serif; 
                    font-size: 14px; 
                    color: #333;"
                >
                    <div style="
                        font-size:18px; 
                        font-weight:bold; 
                        margin-bottom:10px; 
                        border-bottom:1px solid #ccc; 
                        padding-bottom:6px;"
                    >
                        Short Strangle Configuration
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>Call Strike Price:</strong> {otm_call_strike}, 
                        <strong style="color: #cb4335;">Premium: ${cmp_call:.2f}</strong>
                    </div>
                    <div>
                        <strong>Put Strike Price:</strong> {otm_put_strike}, 
                        <strong style="color: #28b463;">Premium: ${cmp_put:.2f}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Stock prices for payoff calculation
            stock_prices = np.linspace(0.5 * current_price, 1.5 * current_price, 10000)
            # Calculate payoff for Short Strangle
            payoff = calculate_payoff(
                "Short Strangle",
                stock_prices,
                [otm_call_strike, otm_put_strike],  # Strikes for OTM Call and Put
                [cmp_call, cmp_put],  # Premiums for Call and Put
                ["Call", "Put"],
            )
            # Calculate break-even points
            strike_prices = [otm_call_strike, otm_put_strike]  # Define OTM call and put strike prices
            premiums = [cmp_call, cmp_put]  # Define premiums for call and put
            break_even_points = calculate_break_even("Short Strangle", strike_prices, premiums)
            # Format break-even points for display
            formatted_breakeven_points = [round(float(point), 2) for point in break_even_points]

        elif strategy == "Butterfly Spread":
            # Display Current CMP in a styled format
            st.markdown(
                f"""
                <style>
                    /* Card Container */
                    .modern-card {{
                        background: linear-gradient(135deg, #2c5364, #0f2027); /* Sophisticated teal-to-dark gradient */
                        border-radius: 15px; /* Rounded corners */
                        padding: 2px 25px;
                        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); /* Soft shadow for elevation */
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin: 15px auto;
                        max-width: 700px;
                        transition: transform 0.3s ease, box-shadow 0.3s ease;
                    }}
                    /* Hover Effect */
                    .modern-card:hover {{
                        transform: translateY(-5px);
                        box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5);
                    }}
                    /* Title */
                    .modern-title {{
                        font-size: 20px;
                        font-weight: bold;
                        font-family: 'Arial', sans-serif;
                        color: #d3dde6; /* Subtle pale blue for elegance */
                    }}
                    /* Price */
                    .modern-price {{
                        font-size: 26px;
                        font-weight: bold;
                        color: #f4a261; /* Warm amber-orange for a luxurious touch */
                        font-family: 'Courier New', monospace;
                        text-shadow: 0 2px 5px rgba(244, 162, 97, 0.8); /* Subtle glow effect */
                    }}
                    /* Icon */
                    .modern-icon {{
                        font-size: 30px;
                        color: #d3dde6; /* Matches title color */
                        margin-right: 10px;
                    }}
                </style>

                <div class="modern-card">
                    <div style="display: flex; align-items: center;">
                        <span class="modern-icon">📈</span>
                        <span class="modern-title">CMP of {ticker.upper()}:</span>
                    </div>
                    <div class="modern-price">${current_price:.2f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Dropdown for selecting ITM Call Strike Price
            itm_call_strike = st.selectbox(
                "Select ITM Call Strike Price:",
                sorted(calls["strike"]),
                index=(calls["strike"] - (current_price - 5.0)).abs().idxmin(),  # Closest to ITM
                help="Select the In-The-Money (ITM) strike price for the call leg of the Butterfly Spread."
            )
            # Dropdown for selecting ATM Call Strike Price
            atm_call_strike = st.selectbox(
                "Select ATM Call Strike Price:",
                sorted(calls["strike"]),
                index=(calls["strike"] - current_price).abs().idxmin(),  # Closest to ATM
                help="Select the At-The-Money (ATM) strike price for the call leg of the Butterfly Spread."
            )
            # Dropdown for selecting OTM Call Strike Price
            otm_call_strike = st.selectbox(
                "Select OTM Call Strike Price:",
                sorted(calls["strike"]),
                index=(calls["strike"] - (current_price + 5.0)).abs().idxmin(),  # Closest to OTM
                help="Select the Out-Of-The-Money (OTM) strike price for the call leg of the Butterfly Spread."
            )
            # Fetch premiums dynamically based on selected strikes
            itm_call_premium = calls.loc[calls["strike"] == itm_call_strike, "lastPrice"].iloc[0]
            atm_call_premium = calls.loc[calls["strike"] == atm_call_strike, "lastPrice"].iloc[0]
            otm_call_premium = calls.loc[calls["strike"] == otm_call_strike, "lastPrice"].iloc[0]
            strike_prices = [itm_call_strike, atm_call_strike, otm_call_strike]
            premiums = [itm_call_premium, atm_call_premium, otm_call_premium]
            # Display the selected strikes and fetched premiums
            st.markdown(
                f"""
                <div style="
                    background-color: #f2f2f2; 
                    padding: 12px; 
                    border-radius: 4px; 
                    font-family: Arial, sans-serif; 
                    font-size: 14px; 
                    color: #333;"
                >
                    <div style="
                        font-size:18px; 
                        font-weight:bold; 
                        margin-bottom:10px; 
                        border-bottom:1px solid #ccc; 
                        padding-bottom:6px;"
                    >
                        Butterfly Spread Configuration
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>ITM Call Strike:</strong> {itm_call_strike}, 
                        <strong style="color: #cb4335;">Premium: ${itm_call_premium:.2f}</strong>
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>ATM Call Strike:</strong> {atm_call_strike}, 
                        <strong style="color: #2874a6;">Premium: ${atm_call_premium:.2f}</strong>
                    </div>
                    <div>
                        <strong>OTM Call Strike:</strong> {otm_call_strike}, 
                        <strong style="color: #28b463;">Premium: ${otm_call_premium:.2f}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Stock prices for payoff calculation
            stock_prices = np.linspace(0.5 * current_price, 1.5 * current_price, 10000)
            # Calculate payoff for Butterfly Spread
            payoff = calculate_payoff(
                "Butterfly Spread",
                stock_prices,
                strike_prices,
                premiums,
                ["Call", "Call", "Call"]
            )
            break_even_points = calculate_break_even("Butterfly Spread", strike_prices, premiums)
            # Format break-even points for display
            formatted_breakeven_points = [round(float(point), 2) for point in break_even_points]

        elif strategy == "Iron Butterfly":
            # Display Current CMP in a styled format
            st.markdown(
                f"""
                <style>
                    /* Card Container */
                    .modern-card {{
                        background: linear-gradient(135deg, #2c5364, #0f2027); /* Sophisticated teal-to-dark gradient */
                        border-radius: 15px; /* Rounded corners */
                        padding: 2px 25px;
                        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); /* Soft shadow for elevation */
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin: 15px auto;
                        max-width: 700px;
                        transition: transform 0.3s ease, box-shadow 0.3s ease;
                    }}
                    /* Hover Effect */
                    .modern-card:hover {{
                        transform: translateY(-5px);
                        box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5);
                    }}

                    /* Title */
                    .modern-title {{
                        font-size: 20px;
                        font-weight: bold;
                        font-family: 'Arial', sans-serif;
                        color: #d3dde6; /* Subtle pale blue for elegance */
                    }}
                    /* Price */
                    .modern-price {{
                        font-size: 26px;
                        font-weight: bold;
                        color: #f4a261; /* Warm amber-orange for a luxurious touch */
                        font-family: 'Courier New', monospace;
                        text-shadow: 0 2px 5px rgba(244, 162, 97, 0.8); /* Subtle glow effect */
                    }}
                    /* Icon */
                    .modern-icon {{
                        font-size: 30px;
                        color: #d3dde6; /* Matches title color */
                        margin-right: 10px;
                    }}
                </style>

                <div class="modern-card">
                    <div style="display: flex; align-items: center;">
                        <span class="modern-icon">📈</span>
                        <span class="modern-title">CMP of {ticker.upper()}:</span>
                    </div>
                    <div class="modern-price">${current_price:.2f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Dropdowns for selecting strike prices
            lower_put_strike = st.selectbox(
                "Select Lower Strike Price (Long Put):",
                sorted(puts["strike"]),
                index=(puts["strike"] - (current_price - 10.0)).abs().idxmin(),
                help="Select the lower strike price for the long put leg of the Iron Butterfly strategy."
            )
            short_put_strike = st.selectbox(
                "Select Short Put Strike Price:",
                sorted(puts["strike"]),
                index=(puts["strike"] - current_price).abs().idxmin(),
                help="Select the strike price for the short put leg of the Iron Butterfly strategy."
            )
            short_call_strike = st.selectbox(
                "Select Short Call Strike Price:",
                sorted(calls["strike"]),
                index=(calls["strike"] - current_price).abs().idxmin(),
                help="Select the strike price for the short call leg of the Iron Butterfly strategy."
            )
            higher_call_strike = st.selectbox(
                "Select Higher Strike Price (Long Call):",
                sorted(calls["strike"]),
                index=(calls["strike"] - (current_price + 10.0)).abs().idxmin(),
                help="Select the higher strike price for the long call leg of the Iron Butterfly strategy."
            )
            # Fetch premiums dynamically from the options data
            lower_put_premium = puts.loc[puts["strike"] == lower_put_strike, "lastPrice"].iloc[0]
            short_put_premium = puts.loc[puts["strike"] == short_put_strike, "lastPrice"].iloc[0]
            short_call_premium = calls.loc[calls["strike"] == short_call_strike, "lastPrice"].iloc[0]
            higher_call_premium = calls.loc[calls["strike"] == higher_call_strike, "lastPrice"].iloc[0]
            # Display the selected strikes and fetched premiums
            st.markdown(
                f"""
                <div style="
                    background-color: #f2f2f2; 
                    padding: 12px; 
                    border-radius: 4px; 
                    font-family: Arial, sans-serif; 
                    font-size: 14px; 
                    color: #333;"
                >
                    <div style="
                        font-size:18px; 
                        font-weight:bold; 
                        margin-bottom:10px; 
                        border-bottom:1px solid #ccc; 
                        padding-bottom:6px;"
                    >
                        Iron Butterfly Configuration
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>Lower Strike Price (Long Put):</strong> {lower_put_strike}, 
                        <strong>Premium:</strong> <span style="color: #239b56;">${lower_put_premium:.2f}</span>
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>Short Strike Price (Short Put):</strong> {short_put_strike}, 
                        <strong>Premium:</strong> <span style="color: #cb4335;">${short_put_premium:.2f}</span>
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>Short Strike Price (Short Call):</strong> {short_call_strike}, 
                        <strong>Premium:</strong> <span style="color: #2874a6;">${short_call_premium:.2f}</span>
                    </div>
                    <div>
                        <strong>Higher Strike Price (Long Call):</strong> {higher_call_strike}, 
                        <strong>Premium:</strong> <span style="color: #cb4335;">${higher_call_premium:.2f}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Stock prices for payoff calculation
            stock_prices = np.linspace(0.5 * current_price, 1.5 * current_price, 10000)
            # Calculate payoff for Iron Butterfly
            payoff = calculate_payoff(
                "Iron Butterfly",
                stock_prices,
                [lower_put_strike, short_put_strike, short_call_strike, higher_call_strike],
                [lower_put_premium, short_put_premium, short_call_premium, higher_call_premium],
                ["Put", "Put", "Call", "Call"]
            )
            # Calculate break-even points
            total_premium_received = short_put_premium + short_call_premium - (lower_put_premium + higher_call_premium)
            lower_bep = short_put_strike - total_premium_received
            upper_bep = short_call_strike + total_premium_received
            break_even_points = [round(lower_bep, 2), round(upper_bep, 2)]
            # Format break-even points for display
            formatted_breakeven_points = [round(float(point), 2) for point in break_even_points]

        elif strategy == "Collar":
            # Display Current CMP in a styled format
            st.markdown(
                f"""
                <style>
                    /* Card Container */
                    .modern-card {{
                        background: linear-gradient(135deg, #2c5364, #0f2027); /* Sophisticated teal-to-dark gradient */
                        border-radius: 15px; /* Rounded corners */
                        padding: 2px 25px;
                        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); /* Soft shadow for elevation */
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin: 15px auto;
                        max-width: 700px;
                        transition: transform 0.3s ease, box-shadow 0.3s ease;
                    }}
                    /* Hover Effect */
                    .modern-card:hover {{
                        transform: translateY(-5px);
                        box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5);
                    }}
                    /* Title */
                    .modern-title {{
                        font-size: 20px;
                        font-weight: bold;
                        font-family: 'Arial', sans-serif;
                        color: #d3dde6; /* Subtle pale blue for elegance */
                    }}
                    /* Price */
                    .modern-price {{
                        font-size: 26px;
                        font-weight: bold;
                        color: #f4a261; /* Warm amber-orange for a luxurious touch */
                        font-family: 'Courier New', monospace;
                        text-shadow: 0 2px 5px rgba(244, 162, 97, 0.8); /* Subtle glow effect */
                    }}
                    /* Icon */
                    .modern-icon {{
                        font-size: 30px;
                        color: #d3dde6; /* Matches title color */
                        margin-right: 10px;
                    }}
                </style>

                <div class="modern-card">
                    <div style="display: flex; align-items: center;">
                        <span class="modern-icon">📈</span>
                        <span class="modern-title">CMP of {ticker.upper()}:</span>
                    </div>
                    <div class="modern-price">${current_price:.2f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # User input for average stock price
            avg_stock_price = st.number_input(
                "Enter the average stock price you hold:",
                value=current_price,
                help="Enter the average price at which you purchased the stock."
            )
            # Dropdowns for selecting strike prices
            protective_put_strike = st.selectbox(
                "Select Protective Put Strike Price (Long Put):",
                sorted(puts["strike"]),
                index=(puts["strike"] - (current_price - 5.0)).abs().idxmin(),
                help="Select the strike price for the protective put leg of the Collar strategy."
            )
            covered_call_strike = st.selectbox(
                "Select Covered Call Strike Price (Short Call):",
                sorted(calls["strike"]),
                index=(calls["strike"] - (current_price + 5.0)).abs().idxmin(),
                help="Select the strike price for the covered call leg of the Collar strategy."
            )
            # Fetch premiums dynamically from the options data
            protective_put_premium = puts.loc[puts["strike"] == protective_put_strike, "lastPrice"].iloc[0]
            covered_call_premium = calls.loc[calls["strike"] == covered_call_strike, "lastPrice"].iloc[0]
            # Display the selected strikes and fetched premiums
            st.markdown(
                f"""
                <div style="
                    background-color: #f2f2f2; 
                    padding: 12px; 
                    border-radius: 4px; 
                    font-family: Arial, sans-serif; 
                    font-size: 14px; 
                    color: #333;"
                >
                    <div style="
                        font-size:18px; 
                        font-weight:bold; 
                        margin-bottom:10px; 
                        border-bottom:1px solid #ccc; 
                        padding-bottom:6px;"
                    >
                        Collar Configuration
                    </div>
                    <div style="margin-bottom:6px;">
                        <strong>Protective Put Strike Price (Long Put):</strong> {protective_put_strike}, 
                        <strong>Premium:</strong> <span style="color: #239b56;">${protective_put_premium:.2f}</span>
                    </div>
                    <div>
                        <strong>Covered Call Strike Price (Short Call):</strong> {covered_call_strike}, 
                        <strong>Premium:</strong> <span style="color: #cb4335;">${covered_call_premium:.2f}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Stock prices for payoff calculation
            stock_prices = np.linspace(0.5 * current_price, 1.5 * current_price, 10000)
            # Calculate payoff for Collar
            payoff = calculate_payoff(
                "Collar",
                stock_prices,
                [protective_put_strike, covered_call_strike],
                [protective_put_premium, covered_call_premium],
                ["Put", "Call"],
                avg_stock_price=avg_stock_price
            )
            # Calculate break-even points
            net_premium = protective_put_premium - covered_call_premium
            break_even_points = [round(avg_stock_price + net_premium, 2)]  # Ensure break-even points is a list


        # Display Payoff Chart
        st.write("## Payoff Visualization")
        formatted_breakeven_points = [round(float(point), 2) for point in
                                      break_even_points] if break_even_points else []
        # Pass the break-even points to the chart function
        payoff_chart = create_interactive_payoff_chart(stock_prices, payoff, strategy,
                                                       break_even_points=formatted_breakeven_points)
        st.plotly_chart(payoff_chart)

        # Display Break-Even Points After the Chart
        st.markdown("## Break-Even Points")

        if formatted_breakeven_points:
            # Define strategy-specific messages
            if strategy == "Long Call":
                strategy_message = (
                    f"If the stock price rises above the break-even point "
                    f"({', '.join(map(str, formatted_breakeven_points))}), you will start making money. "
                    f"However, if the stock price expires below the break-even point, "
                    f"you will lose the premium you paid, which is ${cmp_selected_call:.2f}."
                )
            elif strategy == "Long Put":
                strategy_message = (
                    f"If the stock price falls below the break-even point "
                    f"({', '.join(map(str, formatted_breakeven_points))}), you will start making money. "
                    f"However, if the stock price expires above the break-even point, "
                    f"you will lose the premium you paid, which is ${cmp_selected_put:.2f}."
                )
            elif strategy == "Covered Call":
                strategy_message = (
                    f"You will start making a loss if the stock price falls below "
                    f"{', '.join(map(str, formatted_breakeven_points))}. "
                    f"If the price exceeds this level, your gains are capped at "
                    f"${max_gain:.2f} per share due to the call option sold."
                )
            elif strategy == "Protective Put":
                strategy_message = (
                    f"This strategy protects your downside. Your losses will be limited if the stock "
                    f"price drops below {', '.join(map(str, formatted_breakeven_points))}."
                )
            elif strategy == "Iron Condor":
                # Ensure there are exactly two break-even points
                if len(formatted_breakeven_points) == 2:
                    lower_bep, upper_bep = formatted_breakeven_points  # Unpack the two break-even points
                    strategy_message = (
                        f"The break-even points for this strategy are: {lower_bep} and {upper_bep}. "
                        f"If the stock price falls below {lower_bep} or rises above {upper_bep}, you will start losing money. "
                        f"To maximize profit, the stock price should stay between these two points."
                    )
            elif strategy == "Bull Put Spread":
                strategy_message = (
                    f"You will start incurring losses if the stock price falls below {', '.join(map(str, formatted_breakeven_points))}. "
                    f"However, both your potential profit and losses are limited due to the structure of this strategy."
                )
            elif strategy == "Bear Call Spread":
                strategy_message = (
                    f"You will start making losses if the stock price rise above {', '.join(map(str, formatted_breakeven_points))}. "
                    f"However, both your potential profit and losses are limited due to the structure of this strategy."
                )
            elif strategy == "Long Straddle":
                if len(formatted_breakeven_points) == 2:
                    lower_bep, upper_bep = formatted_breakeven_points  # Unpack the two break-even points
                    strategy_message = (
                        f"The break-even points for this strategy are: {lower_bep} and {upper_bep}. "
                        f"If the stock price falls below {lower_bep} or rises above {upper_bep}, you will start making money. "
                        f"If the stock price stays between these two points you will incur loss."
                    )
            elif strategy == "Short Straddle":
                if len(formatted_breakeven_points) == 2:
                    lower_bep, upper_bep = formatted_breakeven_points  # Unpack the two break-even points
                    strategy_message = (
                        f"The break-even points for this strategy are: {lower_bep} and {upper_bep}. "
                        f"If the stock price falls below {lower_bep} or rises above {upper_bep}, you will start losing money. "
                        f"To maximize profit, the stock price should stay between these two points."
                    )
            elif strategy == "Long Strangle":
                if len(formatted_breakeven_points) == 2:
                    lower_bep, upper_bep = formatted_breakeven_points  # Unpack the two break-even points
                    strategy_message = (
                        f"The break-even points for this strategy are: {lower_bep} and {upper_bep}. "
                        f"If the stock price falls below {lower_bep} or rises above {upper_bep}, you will start making money. "
                        f"If the stock price stays between these two points you will incur loss."
                    )
            elif strategy == "Short Strangle":
                if len(formatted_breakeven_points) == 2:
                    lower_bep, upper_bep = formatted_breakeven_points  # Unpack the two break-even points
                    strategy_message = (
                        f"The break-even points for this strategy are: {lower_bep} and {upper_bep}. "
                        f"If the stock price falls below {lower_bep} or rises above {upper_bep}, you will start losing money. "
                        f"To maximize profit, the stock price should stay between these two points."
                    )
            elif strategy == "Butterfly Spread":
                if len(formatted_breakeven_points) == 2:
                    lower_bep, upper_bep = formatted_breakeven_points  # Unpack the two break-even points
                    strategy_message = (
                        f"The break-even points for this strategy are: {lower_bep} and {upper_bep}. "
                        f"If the stock price falls below {lower_bep} or rises above {upper_bep}, you will start losing money. "
                        f"To maximize profit, the stock price should stay between these two points."
                    )
            elif strategy == "Iron Butterfly":
                if len(formatted_breakeven_points) == 2:
                    lower_bep, upper_bep = formatted_breakeven_points  # Unpack the two break-even points
                    strategy_message = (
                        f"The break-even points for this strategy are: {lower_bep} and {upper_bep}. "
                        f"If the stock price falls below {lower_bep} or rises above {upper_bep}, you will start losing money. "
                        f"To maximize profit, the stock price should stay between these two points."
                    )
            elif strategy == "Collar":
                strategy_message = (
                    f"The break-even points for this strategy is {', '.join(map(str, formatted_breakeven_points))}. "
                    f" If the stock price closes above {', '.join(map(str, formatted_breakeven_points))} at the time of expiry you will make profit, and if it falls below the breakeven point you will make losses."
                )
            # Footer at the bottom with modern design
            st.sidebar.markdown(
                """
                <style>
                    /* Sidebar Footer Styles */
                    .footer {
                        position: absolute;
                        top: 310px;
                        width: 100%;
                        text-align: left;
                        font-family: 'Georgia', sans-serif;
                        font-size: 12px;
                        color: #555;
                    }

                    /* Footer Text */
                    .footer p {
                        margin: 0 0 5px 0;
                        font-weight: bold;
                    }

                    /* Icons */
                    .footer img {
                        width: 25px;
                        margin: 0 5px;
                        transition: transform 0.3s ease, filter 0.3s ease;
                    }

                    /* Icon Hover Effect */
                    .footer img:hover {
                        transform: scale(1.2);
                        filter: drop-shadow(0px 0px 5px #0072b1);
                    }
                </style>
                <div class="footer">
                    <p>Created by Chinmay Yadav</p>
                    <a href="mailto:Chinmay.yadav@uconn.edu" target="_blank">
                        <img src="https://img.icons8.com/fluency/48/000000/email.png" />
                    </a>
                    <a href="https://www.linkedin.com/in/ADoAAD8A20QBPeneBVvTzmY8PSESp5D0uJPuMkk" target="_blank">
                        <img src="https://img.icons8.com/fluency/48/000000/linkedin.png" />
                    </a>
                </div>
                """,
                unsafe_allow_html=True
            )
            # Display the strategy-specific message
            st.markdown(
                f"""
                <div style="background-color: #f9f9f9; padding: 10px; border-radius: 5px; border: 1px solid #ddd;">
                    <span style="font-size: 16px; color: #333;">
                        <b>Break-Even Points:</b> {strategy_message}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="background-color: #fff4e5; padding: 10px; border-radius: 5px; border: 1px solid #f5cda0;">
                    <span style="font-size: 16px; color: #cc6600;">
                        <b>Break-Even Points:</b> Not applicable for this strategy.
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )




