import streamlit as st
import helpers
from lib import (
    generate_dsa_keys,
    save_dsa_private_key,
    save_dsa_public_key,
    load_dsa_private_key,
    load_dsa_public_key,
    sign_data,
    sign_data_prehashed,
    verify_signature,
    verify_signature_prehashed,
    signature_to_hex,
    signature_from_hex,
)
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature
from time import time


def render_key_generation_section():
    """Render the key generation UI section."""
    helpers.write_section_header("Key Management")

    col1, col2 = st.columns(2)

    with col1:
        key_size = st.select_slider(
            "Select DSA key size (bits)",
            options=[1024, 2048, 3072, 4096],
            value=2048,
        )

    with col2:
        if st.button("Generate New Key Pair"):
            with st.spinner("Generating DSA keys..."):
                private_key, public_key = generate_dsa_keys(key_size)
                st.session_state.dsa_private_key = private_key
                st.session_state.dsa_public_key = public_key
            st.success(f"Generated {key_size}-bit DSA key pair!")


def render_key_download_section():
    """Render the key download buttons if keys exist in session."""
    if "dsa_private_key" not in st.session_state:
        return
    if "dsa_public_key" not in st.session_state:
        return

    col1, col2 = st.columns(2)

    with col1:
        private_pem = save_dsa_private_key(st.session_state.dsa_private_key)
        st.download_button(
            "Download Private Key",
            data=private_pem,
            file_name="dsa_private_key.pem",
            mime="application/x-pem-file",
        )

    with col2:
        public_pem = save_dsa_public_key(st.session_state.dsa_public_key)
        st.download_button(
            "Download Public Key",
            data=public_pem,
            file_name="dsa_public_key.pem",
            mime="application/x-pem-file",
        )


def render_key_upload_section():
    """Render the key upload UI section."""
    helpers.write_section_header("Upload Keys")

    col1, col2 = st.columns(2)

    with col1:
        private_key_file = st.file_uploader(
            "Upload Private Key (PEM)", type=["pem"], key="dsa_private_upload"
        )
        if private_key_file is not None:
            try:
                private_key_data = private_key_file.read()
                st.session_state.dsa_private_key = load_dsa_private_key(private_key_data)
                st.success("Private key loaded successfully!")
            except Exception as e:
                st.error(f"Failed to load private key: {e}")

    with col2:
        public_key_file = st.file_uploader(
            "Upload Public Key (PEM)", type=["pem"], key="dsa_public_upload"
        )
        if public_key_file is not None:
            try:
                public_key_data = public_key_file.read()
                st.session_state.dsa_public_key = load_dsa_public_key(public_key_data)
                st.success("Public key loaded successfully!")
            except Exception as e:
                st.error(f"Failed to load public key: {e}")


def render_string_signing_section():
    """Render the string signing UI section."""
    helpers.write_section_header("Sign String")

    input_string = st.text_area("Enter text to sign", value="Hello, World!")

    if st.button("Sign String"):
        if "dsa_private_key" not in st.session_state:
            st.warning("Please generate or upload a private key first!")
        elif not input_string:
            st.warning("Please enter some text to sign!")
        else:
            try:
                data_bytes = input_string.encode("utf-8")
                start_time = time()
                signature = sign_data(data_bytes, st.session_state.dsa_private_key)
                signing_time = time() - start_time

                signature_hex = signature_to_hex(signature)

                results = {
                    "Input string": input_string,
                    "Signature (hex)": signature_hex,
                    "Signature length (bytes)": len(signature),
                    "Signing time (s)": f"{signing_time:.6f}",
                }
                helpers.write_results(results)

                st.download_button(
                    "Download Signature",
                    data=signature_hex.encode("utf-8"),
                    file_name="signature.txt",
                    mime="text/plain",
                )
            except Exception as e:
                st.error(f"Signing failed: {e}")


def render_file_signing_section():
    """Render the file signing UI section."""
    helpers.write_section_header("Sign File")

    uploaded_file = st.file_uploader("Upload file to sign", key="sign_file")

    if uploaded_file is not None:
        if "dsa_private_key" not in st.session_state:
            st.warning("Please generate or upload a private key first!")
        elif st.button("Sign File"):
            try:
                file_data = uploaded_file.read()
                start_time = time()

                # Use prehashed signing for large files to avoid memory issues
                hasher = hashes.Hash(hashes.SHA256())
                hasher.update(file_data)
                digest = hasher.finalize()
                signature = sign_data_prehashed(digest, st.session_state.dsa_private_key)

                signing_time = time() - start_time
                signature_hex = signature_to_hex(signature)

                results = {
                    "File name": uploaded_file.name,
                    "File size (bytes)": len(file_data),
                    "Signature (hex)": signature_hex,
                    "Signature length (bytes)": len(signature),
                    "Signing time (s)": f"{signing_time:.6f}",
                }
                helpers.write_results(results)

                st.download_button(
                    "Download Signature",
                    data=signature_hex.encode("utf-8"),
                    file_name=f"{uploaded_file.name}.sig",
                    mime="text/plain",
                )
            except Exception as e:
                st.error(f"Signing failed: {e}")


def render_string_verification_section():
    """Render the string signature verification UI section."""
    helpers.write_section_header("Verify String Signature")

    input_string = st.text_area("Enter original text", value="Hello, World!", key="verify_string_input")
    signature_hex = st.text_area("Enter signature (hexadecimal)", key="verify_string_sig")

    if st.button("Verify String Signature"):
        if "dsa_public_key" not in st.session_state:
            st.warning("Please generate or upload a public key first!")
        elif not input_string:
            st.warning("Please enter the original text!")
        elif not signature_hex:
            st.warning("Please enter the signature!")
        else:
            try:
                data_bytes = input_string.encode("utf-8")
                signature = signature_from_hex(signature_hex.strip())

                start_time = time()
                verify_signature(data_bytes, signature, st.session_state.dsa_public_key)
                verification_time = time() - start_time

                st.success("Signature is VALID!")

                results = {
                    "Verification result": "Valid",
                    "Verification time (s)": f"{verification_time:.6f}",
                }
                helpers.write_results(results)
            except ValueError as e:
                st.error(f"Invalid signature format: {e}")
            except InvalidSignature:
                st.error("Signature verification failed: Signature is INVALID!")
            except Exception as e:
                st.error(f"Verification failed: {e}")


def render_file_verification_section():
    """Render the file signature verification UI section."""
    helpers.write_section_header("Verify File Signature")

    col1, col2 = st.columns(2)

    with col1:
        original_file = st.file_uploader(
            "Upload original file", key="verify_file_original"
        )

    with col2:
        signature_file = st.file_uploader(
            "Upload signature file (hex format)", type=["txt", "sig"], key="verify_file_sig"
        )

    if original_file is not None and signature_file is not None:
        if "dsa_public_key" not in st.session_state:
            st.warning("Please generate or upload a public key first!")
        elif st.button("Verify File Signature"):
            try:
                file_data = original_file.read()
                signature_hex = signature_file.read().decode("utf-8").strip()
                signature = signature_from_hex(signature_hex)

                # Use prehashed verification for large files to avoid memory issues
                hasher = hashes.Hash(hashes.SHA256())
                hasher.update(file_data)
                digest = hasher.finalize()

                start_time = time()
                verify_signature_prehashed(
                    digest, signature, st.session_state.dsa_public_key
                )
                verification_time = time() - start_time

                st.success("Signature is VALID!")

                results = {
                    "File name": original_file.name,
                    "File size (bytes)": len(file_data),
                    "Verification result": "Valid",
                    "Verification time (s)": f"{verification_time:.6f}",
                }
                helpers.write_results(results)
            except ValueError as e:
                st.error(f"Invalid signature format: {e}")
            except InvalidSignature:
                st.error("Signature verification failed: Signature is INVALID!")
            except Exception as e:
                st.error(f"Verification failed: {e}")


def display_lab_5_info():
    """Main entry point for Lab 5 DSA digital signature interface."""
    helpers.write_section_header("DSA Digital Signature Algorithm (DSS)", wrap=False)

    render_key_generation_section()
    render_key_download_section()
    render_key_upload_section()
    render_string_signing_section()
    render_file_signing_section()
    render_string_verification_section()
    render_file_verification_section()
