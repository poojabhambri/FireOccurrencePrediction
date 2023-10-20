import streamlit as st
import os

if 'show_outputs' not in st.session_state:
    st.session_state.show_outputs = False
if 'ffmc' not in st.session_state:
    st.session_state.ffmc = False
if 'prob' not in st.session_state:
    st.session_state.prob = False

def show_outputs(folder_path):
    png_files = get_png_files_in_folder(folder_path)
    if png_files:
        if st.session_state.use_range:
            if st.session_state.model == "Human":
                choice = st.selectbox("Which map?", ("FFMC", "Probability"))
            elif st.session_state.model == "Lightning":
                choice = st.selectbox("Which map?", ("Arrival", "DC", "DMC", "Probarr0", "Probign", "Holdover", "Totltg"))
            date = st.slider(
            "Which date would you like to see?",
            min_value = st.session_state.selected_date,
            value= st.session_state.selected_date,
            max_value= st.session_state.end_date,
            format="MM/DD/YY")
            selected_files = [file for file in png_files if str(date) in file]
            png_files = [file for file in selected_files if choice.lower() in file]
            png_file = png_files[0]
            with open(os.path.join(folder_path, png_file), 'rb') as f:
                png_image = f.read()
                st.image(png_image, caption=png_file, use_column_width=True)
                download_button_key = f"download_button_1"
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
