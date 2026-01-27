import random


def test_rng_range():
    for _ in range(100):
        n = random.randint(10, 20)
        assert 10 <= n <= 20
