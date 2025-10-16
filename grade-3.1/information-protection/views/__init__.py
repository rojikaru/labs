from typing import Callable, Literal, get_args
from .lab_1 import display_lab_1_info
from .lab_2 import display_lab_2_info
from .lab_3 import display_lab_3_info
from .lab_4 import display_lab_4_info
from .lab_5 import display_lab_5_info


LabName = Literal[
    "Lab 1: Linear congruential generator (LCG)",
    "Lab 2: Cryptographic hash functions (MD5)",
    "Lab 3: Encryption algorithms (RC5)",
    "Lab 4: Encryption algorithms (RSA)",
    "Lab 5: Digital signatures (RSA)",
]
LAB_LIST = list(get_args(LabName))

render_functions_map: dict[LabName, Callable[[], None]] = {
    LAB_LIST[0]: display_lab_1_info,
    LAB_LIST[1]: display_lab_2_info,
    LAB_LIST[2]: display_lab_3_info,
    LAB_LIST[3]: display_lab_4_info,
    LAB_LIST[4]: display_lab_5_info,
}

# Ensure all labs are covered
assert set(LAB_LIST) == set(
    render_functions_map.keys()
), "Function map does not cover all labs."

__all__ = ["LAB_LIST", "render_functions_map"]
