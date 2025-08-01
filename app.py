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
    processed_data_list = table_data_df.values.tolist()
    processed_data = [list(row) for row in processed_data_list]

    total_shuttlecock_grand = 0

    for i in range(last_row_to_process):
        if i >= len(processed_data):
            break

        name_cell_value = str(processed_data[i][0]).strip()
        if not name_cell_value:
            if 2 < len(processed_data[i]):
                processed_data[i][2] = ''
            if 3 < len(processed_data[i]):
                processed_data[i][3] = ''
            continue

        total_row_slashes = 0
        for col_idx in range(4, 24):
            if col_idx < len(processed_data[i]):
                cell_value = str(processed_data[i][col_idx])
                total_row_slashes += cell_value.count('l')

        total_shuttlecock_grand += total_row_slashes

        if 2 < len(processed_data[i]):
            processed_data[i][2] = total_row_slashes
        else:
            while len(processed_data[i]) <= 2:
                processed_data[i].append('')
            processed_data[i][2] = total_row_slashes

        if 3 < len(processed_data[i]):
            processed_data[i][3] = (total_row_slashes * shuttle_val) + walkin_val
        else:
            while len(processed_data[i]) <= 3:
                processed_data[i].append('')
            processed_data[i][3] = (total_row_slashes * walkin_val) + walkin_val

    while len(processed_data) < 23:
        processed_data.append([''] * len(table_data_df.columns))

    sum_d = 0
    sum_e = 0
    for i in range(0, last_row_to_process):
        if i < len(processed_data):
            if str(processed_data[i][0]).strip():
                if 2 < len(processed_data[i]):
                    try:
                        sum_d += float(processed_data[i][2])
                    except (ValueError, TypeError):
                        pass
                if 3 < len(processed_data[i]):
                    try:
                        sum_e += float(processed_data[i][3])
                    except (ValueError, TypeError):
                        pass

    old_solution_sum = ((total_shuttlecock_grand / 4) * real_shuttle_val) + court_val

    results = {
        "total_slashes": total_shuttlecock_grand,
        "old_solution_sum": old_solution_sum,
        "net_price_sum": sum_e,
        "new_solution_minus_old_solution": sum_e - old_solution_sum,
        "sum_D": sum_d
    }

    updated_table_df = pd.DataFrame(processed_data, columns=table_data_df.columns)
    return updated_table_df, results

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

    column_widths = {}
    for col in df.columns:
        header_width = font.getbbox(str(col))[2]
        max_value_width = max([font.getbbox(str(item))[2] for item in df[col]]) if not df[col].empty else 0
        column_widths[col] = max(header_width, max_value_width)

    column_padding = 10
    total_width = sum(column_widths.values()) + (len(column_widths) + 1) * column_padding
    
    line_height = font.getbbox("A")[3] - font.getbbox("A")[1]
    header_height = line_height + column_padding
    row_height = line_height + 5
    
    title_text = "ตารางก๊วน"
    title_height = title_font.getbbox(title_text)[3] - title_font.getbbox(title_text)[1]
    date_width = font.getbbox(date_text)[2]
    
    img_width = max(total_width + 40, 20 + title_font.getbbox(title_text)[2] + 20 + date_width + 20)
    img_height = title_height + line_height + 20 + header_height + (len(df) * row_height) + 40
    
    img = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(img)
    
    x_offset = 20
    y_offset = 20
    
    draw.text((x_offset, y_offset), title_text, font=title_font, fill='black')
    
    date_x = x_offset + title_font.getbbox(title_text)[2] + 20
    date_y = y_offset + (title_height - (font.getbbox(date_text)[3] - font.getbbox(date_text)[1])) / 2
    draw.text((date_x, date_y), date_text, font=font, fill='black')
    
    box_padding = 5
    box_coords = [
        date_x - box_padding,
        date_y - box_padding,
        date_x + font.getbbox(date_text)[2] + box_padding,
        date_y + (font.getbbox(date_text)[3] - font.getbbox(date_text)[1]) + box_padding
    ]
    draw.rectangle(box_coords, outline="red", width=2)
    
    y_offset_start = y_offset + title_height + 10
    y_offset = y_offset_start
    
    current_x = x_offset
    for col in df.columns:
        draw.text((current_x, y_offset), str(col), font=font, fill='black')
        current_x += column_widths[col] + column_padding
        
    y_offset += header_height
    
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
col_date_picker, col_date_display, _ = st.columns([1, 1, 3])
with col_date_picker:
    selected_date = st.date_input("เลือกวันที่", st.session_state.current_date)
with col_date_display:
    st.session_state.current_date = selected_date
    date_to_display = st.session_state.current_date.strftime("%d/%m/%Y")
    st.markdown(f'<div style="border:2px solid red; padding:5px; margin-top:20px; width: fit-content;">{date_to_display}</div>', unsafe_allow_html=True)

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

# --- Custom table creation with columns and buttons ---
# Function to handle button clicks and update the DataFrame
def update_slash_count(row_idx, col_name, value):
    """Callback function to update the DataFrame when a button is clicked."""
    current_value = st.session_state.df.at[row_idx, col_name]
    if value == 1:
        st.session_state.df.at[row_idx, col_name] += 'l'
    elif value == -1 and len(current_value) > 0:
        st.session_state.df.at[row_idx, col_name] = current_value[:-1]
    
# Use a custom layout for the table to enable buttons
col_widths = [1, 1, 1, 1] + [1, 1, 1] * 20 # adjust column widths
header_cols = st.columns(col_widths)
for i, col_name in enumerate(headers):
    # Adjust header placement to match the columns
    if i < 4:
        header_cols[i].write(col_name)
    elif i >= 4:
        header_cols[4 + (i-4)*3].write(col_name)

# Loop through each player to create a row of widgets
for idx in range(len(st.session_state.df)):
    row_data = st.session_state.df.iloc[idx]
    
    cols = st.columns(col_widths)

    # Display "Name", "Time", "Total /", "Price" as text
    cols[0].text_input("Name", value=row_data['Name'], key=f"name_{idx}", label_visibility="hidden")
    cols[1].text_input("Time", value=row_data['Time'], key=f"time_{idx}", label_visibility="hidden")
    cols[2].write(row_data['Total /'])
    cols[3].write(row_data['Price'])

    # Display plus/minus buttons for "game1" to "game20"
    for game_idx in range(4, 24):
        col_name = headers[game_idx]
        game_value = row_data[col_name]
        
        game_cols = cols[4 + (game_idx - 4) * 3 : 4 + (game_idx - 4) * 3 + 3]
        
        with game_cols[0]:
            st.button("-", key=f"minus_{idx}_{game_idx}", on_click=update_slash_count, args=(idx, col_name, -1))
        with game_cols[1]:
            st.markdown(f'<div style="text-align: center;">{game_value}</div>', unsafe_allow_html=True)
        with game_cols[2]:
            st.button("+", key=f"plus_{idx}_{game_idx}", on_click=update_slash_count, args=(idx, col_name, 1))
        
# This button is now needed to run the calculation on the updated session state
if st.button("Calculate"):
    st.session_state.warning_message = ""
    df_to_process = st.session_state.df.fillna('')

    dynamic_last_row_to_process = 0
    for idx, row in df_to_process.iterrows():
        if str(row['Name']).strip():
            dynamic_last_row_to_process = idx + 1

    if dynamic_last_row_to_process == 0:
        st.warning("No names found in the table to process. Please enter data in the 'Name' column.")
        st.session_state.results = None
    else:
        invalid_columns = []
        if len(df_to_process.columns) >= 24:
            for col_idx in range(4, 24):
                if col_idx < len(df_to_process.columns):
                    total_slashes_in_column = df_to_process.iloc[:dynamic_last_row_to_process, col_idx].astype(str).str.count('l').sum()
                    if total_slashes_in_column % 4 != 0:
                        invalid_columns.append(df_to_process.columns[col_idx])
        else:
            st.session_state.warning_message = "The table does not have enough columns for full game data validation (expected at least 24 columns for 'game1' to 'game20')."

        if invalid_columns:
            if st.session_state.warning_message:
                st.session_state.warning_message += f"\n\nAdditionally, the total slash count in the following columns is not divisible by 4: {', '.join(invalid_columns)}"
            else:
                st.session_state.warning_message = f"Game ที่ลูกเเบดไม่ลงตัว: {', '.join(invalid_columns)}"

        updated_df, results = process_table_data(
            df_to_process, shuttle_val, walkin_val, court_val, real_shuttle_val,
            last_row_to_process=dynamic_last_row_to_process
        )
        st.session_state.df = updated_df
        st.session_state.results = results
        st.rerun()
        
if st.session_state.warning_message:
    st.warning(st.session_state.warning_message)

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
