"""
Implementation of a Linear Congruential Generator (LCG) and testing its properties.
"""

import numpy as np
from time import time


def lcg(m, a, c, x0):
    """
    Linear congruential generator (LCG)
    X[n+1] = (a * X[n] + c) mod m

    :param m: modulus
    :param a: multiplier
    :param c: increment
    :param x0: initial value (seed)

    :return: generator function that yields the next random number in the sequence
    """

    x = x0
    while True:
        x = (a * x + c) % m
        yield x


def numpy_rng(m, _a=None, _c=None, _x0=None):
    """
    Adapter for numpy's random number generator to match the LCG interface.

    :param m: upper bound for random numbers (exclusive)
    :param _a: unused (to match LCG interface)
    :param _c: unused (to match LCG interface)
    :param _x0: unused (to match LCG interface)
    :return: generator that yields the next random number in the range [0, m)
    """

    numpy_rng = np.random.default_rng(int(time()))
    while True:
        yield int(numpy_rng.integers(0, m))


def gcd(a, b):
    """
    Compute the greatest common divisor (GCD) of two integers using the Euclidean algorithm.

    :param a: first integer
    :param b: second integer

    :return: GCD of a and b
    """
    while b:
        a, b = b, a % b
    return a


def test_rng(rng_func, m, a, c, x0, count=2000):
    """
    Test the RNG by generating random numbers and analyzing their properties.

    :param rng_func: Random number generator function
    :param m: modulus
    :param a: multiplier
    :param c: increment
    :param x0: initial value (seed)
    :param count: number of random numbers to generate
    :return: dictionary with analysis results
    """

    lcg, time_lcg = rng_func(m, a, c, x0), rng_func(m, a, c, int(time()))

    random_numbers = np.array([next(lcg) for _ in range(count)])

    # Generate $count random pairs (x1, x2)
    random_pairs = random_numbers[
        [next(time_lcg) % count for _ in range(count * 20)]
    ].reshape(-1, 2)

    gcds = [gcd(a, b) for a, b in random_pairs]
    one_prob = gcds.count(1) / len(gcds)

    # Avoid division by zero
    derived_pi = np.sqrt(6 / one_prob) if one_prob else None

    # Calculate the period of the LCG (using numpy)
    index_of_first = np.nonzero(random_numbers == random_numbers[0])
    period = index_of_first[0][1] if len(index_of_first[0]) > 1 else count

    return {
        "Random numbers": random_numbers,
        "Probability that GCD is 1": one_prob,
        "6/pi^2": 6 / (np.pi**2),
        "Derived pi": derived_pi,
        "Actual pi": np.pi,
        # Avoid null pointer exception
        "Difference between derived pi and actual pi": (
            np.abs(derived_pi - np.pi) if derived_pi else None
        ),
        "Period of the RNG": period,
    }
