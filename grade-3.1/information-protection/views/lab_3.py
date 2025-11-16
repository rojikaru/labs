import streamlit as st
import helpers
from lib import encrypt_cbc, decrypt_cbc, md5


def display_lab_3_info():
    helpers.write_section_header("File encryption", wrap=False)

    mode = st.selectbox("Select a mode", ["Encrypt", "Unencrypt"])
    pwd = md5(st.text_input("Enter password").strip()).encode("utf-8")
    file = st.file_uploader("Pick a file")

    if pwd and file:
        if mode == "Encrypt":
            heading = "Download encrypted file"

            helpers.write_section_header(heading)
            encrypted_file = encrypt_cbc(file.read(), pwd)

            st.download_button(
                heading, data=encrypted_file, file_name=f"{file.name}.enc"
            )
        else:
            heading = "Download unencrypted file"
            helpers.write_section_header(heading)

            try:
                decrypted_file = decrypt_cbc(file.read(), pwd)
                file_name = (
                    file.name.removesuffix(".enc")
                    if file.name.endswith(".enc")
                    else f"{file.name}.dec"
                )
                st.download_button(heading, data=decrypted_file, file_name=file_name)
            except Exception as e:
                st.error(f"Decryption failed (make sure you provided an encrypted file): {str(e)}")
