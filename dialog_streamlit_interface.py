import streamlit as st
from streamlit_chat import message
from dialog_orchestrator_integration import DialogOrchestrator
import yfinance as yf
import pandas as pd

# Page configuration
st.set_page_config(page_title="SuperEzio Dialog Cockpit", layout="wide")

# --- Initialization ---
# Initialize the orchestrator and message history in session state
if 'orchestrator' not in st.session_state:
    # This will run only once per session
    st.session_state['orchestrator'] = DialogOrchestrator()
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {"role": "assistant", "content": "Welcome to the SuperEzio Dialog Cockpit! How can I assist you today?"}
    ]

# Default watchlist from README
WATCHLIST = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX']

# --- Helper functions ---
@st.cache_data(ttl=300) # Cache for 5 minutes
def get_watchlist_data(symbols: list) -> pd.DataFrame:
    """Fetches real-time data for a list of symbols."""
    data = []
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if not hist.empty:
                price = hist['Close'][-1]
                prev_close = hist['Close'][-2]
                change = price - prev_close
                change_pct = (change / prev_close) * 100
                data.append({
                    "Symbol": symbol,
                    "Price": f"${price:,.2f}",
                    "Change": f"{change:,.2f}",
                    "% Change": f"{change_pct:.2f}%"
                })
        except Exception as e:
            print(f"Error fetching {symbol} for watchlist: {e}")
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)

def handle_user_input():
    """Processes user input from session state, gets response, and updates history."""
    user_input = st.session_state.user_input
    if user_input:
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Get assistant response
        orchestrator = st.session_state.orchestrator
        assistant_response = orchestrator.handle_message(user_input)

        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

        # Clear the input box
        st.session_state.user_input = ""

# --- UI Layout ---

# Sidebar for chat
with st.sidebar:
    st.title("🤖 SuperEzio Dialog Cockpit")
    st.markdown("---")

    # User input text box at the top of the sidebar
    st.text_input(
        "Your message:",
        key="user_input",
        on_change=handle_user_input,
        placeholder="Analyze AAPL..."
    )

    st.markdown("---")
    st.subheader("Conversation")
    # Chat history
    for i, msg in enumerate(reversed(st.session_state.messages)): # Show newest first
        message(msg["content"], is_user=(msg["role"] == "user"), key=f"chat_{i}")


# Main dashboard area
st.title("📊 Platinum Trading Dashboard")
st.markdown("Welcome to your integrated trading dashboard. Use the chat on the left to interact with your 8 Platinum Analysts.")
st.markdown("---")

# Watchlist display
st.subheader("Market Watchlist")
watchlist_data = get_watchlist_data(WATCHLIST)

# Style the dataframe
if not watchlist_data.empty:
    def style_change(val):
        color = 'white' # Default color
        if isinstance(val, str):
            # Remove currency and percentage signs for numeric conversion
            numeric_val_str = val.replace('$', '').replace('%', '')
            try:
                numeric_val = float(numeric_val_str)
                if numeric_val > 0:
                    color = 'lightgreen'
                elif numeric_val < 0:
                    color = 'lightcoral'
            except ValueError:
                pass # Not a numeric value
        return f'color: {color}'

    st.dataframe(
        watchlist_data.style.applymap(style_change, subset=['Change', '% Change']),
        use_container_width=True
    )
else:
    st.warning("Could not fetch watchlist data. Please check your connection or the stock symbols.")


# Display latest assistant response in the main panel
if len(st.session_state.messages) > 1:
    st.markdown("---")
    st.subheader("Assistant's Latest Response")
    # The last message is the newest one
    latest_response = st.session_state.messages[-1]['content']
    st.markdown(f"> {latest_response.replace(chr(10), chr(10) + '> ')}") # Blockquote style
