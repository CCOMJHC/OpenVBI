import math

from openvbi.core.unit_conversion import to_temperature_kelvin


def test_to_temperature_kelvin():
    expect: float = 300.0
    res: float = to_temperature_kelvin(300.0, 'k')
    assert math.isclose(res, expect)
    res: float = to_temperature_kelvin(300.0, 'K')
    assert res == expect

    expect: float = 293.15
    res: float = to_temperature_kelvin(20, 'c')
    assert res == expect
    res: float = to_temperature_kelvin(20, 'C')
    assert math.isclose(res, expect)

    expect: float = 295.3722222
    res: float = to_temperature_kelvin(72, 'f')
    assert math.isclose(res, expect)
    res: float = to_temperature_kelvin(72, 'F')
    assert math.isclose(res, expect)

    threw_exc: bool = False
    try:
        _ = to_temperature_kelvin(491.67, 'R')
    except ValueError:
        threw_exc = True
    assert threw_exc
