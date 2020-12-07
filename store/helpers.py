from decimal import Decimal


def exclude_mask_chars(value):
    _value = ""
    try:
        for char in value:
            if char.isdigit():
                _value += char
        return _value
    except TypeError:  # value is None
        return value


def get_installment_options(total):
    """
    Funcao que obtem as opcoes de parcelamento.
    Args:
        cart_total (decimal.Decimal): O valor total do carrinho.

    Returns:
        installments_options (dict): Dicionario com o numero e valor das parcelas de pagamento
    """
    if isinstance(total, str):
        total = Decimal(total.replace(",", "."))

    if isinstance(total, float):
        total = Decimal(total)

    installments_options = {}
    for i in range(1, 7):
        installment = round(total / i, 2)
        while installment * i < total:
            installment += Decimal(0.01)

        installments_options[i] = round(installment, 2)

    interest_step = 2
    for j in range(7, 13):
        installments_options[j] = round(
            (total * (100 + j * interest_step) / 100) / j, 2
        )
    return installments_options
