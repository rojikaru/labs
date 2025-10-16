import streamlit as st
import lib
import helpers


def display_lab_1_info():
    helpers.write_section_header("Set RNG parameters", wrap=False)

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

    helpers.write_section_header("Testing custom LCG")
    helpers.write_results(lib.test_rng(lib.lcg, m, a, c, x0, count))

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
    helpers.write_results(period_analysis)

    helpers.write_section_header("Testing numpy random number generator")
    helpers.write_results(lib.test_rng(lib.numpy_rng, m, a, c, x0, count))
