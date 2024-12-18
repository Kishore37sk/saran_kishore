import streamlit as st
import pandas as pd
import math

# Define the Streamlit app
def main():
    st.title("File Processor with Final Summary")
    st.write("Upload your Excel file and generate a processed summary.")

    # File upload
    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")
    
    if uploaded_file:
        # Load the uploaded file
        df = pd.read_excel(uploaded_file)

        # Step 1: Filter out specific criteria
        df = filter_criteria(df)
        st.write("Filtered Data:", df)

        # Step 2: Calculate 20% of Each User Profile's Entries
        df = get_20_percent_entries(df, user_col='User Profile')

        # Step 3: Identify Highly Coded Modules and Ensure Priority
        df_sampled = filter_modules_with_priority(df, user_col='User Profile', module_col='Module')

        # Step 4: Remove Duplicates in External Code
        df_sampled = df_sampled.drop_duplicates(subset='External Code')

        # Step 5: Generate and display summaries
        category_summary, user_summary = generate_summaries(df, df_sampled)

        # Display summaries
        st.write("Category Summary", category_summary)
        st.write("User Profile Summary", user_summary)

        # Save the final output to an Excel file
        save_to_excel(df_sampled, category_summary, user_summary)

        # Allow user to download the file
        with open('final_sample_with_summary.xlsx', 'rb') as f:
            st.download_button(
                label="Download Summary File",
                data=f,
                file_name="final_sample_with_summary.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Helper functions
def filter_criteria(df):
    df = df[~df['User Profile'].str.contains('OGRDS SYSTEM', na=False)]
    df = df[~df['Changed Using'].str.contains('ITEM CODING|SURGERY', na=False, case=False)]
    return df

def get_20_percent_entries(df, user_col):
    user_entries = df.groupby(user_col).size()
    df['20_percent_entries'] = df[user_col].map(user_entries).apply(lambda x: math.ceil(x * 0.2))
    return df

def filter_modules_with_priority(df, user_col, module_col):
    priority_modules = [  # Add your list of priority modules here
        "BEER", "HEALTH & PERFORMANCE POWDER", "DOG FOOD WET", # ...
        "UNCODEABLE", "FOOD (DETAIL UNKNOWN)", "NPD LOW SALES", "UNCLASSIFIED SERVICES TOTAL"
    ]
    final_rows = []

    for user, group in df.groupby(user_col):
        required_count = int(group['20_percent_entries'].iloc[0])

        # Filter priority modules
        priority_rows = group[group[module_col].isin(priority_modules)]

        # If priority rows meet the required count, use them
        if len(priority_rows) >= required_count:
            final_rows.append(priority_rows.sample(n=required_count))
        else:
            # Otherwise, include all priority rows and fill the rest with non-priority rows
            non_priority_rows = group[~group[module_col].isin(priority_modules)]
            combined_rows = pd.concat([priority_rows, non_priority_rows]).sample(n=required_count)
            final_rows.append(combined_rows)

    return pd.concat(final_rows)

def generate_summaries(df, df_sampled):
    # Category Summary
    category_summary = df_sampled.groupby('Module').size().reset_index(name='Sample Count')
    total_volume_by_module = df.groupby('Module').size().reset_index(name='Total Volume')
    category_summary = category_summary.merge(total_volume_by_module, on='Module')
    category_summary['Percentage'] = (category_summary['Sample Count'] / category_summary['Total Volume'])

    # User Profile Summary
    user_summary = df_sampled.groupby('User Profile').size().reset_index(name='Sample Count')
    total_volume_by_user = df.groupby('User Profile').size().reset_index(name='Total Volume')
    user_summary = user_summary.merge(total_volume_by_user, on='User Profile')
    user_summary['Percentage'] = (user_summary['Sample Count'] / user_summary['Total Volume'])

    return category_summary, user_summary

def save_to_excel(df_sampled, category_summary, user_summary):
    with pd.ExcelWriter('final_sample_with_summary.xlsx') as writer:
        df_sampled.to_excel(writer, sheet_name='Final Sample', index=False)
        category_summary.to_excel(writer, sheet_name='Category Summary', index=False)
        user_summary.to_excel(writer, sheet_name='User Profile Summary', index=False)

# Run the app
if __name__ == "__main__":
    main()
