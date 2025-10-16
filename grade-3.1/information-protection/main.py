import streamlit as st
from views import LAB_LIST, render_functions_map


def display_lab_info():
    current_lab = st.session_state.get("current_lab", LAB_LIST[0])
    func = render_functions_map.get(current_lab)
    if func is not None:
        func()


def main():
    st.set_page_config(
        page_title="Information Protection",  # This sets the browser tab title
        page_icon="🚀",  # Optional: favicon
        layout="centered",  # Optional: wide or centered
    )
    st.title("Information Protection Labs")

    lab = st.selectbox("Select a Lab", LAB_LIST)
    st.write("-----")
    st.session_state.current_lab = lab

    display_lab_info()


if __name__ == "__main__":
    main()
