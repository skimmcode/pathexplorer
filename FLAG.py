import streamlit as st
import pandas as pd
from io import BytesIO
import plotly.express as px

dataset_name = "FLAG"

# Function to load data preview (first 100 rows)
@st.cache_data
def load_data_preview(file_path):
    try:
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, nrows=100, engine='openpyxl',)
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

# Function to load full dataset

def load_full_data(file_path,sheet, skip_row):
    try:
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, engine='openpyxl')
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding="utf-8")
        elif file_path.endswith("Out.xlsx"):
            df = pd.read_excel(file_path, engine='openpyxl',sheet_name=sheet, skiprows=skip_row)
        else:
            return None
        return df
    except FileNotFoundError:
        st.warning(f"File not found: {file_path}. Upload it below if missing.")
        return None
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

# Function to filter data
def filter_data(df, filters):
    for col, value in filters.items():
        if value and col in df.columns:
            df = df[df[col].astype(str).str.contains(value, case=False, na=False)]
    return df

# Function to filter based on year range (specific to Dataset 1)
def filter_by_year(df, filter_columns, start_year, end_year):
    year_columns = [(col) for col in df_full.columns if str(col).isdigit()]
    year_columns = sorted(year_columns, key=int)
    selected_years = [year for year in year_columns if start_year <= int(year) <= end_year]
    return df[filter_columns + selected_years]

# Function to convert DataFrame to Excel for download
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    processed_data = output.getvalue()
    return processed_data
    
#st.subheader(f"View and Filter {dataset_name}")

               
# Load data preview (first 1000 rows only)
file_path = "FLAG.xlsx"
milestone_image1 = 'flag_sector_s1.png'
remove_cols = []
filter_columns = ["Commodity", "Region", "Unit"]
apply_year_filter = False

#st.write(remove_cols)
df_preview = load_data_preview(file_path)
df_preview.drop(columns=remove_cols,inplace=True)
if df_preview is not None:
    #st.write("### Data Preview")
    #st.dataframe(df_preview.head(), hide_index=True)

    # Milestone Image 
    st.write("### Key Milestones for Forestry, Land and Agriculture (FLAG) sector")
    st.image(milestone_image1)

    # Load full data for filtering purposes (without limiting to preview rows)
    df_full = load_full_data(file_path,None,None)
    df_full.drop(columns=remove_cols,inplace=True)


    # Filtering UI based on the full data columns (not preview)
    st.write("### Filter Data")
    filters = {}
    
    cols = st.columns(len(filter_columns))

    selected_values = {}  # For storing selected filter values
    
    # Update filter options dynamically based on previous selections
    # Update filter options dynamically based on previous selections
    
    for i, col in enumerate(filter_columns):
        if col in df_full.columns:
            options = df_full[col].astype(str).unique().tolist()
            selected_values[col] = cols[i].multiselect(f"{col}", options, key=f"{col}")

    # Apply the filter to the dataset
    for col, values in selected_values.items():
        if values:  # Ensure selections are made
            df_full = df_full[df_full[col].astype(str).str.lower().isin([v.lower() for v in values])]

    
    # Add year range filters for 'AllData' dataset or any dataset requiring year filtering
    if apply_year_filter:
        # Get list of years from the dataset
        year_columns = [str(col) for col in df_full.columns if str(col).isdigit()]
        year_columns = sorted(year_columns, key=int)  # Sort years in ascending order

        # Dropdown for Start Year
        start_year = st.selectbox(
            "Select Start Year:",
            options=year_columns,
            index=0,  # Default to the first year
            key=f"start_year_{dataset_name}"
        )

        # Dropdown for End Year
        end_year = st.selectbox(
            "Select End Year:",
            options=year_columns,
            index=len(year_columns)-1,  # Default to the last year
            key=f"end_year_{dataset_name}"
        )

        # Ensure end year is greater than or equal to start year
        if int(end_year) < int(start_year):
            st.error("End Year must be greater than or equal to Start Year.")
            end_year = start_year

        # Apply the year filter to the dataset
        df_full = filter_by_year(df_full, filter_columns, int(start_year), int(end_year))

    # Button to load full data and apply filters
    if st.button("Apply Filters", key=f"apply_filters_{dataset_name}"):
        # Show filtered data
        st.write(f"### Filtered Data {dataset_name}")
        st.dataframe(df_full.head(100), hide_index=True)

        # Button to download filtered data
        excel_data = to_excel(df_full)
        st.download_button(
            label="Download Excel",
            data=excel_data,
            file_name=f"{dataset_name}_filtered_data.xlsx",
            mime="application/vnd.ms-excel",
            key=f"download_button_{dataset_name}"  # Ensure unique key for download button
        )

        # Identify year columns (assuming they are numeric)
        year_columns = [(col) for col in df_full.columns if str(col).isdigit()]
        year_columns = sorted(year_columns, key=int)


        #st.write("### Visualizing Data")
        # Calculate the median line across all years
        #print(df_full.columns)
        df_full = df_full[~df_full.apply(lambda row: row.astype(str).str.contains('Median').any(), axis=1)]

        df_melted = df_full.melt(id_vars=filter_columns, 
                            value_vars=[(year) for year in range(2030, 2055, 5)], 
                            var_name="Year", value_name="Value")
        
        
        if df_melted["Commodity"].nunique()==1:

            if df_melted["Unit"].nunique()==1:
                unit = df_melted["Unit"].unique()[0]
                metric_name = df_melted["Commodity"].unique()[0]
            else: 
                unit='Unit (Mixed)'
                metric_name = "Multiple Region"
            # Plot the line chart
            fig = px.line(df_melted, x="Year", y="Value", color="Region", 
                        title= metric_name, 
                        labels={"Value": unit, "Year": "Year", "Region": "Region"},
                        markers=True)

            # Set the line styles for median and other models
            fig.update_traces(line=dict(color="grey"), selector=dict(name="Region"))

            # Set chart height
            fig.update_layout(height=600, width=1200)  # Adjust the height as needed (default is ~450)
            # Display the plot in Streamlit
            st.plotly_chart(fig)
        else:
            st.write("You have Multiple Commodities, please select one to view the Chart!")