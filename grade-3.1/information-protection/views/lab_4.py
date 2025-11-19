import streamlit as st
import helpers
from lib import (
    generate_rsa_keys,
    save_private_key,
    save_public_key,
    load_private_key,
    load_public_key,
    rsa_encrypt_file,
    rsa_decrypt_file,
    encrypt_cbc,
    decrypt_cbc,
)
from lib.rsa import EncryptionMode
from time import time
import os


def render_key_generation_section():
    """Render the key generation UI section."""
    helpers.write_section_header("Key Management")

    col1, col2 = st.columns(2)

    with col1:
        key_size = st.select_slider(
            "Select RSA key size (bits)",
            options=[1024, 2048, 4096],
            value=2048,
        )

    with col2:
        if st.button("Generate New Key Pair"):
            with st.spinner("Generating RSA keys..."):
                private_key, public_key = generate_rsa_keys(key_size)
                st.session_state.rsa_private_key = private_key
                st.session_state.rsa_public_key = public_key
            st.success(f"Generated {key_size}-bit RSA key pair!")


def render_key_download_section():
    """Render the key download buttons if keys exist in session."""
    if "rsa_private_key" not in st.session_state:
        return
    if "rsa_public_key" not in st.session_state:
        return

    col1, col2 = st.columns(2)

    with col1:
        private_pem = save_private_key(st.session_state.rsa_private_key)
        st.download_button(
            "Download Private Key",
            data=private_pem,
            file_name="private_key.pem",
            mime="application/x-pem-file",
        )

    with col2:
        public_pem = save_public_key(st.session_state.rsa_public_key)
        st.download_button(
            "Download Public Key",
            data=public_pem,
            file_name="public_key.pem",
            mime="application/x-pem-file",
        )


def render_key_upload_section():
    """Render the key upload UI section."""
    helpers.write_section_header("Upload Keys")

    col1, col2 = st.columns(2)

    with col1:
        private_key_file = st.file_uploader(
            "Upload Private Key (PEM)", type=["pem"], key="private_upload"
        )
        if private_key_file is not None:
            try:
                private_key_data = private_key_file.read()
                st.session_state.rsa_private_key = load_private_key(private_key_data)
                st.success("Private key loaded successfully!")
            except Exception as e:
                st.error(f"Failed to load private key: {e}")

    with col2:
        public_key_file = st.file_uploader(
            "Upload Public Key (PEM)", type=["pem"], key="public_upload"
        )
        if public_key_file is not None:
            try:
                public_key_data = public_key_file.read()
                st.session_state.rsa_public_key = load_public_key(public_key_data)
                st.success("Public key loaded successfully!")
            except Exception as e:
                st.error(f"Failed to load public key: {e}")


def handle_file_encryption(file, encryption_mode: EncryptionMode):
    """Handle file encryption and display results."""
    heading = "Download encrypted file"
    helpers.write_section_header(heading)

    try:
        file_data = file.read()
        start_time = time()
        encrypted_file = rsa_encrypt_file(
            file_data, st.session_state.rsa_public_key, mode=encryption_mode
        )
        encryption_time = time() - start_time

        st.write(f"**Encryption time**: *{encryption_time:.4f} seconds*")
        st.write(f"**Original size**: *{len(file_data)} bytes*")
        st.write(f"**Encrypted size**: *{len(encrypted_file)} bytes*")

        st.download_button(
            heading,
            data=encrypted_file,
            file_name=f"{file.name}.rsa",
        )
    except Exception as e:
        st.error(f"Encryption failed: {e}")


def handle_file_decryption(file, encryption_mode: EncryptionMode):
    """Handle file decryption and display results."""
    heading = "Download decrypted file"
    helpers.write_section_header(heading)

    try:
        encrypted_data = file.read()
        start_time = time()
        decrypted_file = rsa_decrypt_file(
            encrypted_data,
            st.session_state.rsa_private_key,
            mode=encryption_mode,
        )
        decryption_time = time() - start_time

        st.write(f"**Decryption time**: *{decryption_time:.4f} seconds*")
        st.write(f"**Encrypted size**: *{len(encrypted_data)} bytes*")
        st.write(f"**Decrypted size**: *{len(decrypted_file)} bytes*")

        file_name = (
            file.name.removesuffix(".rsa")
            if file.name.endswith(".rsa")
            else f"{file.name}.dec"
        )

        st.download_button(heading, data=decrypted_file, file_name=file_name)
    except Exception as e:
        st.error(f"Decryption failed: {e}")


def render_file_encryption_section():
    """Render the file encryption/decryption UI section."""
    helpers.write_section_header("File Encryption")

    mode = st.selectbox("Select a mode", ["Encrypt", "Decrypt"])
    encryption_mode_str = st.selectbox(
        "Select encryption mode",
        ["hybrid", "chunked"],
        help="Hybrid: RSA encrypts AES key, AES encrypts data (fast). Chunked: Pure RSA encryption (slower).",
    )
    encryption_mode: EncryptionMode = encryption_mode_str  # type: ignore

    file = st.file_uploader("Pick a file", key="encrypt_file")

    if mode == "Encrypt":
        if "rsa_public_key" not in st.session_state:
            st.warning("Please generate or upload a public key first!")
        elif file:
            handle_file_encryption(file, encryption_mode)
    else:  # Decrypt
        if "rsa_private_key" not in st.session_state:
            st.warning("Please generate or upload a private key first!")
        elif file:
            handle_file_decryption(file, encryption_mode)


def benchmark_rsa_hybrid(test_data: bytes, results: dict):
    """Benchmark RSA hybrid mode encryption/decryption."""
    try:
        start_time = time()
        rsa_hybrid_encrypted = rsa_encrypt_file(
            test_data, st.session_state.rsa_public_key, mode="hybrid"
        )
        rsa_hybrid_enc_time = time() - start_time

        start_time = time()
        _ = rsa_decrypt_file(
            rsa_hybrid_encrypted,
            st.session_state.rsa_private_key,
            mode="hybrid",
        )
        rsa_hybrid_dec_time = time() - start_time

        rsa_hybrid_total = rsa_hybrid_enc_time + rsa_hybrid_dec_time
        results["RSA Hybrid Encryption Time (s)"] = f"{rsa_hybrid_enc_time:.6f}"
        results["RSA Hybrid Decryption Time (s)"] = f"{rsa_hybrid_dec_time:.6f}"
        results["RSA Hybrid Total Time (s)"] = f"{rsa_hybrid_total:.6f}"
    except Exception as e:
        results["RSA Hybrid Error"] = str(e)


def benchmark_rsa_chunked(test_data: bytes, results: dict):
    """Benchmark RSA chunked mode encryption/decryption."""
    try:
        start_time = time()
        rsa_chunked_encrypted = rsa_encrypt_file(
            test_data, st.session_state.rsa_public_key, mode="chunked"
        )
        rsa_chunked_enc_time = time() - start_time

        start_time = time()
        _ = rsa_decrypt_file(
            rsa_chunked_encrypted,
            st.session_state.rsa_private_key,
            mode="chunked",
        )
        rsa_chunked_dec_time = time() - start_time

        rsa_chunked_total = rsa_chunked_enc_time + rsa_chunked_dec_time
        results["RSA Chunked Encryption Time (s)"] = f"{rsa_chunked_enc_time:.6f}"
        results["RSA Chunked Decryption Time (s)"] = f"{rsa_chunked_dec_time:.6f}"
        results["RSA Chunked Total Time (s)"] = f"{rsa_chunked_total:.6f}"
    except Exception as e:
        results["RSA Chunked Error"] = str(e)


def benchmark_rc5(test_data: bytes, test_password: bytes, results: dict):
    """Benchmark RC5 encryption/decryption."""
    try:
        start_time = time()
        rc5_encrypted = encrypt_cbc(test_data, test_password)
        rc5_enc_time = time() - start_time

        start_time = time()
        _ = decrypt_cbc(rc5_encrypted, test_password)
        rc5_dec_time = time() - start_time

        rc5_total = rc5_enc_time + rc5_dec_time
        results["RC5 Encryption Time (s)"] = f"{rc5_enc_time:.6f}"
        results["RC5 Decryption Time (s)"] = f"{rc5_dec_time:.6f}"
        results["RC5 Total Time (s)"] = f"{rc5_total:.6f}"
    except Exception as e:
        results["RC5 Error"] = str(e)


def calculate_speed_ratios(results: dict):
    """Calculate and add speed ratio comparisons to results."""
    try:
        rsa_hybrid_key = "RSA Hybrid Total Time (s)"
        rc5_total_key = "RC5 Total Time (s)"
        if rsa_hybrid_key not in results or rc5_total_key not in results:
            return

        rsa_time = float(results[rsa_hybrid_key])
        rc5_time = float(results[rc5_total_key])
        ratio = rsa_time / rc5_time
        results["Speed Ratio (RSA Hybrid / RC5)"] = f"{ratio:.4f}x"

        if ratio < 1:
            results["RSA Hybrid is faster by"] = f"{1/ratio:.2f} times"
        else:
            results["RC5 is faster by"] = f"{ratio:.2f} times"
    except ValueError:
        pass


def run_performance_benchmarks(test_size: int):
    """Run all performance benchmarks and display results."""
    test_data = os.urandom(test_size)
    test_password = b"test_password16!"  # RC5 requires 16-byte key

    results = {}

    benchmark_rsa_hybrid(test_data, results)
    benchmark_rsa_chunked(test_data, results)
    benchmark_rc5(test_data, test_password, results)
    calculate_speed_ratios(results)

    helpers.write_results(results)


def render_performance_comparison_section():
    """Render the performance comparison UI section."""
    helpers.write_section_header("Performance Comparison: RSA vs RC5")

    test_size = st.selectbox(
        "Select test data size",
        [1024, 10240, 102400, 1048576],
        format_func=lambda x: (
            f"{x} bytes ({x / 1024:.1f} KB)"
            if x < 1048576
            else f"{x} bytes ({x / 1048576:.1f} MB)"
        ),
        index=2,
    )

    if st.button("Run Performance Test"):
        if (
            "rsa_public_key" not in st.session_state
            or "rsa_private_key" not in st.session_state
        ):
            st.warning("Please generate or upload RSA keys first!")
        else:
            with st.spinner("Running performance tests..."):
                run_performance_benchmarks(test_size)


def display_lab_4_info():
    """Main entry point for Lab 4 RSA encryption interface."""
    helpers.write_section_header("RSA Encryption Algorithm", wrap=False)

    render_key_generation_section()
    render_key_download_section()
    render_key_upload_section()
    render_file_encryption_section()
    render_performance_comparison_section()
