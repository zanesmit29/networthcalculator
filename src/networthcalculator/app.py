import streamlit as st
from db_utils import create_table, get_db_connection, ASSET_CATEGORIES, LIABILITY_CATEGORIES, CASHFLOW_CATEGORIES
import pandas as pd
from datetime import date
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def main():
    # Ensure the database table is created
    create_table()
    # Set up the Streamlit app configuration
    st.set_page_config(page_title="Net Worth Tracker", page_icon= "📈", layout="wide")
    st.title("🏦 Personal Net Worth Tracker 🏦")
    st.write("Track your assets liabilities and net worth over time with this comprehensive dashboard.")

    #Make a sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Select a page:", [
        "Dashboard", 
        "Add Assets", 
        "Add Liabilities", 
        "Add Cash Flow",
        "View/Edit Data", 
        "Analytics", 
        "Export Data"
        ])
    page_name = page
    if page_name == "Dashboard":
        dashboard()
        
    elif page_name == "Add Assets":
        add_assets()
        
    elif page_name == "Add Liabilities":
        add_liabilities()
        
    elif  page_name == "Add Cash Flow":
        add_cash_flow()
        
    elif page_name == "View/Edit Data":
        view_edit_data()
        
    elif page_name == "Analytics":
        analytics()
        
    elif page_name == "Export Data":
        export_data()
        
def add_goal(net_worth):
    
    with st.expander("Set a New Goal", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            
            goal_type = st.selectbox(
                "Select goal type:",
                ["Asset", "Liability", "Cash Flow", "Net Worth"],
                key="goal_type"
            )
        with col2:
            
            if goal_type == "Asset":
                goal_subcategory = st.selectbox("Select asset subcategory:", ASSET_CATEGORIES, key="goal_asset_subcat")
            elif goal_type == "Liability":
                goal_subcategory = st.selectbox("Select liability subcategory:", LIABILITY_CATEGORIES, key="goal_liab_subcat")
            elif goal_type == "Cash Flow":
                goal_subcategory = st.selectbox("Select cash flow subcategory:", CASHFLOW_CATEGORIES, key="goal_cashflow_subcat")
            else:
                goal_subcategory = "Net Worth"
        goal_amount = st.number_input("Enter your financial goal (€):", key="goal_amount")

        #Check how many goals are already set
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM goals")
        num_goals = cursor.fetchone()[0]
        
        if st.button("Set Goal"):
            # Get the current progress towards the goal through the database
            if num_goals <= 2:  # Allow up to 3 goals
                if goal_type == "Asset":
                    cursor.execute("SELECT SUM(value) FROM assets_liabilities WHERE category = 'assets' AND subcategory = ?", (goal_subcategory,))
                    progress = goal_amount - (cursor.fetchone()[0] or 0.0)
                elif goal_type == "Liability":
                    cursor.execute("SELECT SUM(value) FROM assets_liabilities WHERE category = 'liabilities' AND subcategory = ?", (goal_subcategory,))
                    progress = goal_amount + (cursor.fetchone()[0] or 0.0)
                elif goal_type == "Cash Flow":
                    cursor.execute("SELECT SUM(value) FROM assets_liabilities WHERE category = 'cash flow' AND subcategory = ?", (goal_subcategory,))
                    progress = goal_amount - (cursor.fetchone()[0] or 0.0)
                else:  # Net Worth
                    progress = net_worth - goal_amount

                # Here you would implement the logic to save the goal to the database
                cursor.execute('''
                    INSERT INTO goals (goal_type, goal_subcategory, goal_amount, progress)
                    VALUES (?, ?, ?, ?)
                ''', (goal_type, goal_subcategory, goal_amount, progress))
                conn.commit()
                conn.close()
                st.success("Goal set successfully!")
                st.rerun()  # Refresh the page to show the new goal
                
                return 
            else:
                st.error("You can only set up to 3 goals at a time. Please complete or delete an existing goal before setting a new one.")
                return 

def delete_goal(goal_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    conn.commit()
    conn.close()
    st.success("Goal deleted successfully!")
    st.rerun()  # Refresh the page to show the updated goals

def dashboard():
    st.header("🪙 Net Worth Dashboard")

    conn = get_db_connection()
    cursor = conn.cursor()
    # Get the total assets, liabilities, and cash flow
    cursor.execute("SELECT SUM(value) FROM assets_liabilities WHERE category = 'assets'")
    total_assets = cursor.fetchone()[0] or 0.0
    cursor.execute("SELECT SUM(value) FROM assets_liabilities WHERE category = 'liabilities'")
    total_liabilities = cursor.fetchone()[0] or 0.0
    cursor.execute("SELECT SUM(value) FROM assets_liabilities WHERE category = 'cash flow'")
    total_cash_flow = cursor.fetchone()[0] or 0.0
    # Calculate net worth
    net_worth = total_assets - total_liabilities
    # Display the totals
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Assets", f"€{total_assets:,.2f}")
    with col2:
        st.metric("Total Liabilities", f"€{total_liabilities:,.2f}")
    with col3:
        st.metric("Total Cash Flow", f"€{total_cash_flow:,.2f}")
    with col4:
        st.metric("Net Worth", f"€{net_worth:,.2f}")
    
    

    # Custom goals and progress tracking
    st.subheader("🎯 Goals and Progress Tracking")
    st.write("Set your financial goals and track your progress towards achieving them.")

    # Load existing goals from the database and display them
    cursor.execute("SELECT id, goal_type, goal_subcategory, goal_amount, progress FROM goals")
    goals = cursor.fetchall()
    if goals:
        for goal in goals:
            rowid, goal_type, goal_subcategory, goal_amount, progress = goal
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.write(f"**Goal:** {goal_amount}")
            col2.write(f"**Type:** {goal_type}")
            col3.write(f"**Subcategory:** {goal_subcategory}")
            col4.write(f"**Amount Needed:** €{progress:,.2f}")
            if col5.button("🗑️", key=f"delete_goal_{rowid}"):
                delete_goal(rowid)
    else:
        st.info("No goals set yet.")
    conn.close()

    # Add a new goal
    add_goal(net_worth)       

    # Display the net worth and cash flow over time
    st.subheader("📈 Net Worth and Cash Flow Over Time")
    # Load data from the database
    conn = get_db_connection()
    history_df = pd.read_sql_query(
        """
        SELECT 
            assets_liabilities_history.date AS history_date,
            assets_liabilities_history.asset_liability_id,
            assets_liabilities_history.difference,
            assets_liabilities_history.old_value,
            assets_liabilities.category
        FROM assets_liabilities_history
        LEFT JOIN assets_liabilities
            ON assets_liabilities_history.asset_liability_id = assets_liabilities.rowid
        ORDER BY assets_liabilities_history.date
        """,
        conn
    )
    conn.close()

    history_df['history_date'] = pd.to_datetime(history_df['history_date'])

    # Get the first old_value for each asset_liability_id
    initials = (
        history_df.sort_values('history_date')
        .groupby('asset_liability_id')
        .first()
        .reset_index()
    )

    # Prepare initial entries DataFrame
    initial_entries = initials[['asset_liability_id', 'history_date', 'old_value', 'category']].copy()
    initial_entries = initial_entries.rename(columns={'old_value': 'difference'})
    initial_entries = initial_entries[['history_date', 'asset_liability_id', 'difference', 'category']]
    initial_entries = initial_entries[initial_entries['difference'].notnull()]

    # Only keep rows where old_value is not null
    initial_entries = initial_entries[initial_entries['difference'].notnull()]

    # Combine initial entries with history (excluding the old_value column)
    history_for_sum = history_df[['history_date', 'asset_liability_id', 'difference', 'category']]
    full_history = pd.concat([initial_entries, history_for_sum], ignore_index=True)

    # Group by date and category, sum differences
    agg_df = full_history.groupby(['history_date', 'category'])['difference'].sum().reset_index()

    # Pivot to get assets and liabilities columns
    pivot_df = agg_df.pivot(index='history_date', columns='category', values='difference').fillna(0)
    # Cumulative sum to get running totals
    pivot_df = pivot_df.sort_index().cumsum()

    pivot_df['Net Worth'] = pivot_df.get('assets', 0) - pivot_df.get('liabilities', 0)
    pivot_df['Cash Flow'] = pivot_df.get('cash flow', 0) if 'cash flow' in pivot_df else 0

    pivot_df.index = pd.to_datetime(pivot_df.index)
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Net Worth on primary y-axis
    fig.add_trace(
        go.Scatter(
            x=pivot_df.index,
            y=pivot_df['Net Worth'],
            mode='lines+markers',
            name='Net Worth'
        ),
        secondary_y=False,
    )

    # Cash Flow on secondary y-axis
    fig.add_trace(
        go.Scatter(
            x=pivot_df.index,
            y=pivot_df['Cash Flow'],
            mode='lines+markers',
            name='Cash Flow'
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title="Net Worth and Cash Flow Over Time",
        xaxis_title="Date",
        template="plotly_white",
        legend_title="Metric"
    )
    fig.update_yaxes(title_text="Net Worth (€)", secondary_y=False)
    fig.update_yaxes(title_text="Cash Flow (€)", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)


    # Pie charts for the distribution of assets, liabilities, and cash flow
    st.subheader("📊 Distribution of Assets, Liabilities, and Cash Flow")
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM assets_liabilities", conn)
    conn.close()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Assets Distribution")
        assets_df = df[df['category'] == 'assets']
        if not assets_df.empty:
            assets_pie = assets_df.groupby('subcategory')['value'].sum().reset_index()
            fig_assets = go.Figure(data=[go.Pie(labels=assets_pie['subcategory'], values=assets_pie['value'], hole=0.3)])
            fig_assets.update_layout(title_text="Assets Distribution")
            st.plotly_chart(fig_assets, use_container_width=True)
        else:
            st.write("No assets data available.")
    with col2:
        st.subheader("Liabilities Distribution")
        liabilities_df = df[df['category'] == 'liabilities']
        if not liabilities_df.empty:
            liabilities_pie = liabilities_df.groupby('subcategory')['value'].sum().reset_index()
            fig_liabilities = go.Figure(data=[go.Pie(labels=liabilities_pie['subcategory'], values=liabilities_pie['value'], hole=0.3)])
            fig_liabilities.update_layout(title_text="Liabilities Distribution")
            st.plotly_chart(fig_liabilities, use_container_width=True)
        else:
            st.write("No liabilities data available.")
    with col3:
        st.subheader("Cash Flow Distribution")
        cash_flow_df = df[df['category'] == 'cash flow']
        if not cash_flow_df.empty:
            cash_flow_pie = cash_flow_df.groupby('subcategory')['value'].sum().reset_index()
            fig_cash_flow = go.Figure(data=[go.Pie(labels=cash_flow_pie['subcategory'], values=cash_flow_pie['value'], hole=0.3)])
            fig_cash_flow.update_layout(title_text="Cash Flow Distribution")
            st.plotly_chart(fig_cash_flow, use_container_width=True)
        else:
            st.write("No cash flow data available.")
    


def add_assets():
    st.header("➕ Add New Assets")

    #Input fields for asset details
    date = st.date_input("Date")
    category = "assets"
    subcategory = st.selectbox("Category", ASSET_CATEGORIES)
    value = st.number_input("Value", min_value=0.0, step=0.01)
    description = st.text_input("Description")
    if st.button("Add Asset"):
        # Here you would implement the logic to add the asset to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO assets_liabilities (date, category, subcategory, description, value)
            VALUES (?, ?, ?, ?, ?)
        ''', (date.isoformat(), category, subcategory, description, value))
        # Get the last inserted row ID
        asset_id = cursor.lastrowid
        # Insert into assets_liabilities_history
        cursor.execute(
            "INSERT INTO assets_liabilities_history (asset_liability_id, date, old_value, new_value, difference, description) VALUES (?, ?, ?, ?, ?, ?)",
            (asset_id, date.isoformat(), 0, value, value, description)
        )
        conn.commit()
        conn.close()
        st.success("Asset added successfully!")

def add_liabilities():
    st.header("➕ Add New Liabilities")

    #Input fields for liability details
    date = st.date_input("Date")
    category = "liabilities"
    subcategory = st.selectbox("Category", LIABILITY_CATEGORIES)
    value = st.number_input("Value", min_value=0.0, step=0.01)
    description = st.text_input("Description")
    if st.button("Add Liability"):
        # Here you would implement the logic to add the liability to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO assets_liabilities (date, category, subcategory, description, value)
            VALUES (?, ?, ?, ?, ?)
        ''', (date.isoformat(), category, subcategory, description, value))
        asset_id = cursor.lastrowid
        # Insert into assets_liabilities_history
        cursor.execute(
            "INSERT INTO assets_liabilities_history (asset_liability_id, date, old_value, new_value, difference, description) VALUES (?, ?, ?, ?, ?, ?)",
            (asset_id, date.isoformat(), 0, value, value, description)
        )
        conn.commit()
        conn.close()
        st.success("Liability added successfully!")

def add_cash_flow():
    st.header("➕ Add Cash Flow")

    #Input fields for cash flow details
    date = st.date_input("Date")
    category = "cash flow"
    subcategory = st.selectbox("Category", CASHFLOW_CATEGORIES)
    value = st.number_input("Value", min_value=0.0, step=0.01)
    description = st.text_input("Description")
    if st.button("Add Cash Flow"):
        # Here you would implement the logic to add the cash flow to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO assets_liabilities (date, category, subcategory, description, value)
            VALUES (?, ?, ?, ?, ?)
        ''', (date.isoformat(), category, subcategory, description, value))
        asset_id = cursor.lastrowid
        # Insert into assets_liabilities_history
        cursor.execute(
            "INSERT INTO assets_liabilities_history (asset_liability_id, date, old_value, new_value, difference, description) VALUES (?, ?, ?, ?, ?, ?)",
            (asset_id, date.isoformat(), 0, value, value, description)
        )
        conn.commit()
        conn.close()
        st.success("Cash Flow added successfully!")



def delete_entry(rowid):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Delete history first
    cursor.execute("DELETE FROM assets_liabilities_history WHERE asset_liability_id = ?", (rowid,))
    # Then delete the main entry
    cursor.execute("DELETE FROM assets_liabilities WHERE rowid = ?", (rowid,))
    conn.commit()
    conn.close()

def update_entry(rowid, new_value, description, new_date):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Get the old value
    cursor.execute("SELECT value, date FROM assets_liabilities WHERE rowid = ?", (rowid,))
    result = cursor.fetchone()
    if result:
        old_value = result[0]
    else:
        old_value = 0  # or handle as needed
    diff = new_value - old_value

    # Update the main table
    cursor.execute(
        "UPDATE assets_liabilities SET value = ?, description = ?, date = ? WHERE rowid = ?",
        (new_value, description, new_date, rowid)
    )

    # Insert into history table
    cursor.execute(
        "INSERT INTO assets_liabilities_history (asset_liability_id, date, old_value, new_value, difference, description) VALUES (?, ?, ?, ?, ?, ?)",
        (rowid, new_date, old_value, new_value, diff, description)
    )

    conn.commit()
    conn.close()

def view_edit_data():
    st.header("📝 View & Edit Data")

    # Load data from the database
    conn = get_db_connection()
    cursor = conn.cursor()
    tabs = st.tabs(["Assets", "Liabilities", "Cash Flow"])

    with tabs[0]:
        st.header("Assets")
        cursor.execute("SELECT * FROM assets_liabilities WHERE category = 'assets'")
        assets = cursor.fetchall()
        for asset in assets:
            rowid, date, category, subcategory, description, value = asset
            col1, col2, col3 , col4, col5, col6= st.columns(6)
            col1.write(subcategory)  # subcategory
            col2.write(description)  # description
            col3.write(f"€{value:,.2f}")  # value
            col4.write(date)  # date
            
            if col5.button("✏️", key=f"update_asset_{rowid}"):
                st.session_state[f"expand_asset_{rowid}"] = not st.session_state.get(f"expand_asset_{rowid}", False)
            if st.session_state.get(f"expand_asset_{rowid}", False):
                with st.expander(f"Edit Asset {rowid}", expanded=True):
                    new_date = st.date_input("Date")
                    new_description = st.text_input("Description", value=description, key=f"desc_{rowid}")
                    new_value = st.number_input("Value", value=value, key=f"val_{rowid}")
                    save_col, cancel_col = st.columns(2)
                    if save_col.button("Save", key=f"save_asset_{rowid}"):
                        update_entry(rowid, new_value, new_description, new_date.isoformat())
                        st.session_state[f"expand_asset_{rowid}"] = False
                        st.success("Asset updated!")
                        st.rerun()
                    if cancel_col.button("Cancel", key=f"cancel_asset_{rowid}"):
                        st.session_state[f"expand_asset_{rowid}"] = False
                        st.rerun()

            if col6.button("🗑️", key=f"delete_asset_{rowid}"):
                delete_entry(rowid)
                st.success("Asset deleted!")
                st.rerun()
            

    with tabs[1]:
        st.header("Liabilities")
        cursor.execute("SELECT * FROM assets_liabilities WHERE category = 'liabilities'")
        liabilities = cursor.fetchall()
        for liability in liabilities:
            rowid, date, category, subcategory, description, value = liability
            col1, col2, col3 , col4, col5, col6= st.columns(6)
            col1.write(subcategory)  # subcategory
            col2.write(description)  # description
            col3.write(f"€{value:,.2f}")  # value
            col4.write(date)  # date
            if col5.button("✏️", key=f"update_liability_{rowid}"):
                st.session_state[f"expand_liability_{rowid}"] = not st.session_state.get(f"expand_liability_{rowid}", False)
            if st.session_state.get(f"expand_liability_{rowid}", False):
                with st.expander(f"Edit Liability {rowid}", expanded=True):
                    new_date = st.date_input("Date")
                    new_description = st.text_input("Description", value=description, key=f"desc_liability_{rowid}")
                    new_value = st.number_input("Value", value=value, key=f"val_liability_{rowid}")
                    save_col, cancel_col = st.columns(2)
                    if save_col.button("Save", key=f"save_liability_{rowid}"):
                        update_entry(rowid, new_value, new_description, new_date.isoformat())
                        st.session_state[f"expand_liability_{rowid}"] = False
                        st.success("Liability updated!")
                        st.rerun()
                    if cancel_col.button("Cancel", key=f"cancel_liability_{rowid}"):
                        st.session_state[f"expand_liability_{rowid}"] = False
                        st.rerun()
            if col6.button("🗑️", key=f"delete_liability_{rowid}"):
                delete_entry(rowid)
                st.success("Liability deleted!")
                st.rerun()
        
    with tabs[2]:
        st.header("Cash Flow")
        cursor.execute("SELECT * FROM assets_liabilities WHERE category = 'cash flow'")    
        cash_flow = cursor.fetchall()
        for flow in cash_flow:
            rowid, date, category, subcategory, description, value = flow
            col1, col2, col3 , col4, col5, col6= st.columns(6)
            col1.write(subcategory)  # subcategory
            col2.write(description)  # description
            col3.write(f"€{value:,.2f}")  # value
            col4.write(date)  # date    
            if col5.button("✏️", key=f"update_cash_flow_{rowid}"):
                st.session_state[f"expand_cash_flow_{rowid}"] = not st.session_state.get(f"expand_cash_flow_{rowid}", False)
            if st.session_state.get(f"expand_cash_flow_{rowid}", False):
                with st.expander(f"Edit Cash Flow {rowid}", expanded=True):
                    new_date = st.date_input("Date")
                    new_description = st.text_input("Description", value=description, key=f"desc_cash_flow_{rowid}")
                    new_value = st.number_input("Value", value=value, key=f"val_cash_flow_{rowid}")
                    save_col, cancel_col = st.columns(2)
                    if save_col.button("Save", key=f"save_cash_flow_{rowid}"):
                        update_entry(rowid, new_value, new_description, new_date)
                        st.session_state[f"expand_cash_flow_{rowid}"] = False
                        st.success("Cash Flow updated!")
                        st.rerun()
                    if cancel_col.button("Cancel", key=f"cancel_cash_flow_{rowid}"):
                        st.session_state[f"expand_cash_flow_{rowid}"] = False
                        st.rerun()
            if col6.button("🗑️", key=f"delete_cash_flow_{rowid}"):
                delete_entry(rowid)
                st.success("Cash Flow deleted!")
                st.rerun()
            

    conn.close()

    

def analytics():
    st.header("🔍 Advanced Analytics")
    
    # Make columns with number of assets, liabilities, and cash flow, average assets, liabilities
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM assets_liabilities WHERE category = 'assets'")
    num_assets = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM assets_liabilities WHERE category = 'liabilities'")
    num_liabilities = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM assets_liabilities WHERE category = 'cash flow'")
    num_cash_flow = cursor.fetchone()[0]
    cursor.execute("SELECT AVG(value) FROM assets_liabilities WHERE category = 'assets'")
    avg_assets = cursor.fetchone()[0] or 0.0
    cursor.execute("SELECT AVG(value) FROM assets_liabilities WHERE category = 'liabilities'")
    avg_liabilities = cursor.fetchone()[0] or 0.0

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Number of Assets", num_assets)
    with col2:
        st.metric("Number of Liabilities", num_liabilities)
    with col3:
        st.metric("Number of Cash Flow Entries", num_cash_flow)
    with col4:
        st.metric("Average Asset Value", f"€{avg_assets:,.2f}")
    with col5:
        st.metric("Average Liability Value", f"€{avg_liabilities:,.2f}")
    
    # Debt-to-Asset Ratio
    cursor.execute("SELECT SUM(value) FROM assets_liabilities WHERE category = 'liabilities'")
    total_liabilities = cursor.fetchone()[0] or 0.0
    cursor.execute("SELECT SUM(value) FROM assets_liabilities WHERE category = 'assets'")
    total_assets = cursor.fetchone()[0] or 0.0
    if total_assets > 0:
        debt_to_asset_ratio = total_liabilities / total_assets
    else:
        debt_to_asset_ratio = 0.0
    
    st.subheader("⚖️ Debt-to-Asset Ratio")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Liabilities", f"€{total_liabilities:,.2f}")
        st.metric("Total Assets", f"€{total_assets:,.2f}")
        st.metric("Debt-to-Asset Ratio", f"{debt_to_asset_ratio:.2%}")
    with col2:
        # Visualize the debt-to-asset ratio with a pie chart
        fig = go.Figure(data=[go.Pie(labels=["Debt", "Assets"], values=[total_liabilities, total_assets], hole=0.3)])
        fig.update_layout(title_text="Debt-to-Asset Ratio", template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    
    # Monthly/Yearly trends
    st.subheader("📅 Monthly/Yearly Trends")
    cursor.execute("""
        SELECT strftime('%Y-%m', date) as month, category, SUM(value) as total_value
        FROM assets_liabilities
        GROUP BY month, category
    """)
    monthly_data = cursor.fetchall()

    if monthly_data:
        monthly_df = pd.DataFrame(monthly_data, columns=['month', 'category', 'total_value'])
        monthly_df['month'] = pd.to_datetime(monthly_df['month'])
        monthly_df.sort_values('month', inplace=True)
        # Pivot so each category is a column
        monthly_pivot = monthly_df.pivot(index='month', columns='category', values='total_value').fillna(0)

        fig = go.Figure()
        for cat in monthly_pivot.columns:
            fig.add_bar(x=monthly_pivot.index, y=monthly_pivot[cat], name=cat.capitalize())
        fig.update_layout(
            barmode='group',
            title_text="Monthly Trends by Category",
            xaxis_title="Month",
            yaxis_title="Value (€)",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- Yearly Trends ---
        cursor.execute("""
            SELECT strftime('%Y', date) as year, category, SUM(value) as total_value
            FROM assets_liabilities
            GROUP BY year, category
        """)
        yearly_data = cursor.fetchall()
        if yearly_data:
            yearly_df = pd.DataFrame(yearly_data, columns=['year', 'category', 'total_value'])
            yearly_df['year'] = pd.to_datetime(yearly_df['year'])
            yearly_df.sort_values('year', inplace=True)
            yearly_pivot = yearly_df.pivot(index='year', columns='category', values='total_value').fillna(0)

            fig_yearly = go.Figure()
            for cat in yearly_pivot.columns:
                fig_yearly.add_bar(x=yearly_pivot.index, y=yearly_pivot[cat], name=cat.capitalize())
            fig_yearly.update_layout(
                barmode='group',
                title_text="Yearly Trends by Category",
                xaxis_title="Year",
                yaxis_title="Value (€)",
                template="plotly_white"
            )
            st.plotly_chart(fig_yearly, use_container_width=True)
        else:
            st.write("No yearly data available.")
    else:
        st.write("No monthly data available.")

    # Trends in categories over time
    st.subheader("📊 Trends in Categories Over Time")
    cursor.execute("SELECT date, subcategory, SUM(value) FROM assets_liabilities GROUP BY date, subcategory")
    category_data = cursor.fetchall()
    if category_data:
        category_df = pd.DataFrame(category_data, columns=['date', 'subcategory', 'total_value'])
        category_df['date'] = pd.to_datetime(category_df['date'])
        category_df.set_index('date', inplace=True)
        category_pivot = category_df.pivot(columns='subcategory', values='total_value').fillna(0)
        fig_category = go.Figure()
        for category in category_pivot.columns:
            fig_category.add_trace(go.Scatter(x=category_pivot.index, y=category_pivot[category], mode='lines+markers', name=category))
            
        fig_category.update_layout(title_text="Trends in Categories Over Time", xaxis_title="Date", yaxis_title="Total Value (€)", template="plotly_white")
        st.plotly_chart(fig_category, use_container_width=True)
    else:
        st.write("No category data available.")
    
    
            







    # Largest increase/Decrease in asset/liability/cash flow over time
    # st.subheader("📈 Largest Increase/Decrease in Assets, Liabilities, and Cash Flow")
    # cursor.execute("SELECT date, category, subcategory, value FROM assets_liabilities ORDER BY date")
    

    



    st.subheader("🏆 Top Assets")
    cursor.execute("SELECT subcategory, SUM(value) as total_value FROM assets_liabilities WHERE category = 'assets' GROUP BY subcategory ORDER BY total_value DESC LIMIT 5")
    top_assets = cursor.fetchall()
    for asset in top_assets:
        subcategory, total_value = asset
        cursor.execute("SELECT COUNT(*) FROM assets_liabilities WHERE subcategory = ? AND category = 'assets'", (subcategory,))
        num_entries = cursor.fetchone()[0]
        col1, col2, col3 = st.columns(3)
        col1.write(subcategory)
        col2.write(f"Total accumalative: €{total_value:,.2f}")
        col3.write(f"Number of entries: {num_entries}")

    #st.subheader("🏦 Top Liabilities")
    st.subheader("💳 Top Liabilities")
    cursor.execute("SELECT subcategory, SUM(value) as total_value FROM assets_liabilities WHERE category = 'liabilities' GROUP BY subcategory ORDER BY total_value DESC LIMIT 5")
    top_liabilities = cursor.fetchall()
    for liability in top_liabilities:
        subcategory, total_value = liability
        cursor.execute("SELECT COUNT(*) FROM assets_liabilities WHERE subcategory = ? AND category = 'liabilities'", (subcategory,))
        num_entries = cursor.fetchone()[0]
        col1, col2, col3 = st.columns(3)
        col1.write(subcategory)
        col2.write(f"Total accumalative: €{total_value:,.2f}")
        col3.write(f"Number of entries: {num_entries}")

    st.subheader("💸 Top Cash Flow Categories")
    cursor.execute("SELECT subcategory, SUM(value) as total_value FROM assets_liabilities WHERE category = 'cash flow' GROUP BY subcategory ORDER BY total_value DESC LIMIT 5")
    top_cash_flow = cursor.fetchall()
    for cash_flow in top_cash_flow:
        subcategory, total_value = cash_flow
        cursor.execute("SELECT COUNT(*) FROM assets_liabilities WHERE subcategory = ? AND category = 'cash flow'", (subcategory,))
        num_entries = cursor.fetchone()[0]
        col1, col2, col3 = st.columns(3)
        col1.write(subcategory)
        col2.write(f"Total accumalative: €{total_value:,.2f}")
        col3.write(f"Number of entries: {num_entries}")
    
    # Recently added assets/liabilities/cash flow
    st.subheader("🕒 Recently Added Entries")
    cursor.execute("SELECT * FROM assets_liabilities ORDER BY date DESC LIMIT 10")
    recent_entries = cursor.fetchall()
    for entry in recent_entries:
        rowid, date, category, subcategory, description, value = entry
        col1, col2, col3, col4 = st.columns(4)
        col1.write(date)
        col2.write(subcategory)
        col3.write(description)
        col4.write(f"€{value:,.2f}")
    
    conn.close()
 

def export_data():
    st.header("📤 Export Data")
    st.write("Export your data to a CSV file for backup or analysis.")
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM assets_liabilities", conn)
    conn.close()
    if st.button("Export to CSV"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name='net_worth_data.csv',
            mime='text/csv'
        )
    st.write("You can also export your data to other formats like Excel or JSON.")
    if st.button("Export to Excel"):
        excel = df.to_excel(index=False)
        st.download_button(
            label="Download Excel",
            data=excel,
            file_name='net_worth_data.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    if st.button("Export to JSON"):
        json_data = df.to_json(orient='records')
        st.download_button(
            label="Download JSON",
            data=json_data,
            file_name='net_worth_data.json',
            mime='application/json'
        )
    

    
if __name__ == "__main__":
    main()