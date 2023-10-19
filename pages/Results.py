import streamlit as st
import os
from datetime import timedelta

if 'show_outputs' not in st.session_state:
    st.session_state.show_outputs = False

def show_outputs(folder_path):
    png_files = get_png_files_in_folder(folder_path)

    if png_files:
        if st.session_state.use_range:
            start_date, end_date = st.session_state.selected_date, st.session_state.end_date
            delta = timedelta(days=1)
            date_list = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

            selected_dates = st.multiselect("Select dates", date_list, default=date_list)
            selected_files = [file for file in png_files if any(str(date) in file for date in selected_dates)]

        columns = st.columns(2)

        for idx, file_name in enumerate(selected_files):
            with open(os.path.join(folder_path, file_name), 'rb') as f:
                png_image = f.read()
                png_width = 300  # Default width for files without specific conditions
                if file_name.startswith("ltg_arrival"):
                    png_width = 350
                if file_name.startswith("ltg_dc"):
                    png_width = 305
                if file_name.startswith("ltg_dmc"):
                    png_width = 305
                if file_name.startswith("ltg_holdover"):
                    png_width = 360
                if file_name.startswith("ltg_probarr0"):
                    png_width = 350
                if file_name.startswith("ltg_probign"):
                    png_width = 360
                if file_name.startswith("ltg_totltg"):
                    png_width = 350
                if file_name.startswith("hmn_ffmc"):
                    png_width=356
                if file_name.startswith("hmn_probability"):
                    png_width=395
                if idx % 2 == 0:
                    with columns[0]:
                        st.image(png_image, caption=file_name, width=png_width)
                        download_button_key = f"download_button_{idx}"
                        st.download_button(
                            label=f"Download {file_name}",
                            data=png_image,
                            file_name=file_name,
                            key=download_button_key,
                        )
                else:
                    with columns[1]:
                        st.image(png_image, caption=file_name, width=png_width)
                        download_button_key = f"download_button_{idx}"
                        st.download_button(
                            label=f"Download {file_name}",
                            data=png_image,
                            file_name=file_name,
                            key=download_button_key,
                        )

def get_png_files_in_folder(folder_path):
    png_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]
    return png_files

def main():
    if st.session_state.show_outputs:
        show_outputs("intermediate_output")
    else:
        st.write("Run the model first to see results")

if __name__ == '__main__':
    main()
