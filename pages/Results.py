import streamlit as st
import os

def show_outputs(folder_path):
    png_files = get_png_files_in_folder(folder_path)
    if png_files:
        options = st.multiselect(
        'Which map(s) do you want displayed?',
        png_files)
        st.session_state.options = options
        show(folder_path)
    else:
        st.write("No output created.")


def show(folder_path):
    for idx, png_file in enumerate(st.session_state.options):
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
