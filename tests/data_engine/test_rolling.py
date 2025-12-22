from data_engine.rolling import RollingWindow


def test_rolling_window_evicts_old_entries():
    window = RollingWindow[int](maxlen=2)
    window.append(1)
    window.append(2)
    window.append(3)
    assert list(window) == [2, 3]
    assert window.last == 3
    assert len(window) == 2
