from decimal import Decimal
from urllib.parse import urlencode
from uuid import uuid4

from defusedxml import ElementTree
import requests

from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import (
    CustomerCreationForm,
    CustomUserCreationForm,
    CreditCardForm,
    PaymentForm,
    ShippingAddressForm,
)
from .helpers import exclude_mask_chars, get_installment_options
from .models import (
    Customer,
    Order,
    Payment,
    ShippingAddress,
    ShippingService,
)


def get_context(request):
    """Funcao que obtem o contexto de todas as paginas do site"""
    context = dict()

    try:
        customer = request.user.customer
    except Customer.DoesNotExist:
        customer, _ = Customer.objects.get_or_create(
            device=request.COOKIES.get("device", uuid4()),
        )
        customer.user = request.user  # social login
        customer.save()
        context["delete_cookie"] = True
    except AttributeError:
        customer, _ = Customer.objects.get_or_create(
            device=request.COOKIES.get("device", uuid4())
        )
        context["set_cookie"] = customer.device

    order, _ = Order.objects.get_or_create(customer=customer, status="analysing")
    context["order"] = order
    items = order.orderitem_set.all().order_by("id")
    context["items"] = items
    return context


def create_shipping_service_and_payment(request, order, zip_code):
    """Função que cria o objeto que representará o servico de frete e o pagamento de uma ordem"""
    payment_type = request.POST["payment_form-payment_type"]
    shipping_service_code = request.POST["shipping_services_form-service"]

    shipping_infos = _get_shipping_infos(
        zip_code=zip_code, service_code=shipping_service_code
    )  # Validate at the backend

    shipping_price = Decimal(shipping_infos["Valor"].replace(",", "."))
    if payment_type == "credit_card":
        number_of_installments = int(request.POST["credit_card_form-installments"])
        value_of_installment = get_installment_options(
            total=order.cart_total + shipping_price
        )[number_of_installments]

    else:
        number_of_installments = 1
        if payment_type == "paypal":
            value_of_installment = order.cart_total + shipping_price
        if payment_type == "bank_slip":
            value_of_installment = order.cash_total + shipping_price

    payment = Payment.objects.create(
        payment_type=payment_type,
        number_of_installments=number_of_installments,
        value_of_installment=value_of_installment,
    )
    shipping_service = ShippingService.objects.create(
        service_code=shipping_service_code,
        price=shipping_price,
        days_to_deliver=int(shipping_infos["PrazoEntrega"]),
    )

    return payment, shipping_service


def render_authenticated_checkout(request):
    """Funcao responsavel pelo processamento de um pedido de um usuario autenticado"""
    context = get_context(request)
    order = context["order"]
    if not order.cart_items:
        return redirect("store")

    payment_form = PaymentForm(prefix="payment_form")
    shipping_form = ShippingAddressForm(prefix="shipping_form", page="checkout")
    credit_card_form = CreditCardForm(
        prefix="credit_card_form", cart_total=order.cart_total
    )
    addresses = ShippingAddress.objects.filter(customer=request.user.customer).order_by(
        "-main"
    )

    if request.method == "POST":
        shipping_address = ShippingAddress.objects.get(
            pk=int(request.POST["user_addresses_form-addresses"])
        )
        payment, shipping_service = create_shipping_service_and_payment(
            request=request, order=order, zip_code=shipping_address.zip_code
        )

        order.payment = payment
        order.shipping_address = shipping_address
        order.shipping_service = shipping_service
        order.transaction_id = uuid4()
        order.requested_at = timezone.now()
        order.requested = True
        order.status = "requested"
        order.save()
        # TODO: Send email to customer
        return redirect("order_success", transaction_id=order.transaction_id)

    return render(
        request,
        "store/checkout_authenticated.html",
        {
            **context,
            "addresses": addresses,
            "shipping_form": shipping_form,
            "payment_form": payment_form,
            "credit_card_form": credit_card_form,
        },
    )


def render_checkout(request):
    """Função que processa a pagina de checkout para usuarios nao autenticados"""
    context = get_context(request)
    order = context["order"]
    if not order.cart_items:
        return redirect("store")

    user_form = CustomUserCreationForm(prefix="user_form")
    customer_form = CustomerCreationForm(prefix="customer_form")
    shipping_form = ShippingAddressForm(prefix="shipping_form", page="checkout")
    payment_form = PaymentForm(prefix="payment_form")
    credit_card_form = CreditCardForm(
        prefix="credit_card_form", cart_total=order.cart_total
    )
    if request.method == "POST":
        shipping_form = ShippingAddressForm(
            request.POST, prefix="shipping_form", page="checkout"
        )
        user_form = CustomUserCreationForm(request.POST, prefix="user_form")
        customer_form = CustomerCreationForm(request.POST, prefix="customer_form")
        payment_form = PaymentForm(request.POST, prefix="payment_form")
        credit_card_form = CreditCardForm(
            prefix="credit_card_form", cart_total=order.cart_total
        )

        if (
            user_form.is_valid()
            and customer_form.is_valid()
            and shipping_form.is_valid()
            and payment_form.is_valid()
        ):
            user = user_form.save()
            # user.is_active = False; user must activate?
            customer = customer_form.save(
                user=user, device=request.COOKIES.get("device")
            )
            shipping_address = shipping_form.save(customer=customer)
            payment, shipping_service = create_shipping_service_and_payment(
                request=request,
                order=order,
                zip_code=request.POST["shipping_form-zip_code"],
            )

            order.payment = payment
            order.shipping_address = shipping_address
            order.shipping_service = shipping_service
            order.transaction_id = uuid4()
            order.requested_at = timezone.now()
            order.status = "requested"
            order.save()
            # TODO: Send email to customer
            login(request, user)
            response = redirect("order_success", transaction_id=order.transaction_id)
            response.delete_cookie("device")
            return response

    return render(
        request,
        "store/checkout.html",
        {
            **context,
            "shipping_form": shipping_form,
            "user_form": user_form,
            "customer_form": customer_form,
            "payment_form": payment_form,
            "credit_card_form": credit_card_form,
        },
    )


def _get_shipping_infos(zip_code, service_code):
    """
    Funcao responsavel por obter as opcoes de frete de um (ou todos) tipo de servico de um pedido

    Args:
        zip_code (int): O CEP do destinatário;
        service_code (list): Lista de código de servicos se quisermos consultar alguns tipos de
            servicos especificos.
    """

    if isinstance(zip_code, str):
        zip_code = exclude_mask_chars(zip_code)

    url = "http://ws.correios.com.br/calculador/CalcPrecoPrazo.aspx?"
    url += urlencode(
        {
            "sCepOrigem": 88037310,
            "sCepDestino": zip_code,
            "nVlPeso": 1,
            "nCdFormato": 1,
            "nVlComprimento": 30,
            "nVlAltura": 20,
            "nVlLargura": 20,
            "sCdMaoPropria": "n",
            "nVlValorDeclarado": 0,
            "sCdAvisoRecebimento": "n",
            "nCdServico": service_code,
            "nVlDiametro": 0,
            "StrRetorno": "xml",
            "nIndicaCalculo": 3,
        }
    )

    tree = ElementTree.fromstring(requests.get(url).text)
    return {
        "Valor": tree.find("cServico").findtext("Valor"),
        "PrazoEntrega": tree.find("cServico").findtext("PrazoEntrega"),
        "Erro": tree.find("cServico").findtext("Erro"),
        "MsgErro": tree.find("cServico").findtext("MsgErro"),
    }
