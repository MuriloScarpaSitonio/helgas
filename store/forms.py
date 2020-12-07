from datetime import datetime, date, timedelta

from django import forms
from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.core.exceptions import ValidationError
from django.forms import EmailField, EmailInput
from django.utils.translation import gettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from crispy_forms.bootstrap import FormActions
from dateutil.relativedelta import relativedelta

from .choices import ADDRESS_TYPE_CHOICES, STATES
from .helpers import exclude_mask_chars, get_installment_options
from .models import Customer, CustomUser, Payment, ShippingAddress
from .validators import cpf_is_valid


class CustomUserCreationForm(UserCreationForm):
    """Classe para o formulario de criacao do usuario"""

    error_messages = {
        "password_mismatch": "As senhas digitadas não são idênticas",
    }

    class Meta:  # pylint: disable=too-few-public-methods
        model = CustomUser
        fields = ["username", "email", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Nome e sobrenome"}),
            "email": forms.EmailInput(
                attrs={"placeholder": "exemplo@email.com", "autocomplete": "email"}
            ),
        }
        labels = {
            "email": "E-mail",
            "username": "Nome completo",
        }

    def __init__(self, *args, **kwargs):
        try:
            page = kwargs.pop("page")
        except KeyError:
            page = None

        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.label_class = "d-flex justify-content-start fs-85"
        self.helper.form_id = "user-form"
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = get_user_creation_form_layout(page)

        self.fields["password1"].widget = forms.PasswordInput(
            attrs={"placeholder": "******"},
        )
        self.fields["password1"].label = "Senha"
        self.fields["password1"].help_text = "Mínimo de seis caracteres"

        self.fields["password2"].widget = forms.PasswordInput(
            attrs={"placeholder": "******"}
        )
        self.fields["password2"].label = "Confirmar senha"
        self.fields["password2"].help_text = "Digite a mesma senha"

    def clean_username(self):
        username = self.cleaned_data["username"]
        if len(username.split(" ")) <= 1:
            raise ValidationError(
                _("Digite seu nome completo"),
                code="invalid",
                params={"username": username},
            )
        return username


def get_user_creation_form_layout(page):
    """
    Funcao que obtem o layout do formulario de criacao do usuario.

    Args:
        page(str): String que indica a página onde o formulario estará.
    """
    if page:
        return Layout(
            Row(
                Column("email", css_class="form-group col-md-3"),
                Column("username", css_class="form-group col-md-3"),
                Column("password1", css_class="form-group col-md-3"),
                Column("password2", css_class="form-group col-md-3"),
                css_class="form-row",
            ),
        )
    return Layout(
        Row(
            Column("email", css_class="form-group col-md-6"),
            Column("username", css_class="form-group col-md-6"),
            css_class="form-row",
        ),
        Row(
            Column("password1", css_class="form-group col-md-6"),
            Column("password2", css_class="form-group col-md-6"),
            css_class="form-row",
        ),
    )


class CustomerCreationForm(forms.ModelForm):
    """Classe para o formulario de criacao do usuario"""

    class Meta:  # pylint: disable=too-few-public-methods, missing-class-docstring
        model = Customer
        fields = ["cpf", "phone", "gender", "birth_date"]
        widgets = {
            "cpf": forms.TextInput(
                attrs={"placeholder": "000.000.000-00", "data-mask": "000.000.000-00"}
            ),
            "phone": forms.TextInput(
                attrs={
                    "placeholder": "(00) 00000-0000",
                    "data-mask": "(00) 00000-0000",
                }
            ),
            "gender": forms.Select(),
            "birth_date": forms.DateInput(
                attrs={"placeholder": "dd/mm/aaaa", "data-mask": "00/00/0000"},
            ),
        }
        labels = {
            "cpf": "CPF",
            "gender": "Sexo",
            "phone": "Telefone celular",
            "birth_date": "Data de nascimento",
        }

        error_messages = {"birth_date": {"invalid": "Data inválida"}}

    def __init__(self, *args, **kwargs):
        try:
            page = kwargs.pop("page")
        except KeyError:
            page = None

        super(CustomerCreationForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.label_class = "d-flex justify-content-start fs-85"
        self.helper.form_id = "customer-form"
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = get_customer_creation_form_layout(page)

        self.fields["birth_date"].input_formats = ["%d/%m/%Y"]

    def save(self, user, device, commit=True):  # pylint: disable=arguments-differ
        instance = super(CustomerCreationForm, self).save(commit=False)
        customer, _ = Customer.objects.get_or_create(device=device)
        customer.user = user
        customer.cpf = instance.cpf
        customer.phone = instance.phone
        customer.gender = instance.gender
        customer.birth_date = instance.birth_date
        if commit:
            customer.save()
        return customer

    def clean_cpf(self):
        """Funcao que valida o CPF de um usuario"""
        cpf = exclude_mask_chars(self.cleaned_data["cpf"])
        if cpf and Customer.objects.filter(cpf=cpf).exists():
            customer = Customer.objects.get(cpf=cpf)
            raise ValidationError(
                _(
                    "O CPF %(cpf)s já está cadastrado no sistema! "
                    "Cliente cadastrado no sistema em %(created_date)s às %(created_time)s."
                ),
                code="invalid",
                params={
                    "cpf": self.cleaned_data["cpf"],
                    "created_date": datetime.strftime(
                        customer.created_at - timedelta(hours=3), format="%d/%m/%Y"
                    ),
                    "created_time": datetime.strftime(
                        customer.created_at - timedelta(hours=3), format="%H:%M:%S"
                    ),
                },
            )

        if not cpf_is_valid(cpf):  # TODO: validate while typing with javascript
            raise ValidationError(
                _("O CPF %(cpf)s é inválido"),
                code="invalid",
                params={
                    "cpf": self.cleaned_data["cpf"],
                },
            )
        return cpf

    def clean_birth_date(self):
        """Funcao que valida a data de nascimento de um usuario"""
        birth_date = self.cleaned_data["birth_date"]

        if birth_date and birth_date > date.today():
            raise ValidationError(
                _("A data %(birth_date)s é inválida, pois trata-se de uma data futura"),
                code="invalid",
                params={"birth_date": birth_date.strftime("%d/%m/%Y")},
            )

        if birth_date and birth_date + relativedelta(years=18) > date.today():
            raise ValidationError(
                _(
                    "A data %(birth_date)s é inválida, pois o usuário tem menos de 18 anos"
                ),
                code="invalid",
                params={"birth_date": birth_date.strftime("%d/%m/%Y")},
            )
        return birth_date

    def clean_phone(self):  # TODO: validate phone
        return exclude_mask_chars(self.cleaned_data["phone"])


def get_customer_creation_form_layout(page):
    """
    Funcao que obtem o layout do formulario de criacao do cliente.

    Args:
        page(str): String que indica a página onde o formulario estará.
    """
    if page:
        return Layout(
            Row(
                Column("cpf", css_class="form-group col-md-3"),
                Column("birth_date", css_class="form-group col-md-3"),
                Column("gender", css_class="form-group col-md-3"),
                Column("phone", css_class="form-group col-md-3"),
                css_class="form-row",
            ),
        )
    return Layout(
        Row(
            Column("cpf", css_class="form-group col-md-6"),
            Column("birth_date", css_class="form-group col-md-6"),
            css_class="form-row",
        ),
        Row(
            Column("gender", css_class="form-group col-md-6"),
            Column("phone", css_class="form-group col-md-6"),
            css_class="form-row",
        ),
    )


class CustomAuthenticationForm(AuthenticationForm):
    """Classe para o formulario de autenticacao do usuario"""

    # username as email
    username = EmailField(
        label="E-mail",
        max_length=254,
        widget=EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "exemplo@email.com",
                "class": "form-control",
            }
        ),
    )

    password = forms.CharField(
        label=_("Senha"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": "Senha",
                "class": "form-control",
            }
        ),
    )

    error_messages = {
        "invalid_login": _("Por favor, forneça um e-mail e senha corretos."),
        "inactive": _("Essa conta está inativa."),
    }

    def clean(self):
        email = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if email is not None and password:
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:
                try:
                    _user = CustomUser.objects.get(email=email)
                except CustomUser.DoesNotExist:
                    _user = None

                if _user is not None and _user.check_password(password):
                    self.confirm_login_allowed(_user)
                else:
                    raise forms.ValidationError(
                        self.error_messages["invalid_login"],
                        code="invalid_login",
                    )

        return self.cleaned_data


class CustomPasswordResetForm(PasswordResetForm):
    pass


class CustomSetPasswordForm(SetPasswordForm):
    error_messages = {
        "password_mismatch": _("As senhas digitadas não são idênticas"),
        "password_too_short": _(
            "Senha com poucos caracteres. A senha deve conter no mínimo 6 caracteres."
        ),
    }
    new_password1 = forms.CharField(
        label=_("Senha"),
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "Senha",
                "class": "form-control",
            }
        ),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("Repetir senha"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "Repetir senha",
                "class": "form-control",
            }
        ),
    )

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages["password_mismatch"],
                    code="password_mismatch",
                )

        if len(password2) < 6:
            raise forms.ValidationError(
                self.error_messages["password_too_short"],
                code="password_too_short",
            )
        password_validation.validate_password(password2, self.user)
        return password2


class ShippingAddressForm(forms.ModelForm):
    """Classe para o formulario de criacao de um endereco"""

    class Meta:  # pylint: disable=too-few-public-methods, missing-class-docstring
        model = ShippingAddress
        fields = [
            "zip_code",
            "address",
            "neighborhood",
            "number",
            "complement",
            "reference",
            "city",
            "uf",
            "country",
        ]
        widgets = {
            "zip_code": forms.TextInput(
                attrs={"placeholder": "00000-000", "data-mask": "00000-000"}
            ),
            "neighborhood": forms.TextInput(
                attrs={"placeholder": "Bairro", "readonly": True}
            ),
            "address": forms.TextInput(
                attrs={"placeholder": "Endereço", "readonly": True}
            ),
            "number": forms.NumberInput(attrs={"min": 1}),
            "complement": forms.TextInput(attrs={"placeholder": "Casa, Condomínio..."}),
            "reference": forms.TextInput(attrs={"placeholder": "Perto de..."}),
            "city": forms.TextInput(attrs={"readonly": True}),
            "uf": forms.Select(attrs={"readonly": True}, choices=STATES),
            "country": forms.TextInput(
                attrs={"value": "Brasil", "readonly": True},
            ),
        }
        labels = {
            "zip_code": "CEP",
            "neighborhood": "Bairro",
            "address": "Endereço",
            "number": "Nº",
            "complement": "Complemento",
            "reference": "Referência",
            "city": "Cidade",
            "uf": "Estado",
            "country": "País",
        }

    def __init__(self, *args, **kwargs):
        try:
            page = kwargs.pop("page")
        except KeyError:
            page = None

        super(ShippingAddressForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = "shipping-form"
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.label_class = "d-flex justify-content-start fs-85"
        self.helper.layout = get_shipping_form_layout(page)

    def save(self, customer, commit=True):  # pylint: disable=arguments-differ
        instance = super(ShippingAddressForm, self).save(commit=False)
        instance.customer = customer
        if ShippingAddress.objects.filter(customer=customer, main=True):
            instance.main = False
        else:
            instance.main = True
        if commit:
            instance.save()
        return instance

    def clean_zip_code(self):
        return exclude_mask_chars(self.cleaned_data["zip_code"])


def get_shipping_form_layout(page):
    """
    Funcao que obtem o layout do formulario de criacao de um endereco.

    Args:
        page(str): String que indica a página onde o formulario estará.
    """
    if page == "checkout":
        return Layout(
            Row(
                Column("zip_code", css_class="form-group col-md-4"),
                css_class="form-row",
            ),
            Row(
                Column("address", css_class="form-group col-md-9"),
                Column("number", css_class="form-group col-md-3"),
                css_class="form-row hidden",
                id="address-number-row",
            ),
            Row(
                Column("complement", css_class="form-group col-md-6"),
                Column("reference", css_class="form-group col-md-6"),
                css_class="form-row hidden",
                id="complement-reference-row",
            ),
            Row(
                Column("neighborhood", css_class="form-group col-md-6"),
                Column("city", css_class="form-group col-md-6"),
                css_class="form-row hidden",
                id="neighborhood-city-row",
            ),
            Row(
                Column("uf", css_class="form-group col-md-6"),
                Column("country", css_class="form-group col-md-6"),
                css_class="form-row hidden",
                id="uf-country-row",
            ),
        )

    return Layout(
        Row(
            Column("zip_code", css_class="form-group col-md-2"),
            Column("address", css_class="form-group col-md-8 hidden", id="address-col"),
            Column("number", css_class="form-group col-md-2 hidden", id="number-col"),
            css_class="form-row",
        ),
        Row(
            Column("neighborhood", css_class="form-group col-md-4"),
            Column("complement", css_class="form-group col-md-4"),
            Column("reference", css_class="form-group col-md-4"),
            css_class="form-row hidden",
            id="neighborhood-complement-reference-row",
        ),
        Row(
            Column("city", css_class="form-group col-md-4"),
            Column("uf", css_class="form-group col-md-4"),
            Column("country", css_class="form-group col-md-4"),
            css_class="form-row hidden",
            id="city-uf-country-row",
        ),
    )


class CustomUserChangeForm(forms.Form):
    """Classe para o formulario de alteracao de informacoes de um cliente"""

    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(
            attrs={"placeholder": "exemplo@email.com", "autocomplete": "email"}
        ),
        disabled=True,
    )
    username = forms.CharField(
        label="Nome completo",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Nome completo"}),
    )
    cpf = forms.CharField(
        label="CPF",
        max_length=14,
        widget=forms.TextInput(
            attrs={"placeholder": "000.000.000-00", "data-mask": "000.000.000-00"}
        ),
        disabled=True,
    )
    birth_date = forms.DateField(
        label="Data de nascimento",
        widget=forms.DateInput(
            attrs={"placeholder": "mm/dd/aaaa", "data-mask": "00/00/0000"}
        ),
        input_formats=["%d/%m/%Y"],
        error_messages={"invalid": "Data inválida"},
    )
    gender = forms.ChoiceField(
        label="Sexo",
        choices=[("MAS", "Masculino"), ("FEM", "Feminino")],
    )
    phone = forms.CharField(
        label="Telefone celular",
        widget=forms.TextInput(
            attrs={"placeholder": "(00) 00000-0000", "data-mask": "(00) 00000-0000"}
        ),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")

        super(CustomUserChangeForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.label_class = "d-flex justify-content-start fs-85"
        self.helper.layout = Layout(
            Row(
                Column("email", css_class="form-group col-md-6"),
                Column("username", css_class="form-group col-md-6"),
                css_class="form-row",
            ),
            Row(
                Column("cpf", css_class="form-group col-md-6"),
                Column("birth_date", css_class="form-group col-md-6"),
                css_class="form-row",
            ),
            Row(
                Column("gender", css_class="form-group col-md-6"),
                Column("phone", css_class="form-group col-md-6"),
                css_class="form-row",
            ),
            FormActions(
                Submit(
                    "save-changes",
                    "ALTERAR DADOS",
                    css_class="btn btn-lg btn-dark",
                ),
                css_class="d-flex justify-content-end",
            ),
        )

        self.fields["email"].initial = self.user.email
        self.fields["username"].initial = self.user.username
        self.fields["cpf"].initial = self.user.customer.cpf
        self.fields["gender"].initial = self.user.customer.gender
        self.fields["phone"].initial = self.user.customer.phone
        try:
            self.fields["birth_date"].initial = datetime.strftime(
                self.user.customer.birth_date, "%d/%m/%Y"
            )
        except TypeError:  # None
            self.fields["birth_date"].initial = self.user.customer.birth_date

        if not self.user.customer.cpf:
            self.fields["cpf"].disabled = False

    @property
    def has_different_values(self):
        return any(
            True
            for field, value in self.data.items()
            if self.fields.get(field) and self.fields[field].initial != value
        )

    def save(self, commit=True):  # pylint: disable=arguments-differ
        """Metodo que salva as alteracoes nos dados de um cliente"""
        for field, value in self.data.items():
            if self.fields.get(field):
                print(self.fields.get(field), value)
                if self.fields[field].initial != value:
                    if field in ("email", "username"):
                        setattr(self.user, field, value)
                    else:
                        if field == "birth_date":
                            value = datetime.strptime(value, "%d/%m/%Y").date()
                        setattr(self.user.customer, field, value)
        if commit:
            self.user.save()
            self.user.customer.save()
        return self.user

    def clean_username(self):
        username = self.cleaned_data["username"]
        if len(username.split(" ")) <= 1:
            raise ValidationError(
                _("Digite seu nome completo"),
                code="invalid",
                params={"username": username},
            )
        return username

    def clean_birth_date(self):
        """Funcao que valida a data de nascimento de um usuario"""
        birth_date = self.cleaned_data["birth_date"]

        if birth_date and birth_date > date.today():
            raise ValidationError(
                _("A data %(birth_date)s é inválida, pois trata-se de uma data futura"),
                code="invalid",
                params={"birth_date": birth_date.strftime("%d/%m/%Y")},
            )

        if birth_date and birth_date + relativedelta(years=18) > date.today():
            raise ValidationError(
                _(
                    "A data %(birth_date)s é inválida, pois o usuário tem menos de 18 anos"
                ),
                code="invalid",
                params={"birth_date": birth_date.strftime("%d/%m/%Y")},
            )
        return birth_date

    def clean_phone(self):  # TODO: validate phone
        return exclude_mask_chars(self.cleaned_data["phone"])


class ShippingAddressChangeForm(ShippingAddressForm):
    """Classe para o formulario de alteracao de informacoes de um endereco"""

    main = forms.ChoiceField(
        label="Tipo de endereço",
        widget=forms.Select(attrs={"class": "form-control"}),
        choices=ADDRESS_TYPE_CHOICES,
    )

    def __init__(self, *args, **kwargs):
        self.shipping_address = kwargs.pop("shipping_address")

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.label_class = "d-flex justify-content-start fs-85"
        self.helper.layout = Layout(
            Row(
                Column("zip_code", css_class="form-group col-md-2"),
                Column("address", css_class="form-group col-md-8", id="address-col"),
                Column("number", css_class="form-group col-md-2", id="number-col"),
                css_class="form-row",
            ),
            Row(
                Column("neighborhood", css_class="form-group col-md-4"),
                Column("complement", css_class="form-group col-md-4"),
                Column("reference", css_class="form-group col-md-4"),
                css_class="form-row",
                id="neighborhood-complement-reference-row",
            ),
            Row(
                Column("city", css_class="form-group col-md-3"),
                Column("uf", css_class="form-group col-md-3"),
                Column("country", css_class="form-group col-md-3"),
                Column("main", css_class="form-group col-md-3"),
                css_class="form-row",
                id="city-uf-country-row",
            ),
        )

        self.fields["zip_code"].initial = self.shipping_address.zip_code
        self.fields["address"].initial = self.shipping_address.address
        self.fields["neighborhood"].initial = self.shipping_address.neighborhood
        self.fields["number"].initial = self.shipping_address.number
        self.fields["complement"].initial = self.shipping_address.complement
        self.fields["reference"].initial = self.shipping_address.reference
        self.fields["city"].initial = self.shipping_address.city
        self.fields["uf"].initial = self.shipping_address.uf
        self.fields["country"].initial = self.shipping_address.country
        self.fields["main"].initial = self.shipping_address.main
        if self.shipping_address.main:
            self.fields["main"].disabled = True

    def is_valid(self):
        new_values = {}
        for field, value in self.data.items():
            if self.fields.get(field):
                if field == "number":
                    value = int(value)
                if field == "main":
                    value = value == "True"
                if self.fields[field].initial != value:
                    new_values[field] = value
        return new_values

    def save(self, new_values, customer, commit=True):
        # pylint: disable=arguments-differ
        for field, value in new_values.items():
            if field == "main":
                if value:
                    address = ShippingAddress.objects.get(customer=customer, main=True)
                    address.main = False
                    address.save()
            setattr(self.shipping_address, field, value)
        if commit:
            self.shipping_address.save()
        return self.shipping_address


class PaymentForm(forms.ModelForm):
    """Classe para o formulario de definicao de um pagamento"""

    class Meta:  # pylint: disable=too-few-public-methods
        model = Payment
        fields = ["payment_type"]
        widgets = {"payment_type": forms.RadioSelect()}

    def __init__(self, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = "payment-form"
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.form_show_labels = False

    def payment_type_choices(self):
        return self.fields["payment_type"].choices

    def save(self, number_of_installments, value_of_installment, commit=True):
        # pylint: disable=arguments-differ
        instance = super(PaymentForm, self).save(commit=False)
        instance.number_of_installments = number_of_installments
        instance.value_of_installment = value_of_installment
        if commit:
            instance.save()
        return instance


class CreditCardForm(forms.Form):
    """Classe para o formulario de definicao de um pagamento utilizando cartao de credito"""

    number = forms.CharField(
        label="Número do cartão",
        widget=forms.TextInput(
            attrs={
                "placeholder": "0000 0000 0000",
                "data-mask": "0000 0000 0000",
                "disabled": True,
            }
        ),
    )
    expiring_date = forms.CharField(
        label="Validade",
        widget=forms.DateInput(
            attrs={
                "placeholder": "mm/aaaaa",
                "data-mask": "00/0000",
                "disabled": True,
            },
            format="%m/%Y",
        ),
    )
    holder_name = forms.CharField(
        label="Nome do titular do cartão",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Nome do titular do cartão",
                "disabled": True,
            }
        ),
    )
    security_code = forms.CharField(
        label="CVV",
        widget=forms.TextInput(
            attrs={
                "placeholder": "000",
                "data-mask": "000",
                "disabled": True,
            }
        ),
    )
    installments = forms.ChoiceField(
        label="Parcelas", widget=forms.Select(), choices=[]
    )

    def __init__(self, *args, **kwargs):
        self.cart_total = kwargs.pop("cart_total")

        super(CreditCardForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = "credit-card-form"
        self.helper.label_class = "d-flex justify-content-start fs-85"
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Row(
                Column("number", css_class="form-group col-md-8"),
                Column("expiring_date", css_class="form-group col-md-4"),
                css_class="form-row",
            ),
            Row(
                Column("holder_name", css_class="form-group col-md-9"),
                Column("security_code", css_class="form-group col-md-3"),
                css_class="form-row",
            ),
            Row(
                Column("installments", css_class="form-group col-md-12"),
                css_class="form-row",
            ),
        )

        self.fields["installments"].choices = organize_installment_text(
            self.installments_infos
        )

    @property
    def installments_infos(self):
        return get_installment_options(total=self.cart_total)


def organize_installment_text(installments_options):
    """
    Funcao que organiza o texto das opcoes de parcelamento.
    Args:
        installments_options (dict): Dicionario com o numero e valor das parcelas de pagamento.

    Returns:
        installments_choices (dict): Dicionario com o numero e texto das parcelas de pagamento
    """
    installments_choices = []
    for n_installment, v_installment in installments_options.items():
        if n_installment < 7:
            text = f"{n_installment}x sem juros de R${v_installment}"
        else:
            text = f"{n_installment}x de R${v_installment}"
        installments_choices.append(
            (
                n_installment,
                text.replace(".", ",")
                # TODO: break installments per month
                # avoid n_installment*v_installment > cart_total
            )
        )
    return installments_choices
