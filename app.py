import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import date

# --- Excel Processing Logic ---
def process_table_data(table_data_df, shuttle_val, walkin_val, court_val, real_shuttle_val, last_row_to_process):
    """
    Processes the DataFrame: sums counts, performs calculations,
    and returns updated DataFrame and results.
    """
    processed_data_df = table_data_df.copy()

    total_shuttlecock_grand = 0

    for i in range(last_row_to_process):
        if i >= len(processed_data_df):
            break

        name_cell_value = str(processed_data_df.loc[i, 'Name']).strip()
        if not name_cell_value:
            processed_data_df.loc[i, 'Total /'] = ''
            processed_data_df.loc[i, 'Price'] = ''
            continue

        total_row_slashes = 0
        for col_idx in range(4, 24):
            col_name = processed_data_df.columns[col_idx]
            try:
                # Sum the integer values directly
                total_row_slashes += int(processed_data_df.loc[i, col_name])
            except (ValueError, TypeError):
                # Handle empty or non-numeric cells gracefully
                pass

        total_shuttlecock_grand += total_row_slashes
        processed_data_df.loc[i, 'Total /'] = total_row_slashes
        processed_data_df.loc[i, 'Price'] = (total_row_slashes * shuttle_val) + walkin_val

    while len(processed_data_df) < 23:
        new_row = pd.Series([''] * len(processed_data_df.columns), index=processed_data_df.columns)
        processed_data_df = pd.concat([processed_data_df, new_row.to_frame().T], ignore_index=True)

    sum_d = 0
    sum_e = 0
    for i in range(0, last_row_to_process):
        if i < len(processed_data_df):
            if str(processed_data_df.loc[i, 'Name']).strip():
                try:
                    sum_d += float(processed_data_df.loc[i, 'Total /'])
                except (ValueError, TypeError):
                    pass
                try:
                    sum_e += float(processed_data_df.loc[i, 'Price'])
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
    
    img_width = total_width + 40
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
        y_offset - box_padding,
        date_x + font.getbbox(date_text)[2] + box_padding,
        y_offset + title_height + box_padding
    ]
    draw.rectangle(box_coords, outline="red", width=2)
    
    y_offset_start = y_offset + title_height + 5
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

# Initialize initial data with numbers for game columns
initial_data_list = [
    ["is", "18:00", "", "", 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["ploy", "18:00", "", "", 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["mart", "18:00", "", "", 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["voy", "18:00", "", "", 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["jump", "18:00", "", "", 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["tong", "18:00", "", "", 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["k", "18:00", "", "", 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["song", "18:00", "", "", 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["nice", "18:00", "", "", 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["nut", "18:00", "", "", 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["temp", "18:00", "", "", 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ["pin", "18:00", "", "", 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]
for row in initial_data_list:
    while len(row) < len(headers):
        row.append(0)

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(initial_data_list, columns=headers)
if 'results' not in st.session_state:
    st.session_state.results = None
if 'warning_message' not in st.session_state:
    st.session_state.warning_message = ""
if 'current_date' not in st.session_state:
    st.session_state.current_date = date.today()

st.title("คิดเงินค่าตีก๊วน")

st.header("ใส่ข้อมูล")
col_date_picker, col_date_display = st.columns([1, 4])
with col_date_picker:
    selected_date = st.date_input("เลือกวันที่", st.session_state.current_date)
with col_date_display:
    st.session_state.current_date = selected_date
    date_to_display = st.session_state.current_date.strftime("%d/%m/%Y")
    st.markdown(f'<div style="border:2px solid red; padding:5px; margin-top:20px;">{date_to_display}</div>', unsafe_allow_html=True)

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

dynamic_last_row_to_process = 0
if not st.session_state.df.empty:
    for idx, row in st.session_state.df.iterrows():
        if str(row['Name']).strip():
            dynamic_last_row_to_process = idx + 1
num_rows_to_display = max(10, dynamic_last_row_to_process + 5)

def handle_slash_button_click(row_idx, col_name, change_type):
    if st.session_state.df.empty:
        return
    
    current_value = st.session_state.df.loc[row_idx, col_name]
    
    try:
        current_value = int(current_value)
    except (ValueError, TypeError):
        current_value = 0

    if change_type == 'plus':
        st.session_state.df.loc[row_idx, col_name] = current_value + 1
    elif change_type == 'minus' and current_value > 0:
        st.session_state.df.loc[row_idx, col_name] = current_value - 1

    df_to_process = st.session_state.df.fillna(0)

    temp_last_row = 0
    if not df_to_process.empty:
        for idx, row in df_to_process.iterrows():
            if str(row['Name']).strip():
                temp_last_row = idx + 1
    
    if temp_last_row > 0:
        updated_df, results = process_table_data(
            df_to_process, shuttle_val, walkin_val, court_val, real_shuttle_val,
            last_row_to_process=temp_last_row
        )
        st.session_state.df = updated_df
        st.session_state.results = results
    
    st.rerun()

col_widths = [2, 2, 1, 1] + [0.5] * 20
main_cols = st.columns(col_widths)
for i, col_name in enumerate(headers):
    with main_cols[i]:
        st.write(f"**{col_name}**")

for i in range(num_rows_to_display):
    if i >= len(st.session_state.df):
        new_row = pd.Series([''] * 4 + [0] * 20, index=headers)
        st.session_state.df = pd.concat([st.session_state.df, new_row.to_frame().T], ignore_index=True)

    row = st.session_state.df.iloc[i]
    row_cols = st.columns(col_widths)
    
    with row_cols[0]:
        st.session_state.df.loc[i, 'Name'] = st.text_input(f"Name_{i}", value=row['Name'], label_visibility="collapsed", key=f"name_input_{i}")
    with row_cols[1]:
        st.session_state.df.loc[i, 'Time'] = st.text_input(f"Time_{i}", value=row['Time'], label_visibility="collapsed", key=f"time_input_{i}")
    
    with row_cols[2]:
        st.markdown(f'<div style="text-align: center; height: 38px; display: flex; align-items: center; justify-content: center; background-color: #f0f2f6; border-radius: 5px; border: 1px solid #d4d4d4; margin-bottom: 8px;">{row["Total /"]}</div>', unsafe_allow_html=True)
    with row_cols[3]:
        st.markdown(f'<div style="text-align: center; height: 38px; display: flex; align-items: center; justify-content: center; background-color: #f0f2f6; border-radius: 5px; border: 1px solid #d4d4d4; margin-bottom: 8px;">{row["Price"]}</div>', unsafe_allow_html=True)

    for j in range(4, 24):
        col_name = headers[j]
        with row_cols[j]:
            btn_cols = st.columns([1, 1, 1], gap="small")
            current_count = int(st.session_state.df.loc[i, col_name])
            
            with btn_cols[0]:
                st.button(
                    "-",
                    key=f"minus_button_{i}_{j}",
                    on_click=handle_slash_button_click,
                    args=(i, col_name, 'minus'),
                    use_container_width=True
                )
            with btn_cols[1]:
                # Display 'l's as a string
                st.markdown(f'<div style="text-align: center; height: 38px; display: flex; align-items: center; justify-content: center;">{"l" * current_count}</div>', unsafe_allow_html=True)
            with btn_cols[2]:
                st.button(
                    "+",
                    key=f"plus_button_{i}_{j}",
                    on_click=handle_slash_button_click,
                    args=(i, col_name, 'plus'),
                    use_container_width=True
                )

if st.button("Add new row"):
    new_row = pd.Series([''] * 4 + [0] * 20, index=headers)
    st.session_state.df = pd.concat([st.session_state.df, new_row.to_frame().T], ignore_index=True)
    st.rerun()

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
