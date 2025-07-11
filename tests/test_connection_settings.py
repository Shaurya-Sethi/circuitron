from circuitron.settings import ConnectionSettings


def test_progressive_timeout() -> None:
    cs = ConnectionSettings()
    assert cs.get_progressive_timeout(0, 10) == 10
    assert cs.get_progressive_timeout(1, 10) >= 10
