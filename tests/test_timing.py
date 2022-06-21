import time

from bell.avr.utils.timing import rate_limit


def test_rate_limit_period() -> None:
    # create a counter starting at 0
    counter = 0

    # function to add to the counter
    def add() -> None:
        nonlocal counter
        counter += 1

    # make sure counter starts at 0
    assert counter == 0

    # run loop 4 times
    for _ in range(4):
        # run every half second
        rate_limit(add, period=0.5)
        time.sleep(0.2)

    # make sure the counter only incremented 2 times
    assert counter == 2


def test_rate_limit_frequency() -> None:
    # create a counter starting at 0
    counter = 0

    # function to add to the counter
    def add() -> None:
        nonlocal counter
        counter += 1

    # make sure counter starts at 0
    assert counter == 0

    # run loop 4 times
    for _ in range(4):
        # run twice a second
        rate_limit(add, frequency=2)
        time.sleep(0.2)

    # make sure the counter only incremented 2 times
    assert counter == 2
