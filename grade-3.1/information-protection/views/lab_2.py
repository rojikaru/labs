import streamlit as st
from hashlib import md5 as hashlib_md5
from time import time
import lib
import helpers


def display_lab_2_info():
    helpers.write_section_header("MD5 Hash Function", wrap=False)

    message = st.text_area("Input message", value="Hello, World!")
    hash_result = lib.md5(message)
    st.write(f"**MD5 Hash**: `{hash_result}`")
    st.write(f"**hashlib MD5**: `{hashlib_md5(message.encode('utf-8')).hexdigest()}`")
    st.write(
        f"**Matches**: *{hash_result == hashlib_md5(message.encode('utf-8')).hexdigest()}*"
    )

    helpers.write_section_header("File Hashing")
    uploaded_file = st.file_uploader("Upload a file to hash")
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        start_time = time()
        custom_hash = lib.md5(file_bytes)
        custom_time = time() - start_time

        start_time = time()
        hashlib_hash = hashlib_md5(file_bytes).hexdigest()
        hashlib_time = time() - start_time

        file_results = {
            "Custom MD5": custom_hash,
            "hashlib MD5": hashlib_hash,
            "Matches": custom_hash == hashlib_hash,
            "Custom MD5 Time (s)": f"{custom_time:.6f}",
            "hashlib MD5 Time (s)": f"{hashlib_time:.6f}",
        }
        helpers.write_results(file_results)

    test_set = {
        "": "d41d8cd98f00b204e9800998ecf8427e",
        "a": "0cc175b9c0f1b6a831c9a71f5c1d8f2",
        "abc": "900150983cd24fb0d6963f7d28e17f72",
        "message digest": "f96b697d7cb7938d525a2f31aaf161d0",
        "abcdefghijklmnopqrstuvwxyz": "c3fcd3d76192e4007dfb496cca67e13b",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789": "d174ab98d277d9f5a5611c2c9f419d9f",
        "12345678901234567890123456789012345678901234567890123456789012345678901234567890": "57edf4a22be3c955ac49da2e2107b67a",
    }
    results = {
        msg: {
            "Custom MD5": lib.md5(msg),
            "hashlib MD5": hashlib_md5(msg.encode("utf-8")).hexdigest(),
            "Expected": expected_hash,
            "Matches": lib.md5(msg) == hashlib_md5(msg.encode("utf-8")).hexdigest(),
        }
        for msg, expected_hash in test_set.items()
    }

    helpers.write_section_header("Test Vectors")
    for msg, result in results.items():
        st.write(f"**Message**: `{msg}`")
        helpers.write_results(result)
        st.write("-----")
