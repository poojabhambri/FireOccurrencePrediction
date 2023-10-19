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
         
            for idx, png_file in enumerate(selected_files):
                with open(os.path.join(folder_path, png_file), 'rb') as f:
                    png_image = f.read()
                    st.image(png_image, caption=png_file, use_column_width=True)
                    download_button_key = f"download_button_{idx}"
                    st.download_button(
                        label=f"Download {png_file}",
                        data=png_image,
                        file_name=png_file,
                        key=download_button_key,
                    )
        else: 
            for idx, png_file in enumerate(png_files):
                with open(os.path.join(folder_path, png_file), 'rb') as f:
                    png_image = f.read()
                    st.image(png_image, caption=png_file, use_column_width=True)
                    download_button_key = f"download_button_{idx}"
                    st.download_button(
                        label=f"Download {png_file}",
                        data=png_image,
                        file_name=png_file,
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
