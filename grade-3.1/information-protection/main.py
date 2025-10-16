from time import time
from typing import Callable, Literal, get_args
import streamlit as st
import lib


LabName = Literal[
    "Lab 1: Linear congruential generator (LCG)",
    "Lab 2: Cryptographic hash functions (MD5)",
    "Lab 3: Encryption algorithms (RC5)",
    "Lab 4: Encryption algorithms (RSA)",
    "Lab 5: Digital signatures (RSA)",
]
LAB_LIST = list(get_args(LabName))


def write_section_header(title: str, heading: int = 2, wrap: bool = True) -> None:
    """
    Write a section header with optional wrapping lines.

    :param title: The title of the section
    :param heading: The heading level (1-6)
    :param wrap: Whether to wrap the title with lines
    :return: None
    """

    st.write(f"{"-----\n\n" if wrap else ""}{'#' * heading} {title}")


def write_results(results: dict) -> None:
    """
    Write the results dictionary to the Streamlit app.

    :param results: Dictionary of results to display
    :return: None
    """

    for key, value in results.items():
        st.write(f"**{key}**: *{value}*")


def display_lab_1_info():
    write_section_header("Set RNG parameters", wrap=False)

    col1, col2 = st.columns(2)
    with col1:
        m = st.number_input("Modulus (m)", value=2**13 - 1, step=1)
        a = st.number_input("Multiplier (a)", value=5**5, step=1)
        c = st.number_input("Increment (c)", value=3, step=1)
    with col2:
        x0 = st.number_input("Initial value (seed, x0)", value=16, step=1)
        count = st.number_input(
            "Count of random numbers to generate", value=2000, step=1
        )

    write_section_header("Testing custom LCG")
    write_results(lib.test_rng(lib.lcg, m, a, c, x0, count))

    # Analyze why the period sucks
    m_factors = [i for i in range(1, m + 1) if m % i == 0]
    period_analysis = {
        "GCD(m, c)": lib.gcd(m, c),
        "Factors of m": m_factors,
        "a-1 mod p = 0 for all prime factors p of m": all(
            (a - 1) % p == 0 for p in m_factors
        ),
    }
    if m % 4 == 0:
        period_analysis[f"If m/4 ({m / 4}), then (a-1)/4 ({(a - 1) / 4})"] = (
            a - 1
        ) % 4 == 0
    write_results(period_analysis)

    write_section_header("Testing numpy random number generator")
    write_results(lib.test_rng(lib.numpy_rng, m, a, c, x0, count))


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

    # Ensure all labs are covered
    assert set(LAB_LIST) == set(
        func_map.keys()
    ), "Function map does not cover all labs."

    func = func_map.get(current_lab)
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
