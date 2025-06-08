import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------ SETUP ------------------------
st.set_page_config(page_title="Sales Insight Dashboard", layout="wide")  # for setting the webpage title and layout 
st.title("\U0001F4CA Sales Insight Dashboard") # adding a bar chart emoji before sales insight dashboard

# Define alias dictionary for each key cloumn type,helping code auto-detect columns even if they're named differently
COLUMN_ALIASES = {
    "date": ["date", "orderdate", "saledate", "transactiondate", "dateofsale"],
    "revenue": ["revenue", "totalsales", "salesamount", "amount", "generated", "revenuegenerated"],
    "units": ["units", "quantity", "unitssold", "quantitysold"],
    "product": ["product", "item", "productname"],
    "region": ["region", "zone", "area", "saleszone"],
    "category": ["category", "department", "segment", "productcategory"]
}


def detect_column(column_type, df_columns): #defines a function which calls two arguments: column_type-->(string representing type of column youre trying to detect) and df_columns-->list of column names (from Dataframe)
    aliases = COLUMN_ALIASES.get(column_type, [])#looks up list of possible alternative name for given column_type from dictionary COLUMN_ALIAS,and if not found in dictionary ,it defaults to an empty list[]
    for col in df_columns: # starts loop to iterate through each column name in df_columns list
        col_norm = col.lower().replace("_", "").replace(" ", "")#normalize the column name to matching easier,converts it to lowercase and removes _and " "
        if any(alias in col_norm for alias in aliases):#Checks if any of the aliases appear as substrings in the normalized column name,any(...) returns True if at least one alias is found inside col_norm.
            return col#if a match found , returns the original column name 
    return None#if no matching column is found after checking all of them , the fucntion returns None

uploaded_file = st.file_uploader("\U0001F4C1 Upload your sales CSV file", type=["csv"])#allows users to upload a .csv file 

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)#if  afile is uploaded , read it into a DataFrame df 

    # COLUMN DETECTION-->uses the above function to find the relevant columnsfor dat,revenue,units,product,region,category 
    date_col = detect_column("date", df.columns)
    revenue_col = detect_column("revenue", df.columns)
    units_col = detect_column("units", df.columns)
    product_col = detect_column("product", df.columns)
    region_col = detect_column("region", df.columns)
    category_col = detect_column("category", df.columns)

    # Fallback to manual selection-->if autodetection fails ,shows dropdown for user to manually pick the correct column
    if not date_col:
        date_col = st.selectbox("❓ Please select the Date column", df.columns)
    if not revenue_col:
        revenue_col = st.selectbox("❓ Please select the Revenue column", df.columns)
    if not units_col:
        units_col = st.selectbox("❓ Please select the Units Sold column", df.columns)
    if not product_col:
        product_col = st.selectbox("❓ Please select the Product column", df.columns)

    # Convert detected columns to appropriate types
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df[revenue_col] = pd.to_numeric(df[revenue_col], errors='coerce')
    df[units_col] = pd.to_numeric(df[units_col], errors='coerce')

    # ------------------------ SIDEBAR FILTERS ------------------------
    st.sidebar.header("\U0001F50D Filter Data")

    date_range = None
    if pd.notnull(df[date_col].min()) and pd.notnull(df[date_col].max()):
        date_range = st.sidebar.date_input("Select Date Range", [df[date_col].min(), df[date_col].max()])

    regions = st.sidebar.multiselect("Select Region(s)", options=df[region_col].dropna().unique() if region_col else [], default=df[region_col].dropna().unique() if region_col else []) if region_col else None

    categories = st.sidebar.multiselect("Select Category(s)", options=df[category_col].dropna().unique() if category_col else [], default=df[category_col].dropna().unique() if category_col else []) if category_col else None

    # ------------------------ FILTERING ------------------------
    mask = pd.Series(True, index=df.index)

    if date_range and len(date_range) == 2:
        mask &= (df[date_col] >= pd.to_datetime(date_range[0])) & (df[date_col] <= pd.to_datetime(date_range[1]))
    if region_col and regions:
        mask &= df[region_col].isin(regions)
    if category_col and categories:
        mask &= df[category_col].isin(categories)

    filtered_df = df[mask]

    # ------------------------ METRICS ------------------------
    if filtered_df.empty:
        st.warning("⚠️ No data matches the selected filters.")
    else:
        st.markdown("### \U0001F522 Key Metrics")
        col1, col2, col3 = st.columns(3)

        total_revenue = filtered_df[revenue_col].sum()
        total_units = filtered_df[units_col].sum()
        try:
            top_product = filtered_df.groupby(product_col)[revenue_col].sum().idxmax()
        except:
            top_product = "N/A"

        col1.metric("\U0001F4B0 Total Revenue", f"${total_revenue:,.2f}")
        col2.metric("\U0001F4E6 Total Units Sold", int(total_units))
        col3.metric("\U0001F3C6 Top Product", top_product)

        st.divider()

        # ------------------------ CHARTS ------------------------
        st.markdown("### \U0001F4C8 Revenue Over Time")
        revenue_by_date = filtered_df.groupby(date_col)[revenue_col].sum().reset_index()
        fig1 = px.line(revenue_by_date, x=date_col, y=revenue_col, title="Revenue Over Time")
        st.plotly_chart(fig1, use_container_width=True)

        st.markdown("### \U0001F4CA Top 5 Products by Revenue")
        top_products = filtered_df.groupby(product_col)[revenue_col].sum().nlargest(5).reset_index()
        fig2 = px.bar(top_products, x=product_col, y=revenue_col, color=product_col, title="Top 5 Products")
        st.plotly_chart(fig2, use_container_width=True)

        if category_col:
            st.markdown("### \U0001F967 Sales by Category")
            cat_sales = filtered_df.groupby(category_col)[revenue_col].sum().reset_index()
            fig3 = px.pie(cat_sales, values=revenue_col, names=category_col, title="Sales Distribution by Category")
            st.plotly_chart(fig3, use_container_width=True)

        st.divider()
        st.markdown("### \U0001F4C4 Filtered Data Preview")
        st.dataframe(filtered_df)

        st.download_button(
            label="⬇️ Download Filtered Data as CSV",
            data=filtered_df.to_csv(index=False).encode('utf-8'),
            file_name='filtered_sales_data.csv',
            mime='text/csv'
        )

else:
    st.info("\U0001F4CC Upload a sales CSV file to begin.")
