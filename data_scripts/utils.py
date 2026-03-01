import base64
from decimal import ROUND_HALF_UP, Decimal

import pandas as pd


def to_decimal_2(value) -> Decimal:
    """
    Converte valor para Decimal com 2 casas decimais.
    """
    if pd.isna(value) or value is None:
        return Decimal("0.00")
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def decode_base64(encoded_str):
    try:
        return base64.b64decode(encoded_str).decode("utf-8")
    except Exception:
        return encoded_str
