from django.contrib.auth.validators import UnicodeUsernameValidator


class CustomUnicodeUsernameValidator(UnicodeUsernameValidator):
    # pylint: disable=too-few-public-methods
    regex = r"^[\w.@+\- ]+$"
    message = "Entre um usuário válido. 150 caracteres ou menos. Apenas letras."


def cpf_is_valid(cpf):
    """Funcao que checa se um cpf eh valido"""

    def get_cpf_sum(cpf, _range):
        _sum = 0
        for char, i in zip(cpf, _range):
            _sum += int(char) * i
        return _sum

    if len(cpf) != 11:
        return False

    if len(set(cpf)) == 1:
        return False

    first_digit_sum = get_cpf_sum(cpf, range(10, 1, -1))
    if int(cpf[-2]) != (first_digit_sum * 10) % 11:
        return False

    second_digit_sum = get_cpf_sum(cpf, range(11, 1, -1))
    if int(cpf[-1]) != (second_digit_sum * 10) % 11:
        return False

    return True
