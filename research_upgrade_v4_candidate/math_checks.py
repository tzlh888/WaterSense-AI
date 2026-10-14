#!/usr/bin/env python3
"""Small transparent checks for numerical examples in the V4 supplement."""

from math import isclose


def run() -> None:
    recall = 699 / (699 + 59)
    precision = 699 / (699 + 9517)
    f1 = 2 * precision * recall / (precision + recall)
    assert isclose(recall, 0.9221635883905013)
    assert isclose(precision, 0.06842208300704777)
    assert isclose(f1, 0.1273920174958994)
    assert 10 * 482 + 219 == 5039
    assert 25 * 59 + 9517 == 10992
    assert isclose(4096 / (1 + 4095 * 0.9), 1.1110809711108096)
    print("mathematical examples verified")


if __name__ == "__main__":
    run()
