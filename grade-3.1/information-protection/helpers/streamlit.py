from typing import Literal
import streamlit as st


def write_section_header(
    title: str, heading: Literal[1, 2, 3, 4, 5, 6] = 2, wrap: bool = True
) -> None:
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
