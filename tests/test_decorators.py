import time

import pytest

import bell.vrc.utils.decorators as decorators


def test_try_except_no_reraise() -> None:
    @decorators.try_except(reraise=False)
    def fail1() -> None:
        raise ValueError("Test")

    @decorators.try_except()
    def fail2() -> None:
        raise ValueError("Test")

    # make sure no exception gets raised
    fail1()

    # make sure no exception gets raised, as default
    fail2()


def test_try_except_reraise() -> None:
    @decorators.try_except(reraise=True)
    def fail() -> None:
        raise ValueError("Test")

    # make sure exception gets raised
    with pytest.raises(ValueError):
        fail()


def test_run_forever() -> None:
    counter = 0

    @decorators.run_forever(period=0.1)
    def add() -> None:
        nonlocal counter
        counter += 1

        # to not actually run forever, raise exception
        # after 4th iteration
        if counter > 4:
            raise ValueError

    # record the start time
    start_time = time.time()

    # run forever
    with pytest.raises(ValueError):
        add()

    # make sure it took more than 0.4 seconds
    assert time.time() - start_time > 0.4
