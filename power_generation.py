import streamlit as st
import pandas as pd
from io import BytesIO
import plotly.express as px

# --- Basic Authentication ---
USER_CREDENTIALS = {
    "admin": "password123",
    "user1": "mypassword",
}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def login():
    st.title("Login to Access the Dashboard")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state["authenticated"] = True
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password!")

if not st.session_state["authenticated"]:
    login()
    st.stop()

# --- Main App ---
dataset_name = "Power Generation"

@st.cache_data
def load_data_preview(file_path):
    try:
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, nrows=100, engine='openpyxl')
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding="utf-8", nrows=100)
        else:
            return None
        return df
    except FileNotFoundError:
        st.warning(f"File not found: {file_path}. Upload it below if missing.")
        return None
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def load_full_data(file_path, sheet, skip_row):
    try:
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, engine='openpyxl')
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding="utf-8")
        elif file_path.endswith("Out.xlsx"):
            df = pd.read_excel(file_path, engine='openpyxl', sheet_name=sheet, skiprows=skip_row)
        else:
            return None
        return df
    except FileNotFoundError:
        st.warning(f"File not found: {file_path}. Upload it below if missing.")
        return None
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def filter_by_year(df, filter_columns, start_year, end_year):
    year_columns = [col for col in df.columns if str(col).isdigit()]
    year_columns = sorted(year_columns, key=int)
    selected_years = [year for year in year_columns if start_year <= int(year) <= end_year]
    return df[filter_columns + selected_years]

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

file_path = "Power Sector.xlsx"
milestone_image1 = 'power_sector_s1.png'
df_preview = load_data_preview(file_path)

df_preview.drop(columns=[], inplace=True)
if df_preview is not None:
    st.write("### Key Milestone for Power generation")
    st.image(milestone_image1)
    df_full = load_full_data(file_path, None, None)
    df_full.drop(columns=[], inplace=True)
    
    st.write("### Filter Data")
    filters = {}
    filter_columns = ["Scenario", "Metric", "Unit"]
    cols = st.columns(len(filter_columns))
    selected_values = {}
    
    for i, col in enumerate(filter_columns):
        if col in df_full.columns:
            options = df_full[col].astype(str).unique().tolist()
            selected_values[col] = cols[i].multiselect(f"{col}", options, key=f"{col}")
    
    for col, values in selected_values.items():
        if values:
            df_full = df_full[df_full[col].astype(str).str.lower().isin([v.lower() for v in values])]
    
    year_columns = sorted([str(col) for col in df_full.columns if str(col).isdigit()], key=int)
    start_year = st.selectbox("Select Start Year:", options=year_columns, index=0, key=f"start_year_{dataset_name}")
    end_year = st.selectbox("Select End Year:", options=year_columns, index=len(year_columns)-1, key=f"end_year_{dataset_name}")
    
    if int(end_year) < int(start_year):
        st.error("End Year must be greater than or equal to Start Year.")
        end_year = start_year
    
    df_full = filter_by_year(df_full, filter_columns, int(start_year), int(end_year))
    
    if st.button("Apply Filters", key=f"apply_filters_{dataset_name}"):
        st.write(f"### Filtered Data {dataset_name}")
        st.dataframe(df_full.head(100), hide_index=True)
        excel_data = to_excel(df_full)
        st.download_button(
            label="Download Excel",
            data=excel_data,
            file_name=f"{dataset_name}_filtered_data.xlsx",
            mime="application/vnd.ms-excel",
            key=f"download_button_{dataset_name}"
        )
    
        df_melted = df_full.melt(id_vars=filter_columns, value_vars=[str(year) for year in range(2020, 2051, 5)], var_name="Year", value_name="Value")
        median_values = df_melted.groupby('Year')['Value'].median().reset_index()
        median_values['Scenario'] = 'Median - ALL'
        df_combined = pd.concat([df_melted, median_values])
    
        unit = df_combined["Unit"].unique()[0] if df_combined["Unit"].nunique() == 1 else 'Unit (Mixed)'
        metric_name = df_combined["Metric"].unique()[0] if df_combined["Metric"].nunique() == 1 else "Multiple Metric"
    
        fig = px.line(df_combined, x="Year", y="Value", color="Scenario", title=metric_name, labels={"Value": unit, "Year": "Year", "Scenario": "Scenario"}, markers=True)
        fig.update_traces(line=dict(color="black", width=4), selector=dict(name="Median - ALL"))
        fig.update_layout(height=600, width=1200)
        st.plotly_chart(fig)

if st.button("Logout"):
    st.session_state["authenticated"] = False
    st.experimental_rerun()
