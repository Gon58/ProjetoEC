from decimal import Decimal
from data_pipeline.core.utils import to_decimal_2


def test_to_decimal_2_basic():
    assert to_decimal_2(10.555) == Decimal("10.56")
    assert to_decimal_2(None) == Decimal("0.00")
    assert to_decimal_2("12.3") == Decimal("12.30")