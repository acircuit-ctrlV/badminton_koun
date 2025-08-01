import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import date

# --- Excel Processing Logic ---
def process_table_data(table_data_df, shuttle_val, walkin_val, court_val, real_shuttle_val, last_row_to_process):
    """
    Processes the DataFrame: counts slashes, performs calculations,
    and returns updated DataFrame and results.
    """
    # Create a copy to avoid modifying the original DataFrame in-place
    processed_data_df = table_data_df.copy()

    total_shuttlecock_grand = 0

    # Loop through rows up to dynamic_last_row_to_process
    for i in range(last_row_to_process):
        if i >= len(processed_data_df):
            break  # Stop if we exceed the actual number of rows

        name_cell_value = str(processed_data_df.loc[i, 'Name']).strip()
        if not name_cell_value:
            # Clear calculated fields for empty name rows
            processed_data_df.loc[i, 'Total /'] = ''
            processed_data_df.loc[i, 'Price'] = ''
            continue

        # --- CHANGE: Counting 'l' instead of '/' ---
        total_row_slashes = 0
        # Iterate through game columns (indices 4 to 23)
        for col_idx in range(4, 24):
            col_name = processed_data_df.columns[col_idx]
            cell_value = str(processed_data_df.loc[i, col_name])
            total_row_slashes += cell_value.count('l')

        total_shuttlecock_grand += total_row_slashes

        # Update 'Total /' column
        processed_data_df.loc[i, 'Total /'] = total_row_slashes

        # Update 'Price' column
        processed_data_df.loc[i, 'Price'] = (total_row_slashes * shuttle_val) + walkin_val
    
    # Ensure enough rows exist for calculations at row 22 and 23 (indices 21 and 22)
    while len(processed_data_df) < 23:
        new_row = pd.Series([''] * len(processed_data_df.columns), index=processed_data_df.columns)
        processed_data_df = pd.concat([processed_data_df, new_row.to_frame().T], ignore_index=True)

    sum_d = 0  # Sum of 'Total /' column
    sum_e = 0  # Sum of 'Price' column
    for i in range(0, last_row_to_process):
        if i < len(processed_data_df):  # Ensure row exists
            if str(processed_data_df.loc[i, 'Name']).strip():  # Only sum if 'Name' column is not empty
                try:
                    sum_d += float(processed_data_df.loc[i, 'Total /'])
                except (ValueError, TypeError):
                    pass  # Ignore if value is not a number
                try:
                    sum_e += float(processed_data_df.loc[i, 'Price'])
                except (ValueError, TypeError):
                    pass  # Ignore if value is not a number

    # New calculations from the VBA code
    old_solution_sum = ((total_shuttlecock_grand / 4) * real_shuttle_val) + court_val

    results = {
        "total_slashes": total_shuttlecock_grand,
        "old_solution_sum": old_solution_sum,
        "net_price_sum": sum_e,
        "new_solution_minus_old_solution": sum_e - old_solution_sum,
        "sum_D": sum_d  # This is the sum of 'Total /' column
    }

    return processed_data_df, results


def dataframe_to_image(df, date_text=""):
    """
    Converts a pandas DataFrame to a Pillow Image object with aligned columns,
    and adds a title and a date.
    """
    try:
        font_path = "THSarabunNew.ttf"
        font = ImageFont.truetype(font_path, 20)
        title_font = ImageFont.truetype(font_path, 28)
    except IOError:
        st.warning(f"Font file '{font_path}' not found. Using default font.")
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    # Calculate column widths based on the maximum width of text in each column
    column_widths = {}
    for col in df.columns:
        # Get the width of the column header
        header_width = font.getbbox(str(col))[2]
        # Get the max width of all cell values in the column
        max_value_width = max([font.getbbox(str(item))[2] for item in df[col]]) if not df[col].empty else 0
        column_widths[col] = max(header_width, max_value_width)

    # Add some padding to each column
    column_padding = 10
    total_width = sum(column_widths.values()) + (len(column_widths) + 1) * column_padding
    
    # Calculate image dimensions
    line_height = font.getbbox("A")[3] - font.getbbox("A")[1]
    header_height = line_height + column_padding
    row_height = line_height + 5  # Add a little extra space for rows
    
    title_text = "ตารางก๊วน"
    title_height = title_font.getbbox(title_text)[3] - title_font.getbbox(title_text)[1]
    
    img_width = total_width + 40
    img_height = title_height + line_height + 20 + header_height + (len(df) * row_height) + 40
    
    # Create the image
    img = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(img)
    
    x_offset = 20
    y_offset = 20
    
    # Draw title
    draw.text((x_offset, y_offset), title_text, font=title_font, fill='black')
    
    # Draw the date
    date_x = x_offset + title_font.getbbox(title_text)[2] + 20
    date_y = y_offset + (title_height - (font.getbbox(date_text)[3] - font.getbbox(date_text)[1])) / 2
    draw.text((date_x, date_y), date_text, font=font, fill='black')
    
    # Draw the red box around the date
    box_padding = 5
    box_coords = [
        date_x - box_padding,
        y_offset - box_padding,
        date_x + font.getbbox(date_text)[2] + box_padding,
        y_offset + title_height + box_padding
    ]
    draw.rectangle(box_coords, outline="red", width=2)
    
    y_offset_start = y_offset + title_height + 5
    y_offset = y_offset_start
    
    # Draw headers
    current_x = x_offset
    for col in df.columns:
        draw.text((current_x, y_offset), str(col), font=font, fill='black')
        current_x += column_widths[col] + column_padding
        
    y_offset += header_height
    
    # Draw data rows
    for _, row in df.iterrows():
        current_x = x_offset
        for col in df.columns:
            draw.text((current_x, y_offset), str(row[col]), font=font, fill='black')
            current_x += column_widths[col] + column_padding
        y_offset += row_height
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    
    return buf

# --- Streamlit Session State Management ---
headers = ["Name", "Time", "Total /", "Price", "game1", "game2", "game3", "game4", "game5",
           "game6", "game7", "game8", "game9", "game10", "game11", "game12", "game13",
           "game14", "game15", "game16", "game17", "game18", "game19", "game20"]

initial_data_list = [
    ["is", "18:00", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["ploy", "18:00", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["mart", "18:00", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["voy", "18:00", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["jump", "18:00", "", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["tong", "18:00", "", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["k", "18:00", "", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["song", "18:00", "", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["nice", "18:00", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["nut", "18:00", "", "", "l", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["temp", "18:00", "", "", "l", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["pin", "18:00", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]
]
for row in initial_data_list:
    while len(row) < len(headers):
        row.append("")

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(initial_data_list, columns=headers)
if 'results' not in st.session_state:
    st.session_state.results = None
if 'warning_message' not in st.session_state:
    st.session_state.warning_message = ""
if 'current_date' not in st.session_state:
    st.session_state.current_date = date.today()

st.title("คิดเงินค่าตีก๊วน")

# --- Date input and display ---
st.header("ใส่ข้อมูล")
col_date_picker, col_date_display = st.columns([1, 4])
with col_date_picker:
    selected_date = st.date_input("เลือกวันที่", st.session_state.current_date)
with col_date_display:
    st.session_state.current_date = selected_date
    date_to_display = st.session_state.current_date.strftime("%d/%m/%Y")
    st.markdown(f'<div style="border:2px solid red; padding:5px; margin-top:20px;">{date_to_display}</div>', unsafe_allow_html=True)

# --- Input Parameters ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    shuttle_val = st.number_input("ค่าลูก:", value=20, step=1)
with col2:
    walkin_val = st.number_input("ค่าคอร์ดต่อคน:", value=60, step=1)
with col3:
    court_val = st.number_input("ค่าเช่าคอร์ด:", value=0, step=1)
with col4:
    real_shuttle_val = st.number_input("ค่าลูกตามจริง:", value=0, step=1)

st.header("ตารางก๊วน")

# Find the last row with a name to determine the number of rows to display
dynamic_last_row_to_process = 0
for idx, row in st.session_state.df.iterrows():
    if str(row['Name']).strip():
        dynamic_last_row_to_process = idx + 1
# Add a few extra rows for user convenience
num_rows_to_display = max(10, dynamic_last_row_to_process + 5)


# This function will be called when a button is clicked
def handle_slash_button_click(row_idx, col_idx):
    current_value = st.session_state.df.iloc[row_idx, col_idx]
    if current_value == 'l':
        st.session_state.df.iloc[row_idx, col_idx] = ''
    else:
        st.session_state.df.iloc[row_idx, col_idx] = 'l'
    
    # Recalculate everything after a click
    df_to_process = st.session_state.df.fillna('')
    updated_df, results = process_table_data(
        df_to_process, shuttle_val, walkin_val, court_val, real_shuttle_val,
        last_row_to_process=dynamic_last_row_to_process
    )
    st.session_state.df = updated_df
    st.session_state.results = results
    # Rerun to update the display with new calculations
    st.rerun()


# Manually render the table with buttons for 'game' columns
# First, display headers
cols = st.columns([1, 1, 1, 1] + [0.5] * 20)  # Adjust column widths as needed
for i, col_name in enumerate(headers):
    with cols[i]:
        st.write(f"**{col_name}**")

# Display data rows
for i in range(num_rows_to_display):
    # Ensure row exists in the DataFrame, add a new one if not
    if i >= len(st.session_state.df):
        new_row = pd.Series([''] * len(headers), index=headers)
        st.session_state.df = pd.concat([st.session_state.df, new_row.to_frame().T], ignore_index=True)

    row = st.session_state.df.iloc[i]
    cols = st.columns([1, 1, 1, 1] + [0.5] * 20) # Adjust column widths as needed
    
    # Editable 'Name' and 'Time' columns
    with cols[0]:
        st.session_state.df.iloc[i, 0] = st.text_input(f"Name_{i}", value=row['Name'], label_visibility="collapsed")
    with cols[1]:
        st.session_state.df.iloc[i, 1] = st.text_input(f"Time_{i}", value=row['Time'], label_visibility="collapsed")
    
    # Display calculated 'Total /' and 'Price' columns
    with cols[2]:
        st.markdown(f'<div style="text-align: center; height: 38px; display: flex; align-items: center; justify-content: center; background-color: #f0f2f6; border-radius: 5px;">{row["Total /"]}</div>', unsafe_allow_html=True)
    with cols[3]:
        st.markdown(f'<div style="text-align: center; height: 38px; display: flex; align-items: center; justify-content: center; background-color: #f0f2f6; border-radius: 5px;">{row["Price"]}</div>', unsafe_allow_html=True)
    
    # Buttons for 'game' columns
    for j in range(4, 24):
        col_name = headers[j]
        with cols[j]:
            current_value = row[col_name]
            button_label = "l" if current_value == 'l' else ""
            button_style = "primary" if current_value == 'l' else "secondary"
            st.button(
                button_label,
                key=f"button_{i}_{j}",
                on_click=handle_slash_button_click,
                args=(i, j),
                type=button_style,
                use_container_width=True
            )

# Add a button to add a new row
if st.button("Add new row"):
    new_row = pd.Series([''] * len(headers), index=headers)
    st.session_state.df = pd.concat([st.session_state.df, new_row.to_frame().T], ignore_index=True)
    st.rerun()

# --- The rest of your code remains the same ---
st.header("สรุป")
if st.session_state.results:
    st.write(f"**จำนวนลูกเเบดที่ใช้ทั้งหมด:** {st.session_state.results['total_slashes']/4} units")
    st.write(f"**คิดราคาเเบบเก่า:** {st.session_state.results['old_solution_sum']}")
    st.write(f"**คิดราคาเเบบใหม่:** {st.session_state.results['net_price_sum']}")
    st.write(f"**ราคาใหม่ - ราคาเก่า:** {st.session_state.results['new_solution_minus_old_solution']}")
elif st.session_state.results is None and not st.session_state.warning_message:
    st.write("No calculations performed yet or no valid data to process.")

st.markdown("---")
st.subheader("Download ตารางตีก๊วน")

if st.session_state.results:
    date_text_for_image = st.session_state.current_date.strftime("%d/%m/%Y")
    image_bytes = dataframe_to_image(st.session_state.df, date_text_for_image)

    st.download_button(
        label="Download Table as Image",
        data=image_bytes,
        file_name="badminton_table.png",
        mime="image/png"
    )
else:
    st.info("Calculate the results first to enable the download button.")
