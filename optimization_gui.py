import streamlit as st
from data_model import load_warehouse_data_from_csv, save_warehouse_stock_to_csv
from stock_optimization import trigger_stock_optimization, display_warehouse_stock
from sales_stock_selection import trigger_stock_dispatch  # Assuming you put the dispatch code in a file called stock_dispatch.py

# Set page configuration to enable scrolling
st.set_page_config(page_title="Warehouse Stock Management", layout="wide", initial_sidebar_state="auto")

# Sidebar menu with buttons
st.sidebar.title("Navigation")
if "menu" not in st.session_state:
    st.session_state.menu = "Warehouse Stock Optimization"  # Set default menu

# Button for Warehouse Stock Optimization
if st.sidebar.button("Warehouse Stock Optimization"):
    st.session_state.menu = "Warehouse Stock Optimization"

# Button for Stock Dispatch Selection
if st.sidebar.button("Stock Dispatch Selection"):
    st.session_state.menu = "Stock Dispatch Selection"

# Load warehouse data from CSV
stock_file = "warehouse_stock.csv"
connection_file = "warehouse_mapping.csv"
stock_optimization_file = "optimized_warehouse_stock.csv"
stock_dispatch_file = "dispatched_warehouse_stock.csv"
warehouses = load_warehouse_data_from_csv(stock_file, connection_file)

# Function to display warehouse stock information in a table format
def display_stock_table(warehouses):
    stock_data = []
    for warehouse_code, warehouse in warehouses.items():
        for stock in warehouse.get_stock():
            stock_data.append({
                "Warehouse": warehouse_code,
                "Item Code": stock['item_code'],
                "Quantity": stock['quantity'],
                "Min Amount": stock['min_amount'],
                "Expiry Date": stock['expiry_date'],
            })
    st.table(stock_data)

# Page for Warehouse Stock Optimization
if st.session_state.menu == "Warehouse Stock Optimization":
    st.title("Warehouse Stock Optimization")

    # Section to display warehouse stock
    st.header("Current Warehouse Stock")
    if st.button("Refresh Stock Data"):
        warehouses = load_warehouse_data_from_csv(stock_file, connection_file)
    display_stock_table(warehouses)

    # Section to trigger stock optimization
    st.header("Trigger Stock Optimization")
    with st.form("stock_optimization_form"):
        target_warehouse = st.selectbox(
            "Select Target Warehouse",
            options=list(warehouses.keys()),
            format_func=lambda x: f"Warehouse {x}",
        )

        required_stock_input = st.text_area(
            "Enter Required Stock (JSON format, e.g., {\"N007\": 70, \"H014\": 40})",
            value="{}",
        )

        submitted = st.form_submit_button("Optimize Stock")

        if submitted:
            try:
                output_text = ""
                required_stock = eval(required_stock_input)  # Safely parse JSON
                with st.spinner("Optimizing stock..."):
                    output_text = trigger_stock_optimization(target_warehouse, required_stock)

                st.success(f"Stock optimization completed for warehouse {target_warehouse}.")

                # Display detailed output
                st.text(output_text)

                # Refresh warehouses after optimization
                warehouses = load_warehouse_data_from_csv(stock_optimization_file, connection_file)
                st.header("Updated Warehouse Stock")
                display_stock_table(warehouses)

            except Exception as e:
                st.error(f"Error: {e}")

# Page for Stock Dispatch Selection
elif st.session_state.menu == "Stock Dispatch Selection":
    st.title("Stock Dispatch Selection")

    # Section to display warehouse stock
    st.header("Current Warehouse Stock")
    if st.button("Refresh Stock Data"):
        warehouses = load_warehouse_data_from_csv(stock_file, connection_file)
    display_stock_table(warehouses)

    # Section to trigger stock dispatch
    st.header("Trigger Stock Dispatch")
    with st.form("stock_dispatch_form"):
        target_warehouse = st.selectbox(
            "Select Target Warehouse",
            options=list(warehouses.keys()),
            format_func=lambda x: f"Warehouse {x}",
        )

        required_stock_input = st.text_area(
            "Enter Required Stock to Dispatch (JSON format, e.g., {\"N007\": 70, \"H014\": 40})",
            value="{}",
        )

        submitted = st.form_submit_button("Dispatch Stock")

        if submitted:
            try:
                output_text = ""
                required_stock = eval(required_stock_input)  # Safely parse JSON
                with st.spinner("Dispatching stock..."):
                    output_text = trigger_stock_dispatch(target_warehouse, required_stock)

                st.success(f"Stock dispatch completed for warehouse {target_warehouse}.")

                # Display detailed output
                st.text(output_text)

                # Refresh warehouses after dispatch
                warehouses = load_warehouse_data_from_csv(stock_dispatch_file, connection_file)
                st.header("Updated Warehouse Stock")
                display_stock_table(warehouses)

            except Exception as e:
                st.error(f"Error: {e}")

# Footer
st.write("\n---\nBuilt with Streamlit")
