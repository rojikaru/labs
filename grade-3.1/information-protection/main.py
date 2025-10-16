from typing import Callable, Literal, get_args
import streamlit as st


LabName = Literal[
    "Lab 1: Linear congruential generator (LCG)",
    "Lab 2: Cryptographic hash functions (MD5)",
    "Lab 3: Encryption algorithms (RC5)",
    "Lab 4: Encryption algorithms (RSA)",
    "Lab 5: Digital signatures (RSA)",
]
LAB_LIST = list(get_args(LabName))


def display_lab_1_info():
    # TODO: Implement details for Lab 1
    st.write("TBD")


def display_lab_2_info():
    # TODO: Implement details for Lab 2
    st.write("TBD")


def display_lab_3_info():
    # TODO: Implement details for Lab 3
    st.write("TBD")


def display_lab_4_info():
    # TODO: Implement details for Lab 4
    st.write("TBD")


def display_lab_5_info():
    # TODO: Implement details for Lab 5
    st.write("TBD")


def display_lab_info():
    current_lab = st.session_state.get("current_lab", LAB_LIST[0])

    func_map: dict[LabName, Callable[[], None]] = {
        LAB_LIST[0]: display_lab_1_info,
        LAB_LIST[1]: display_lab_2_info,
        LAB_LIST[2]: display_lab_3_info,
        LAB_LIST[3]: display_lab_4_info,
        LAB_LIST[4]: display_lab_5_info,
    }
    assert set(LAB_LIST) == set(func_map.keys()), "Function map does not cover all labs."

    func = func_map.get(current_lab)
    if func is not None:
        func()


def main():
    st.title("Information Protection Lab")
    lab = st.selectbox("Select a Lab", LAB_LIST)
    st.session_state.current_lab = lab
    display_lab_info()


if __name__ == "__main__":
    main()
