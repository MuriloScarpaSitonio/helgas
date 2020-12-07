from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import ugettext_lazy as _

from .choices import (
    GENDERS,
    PAYMENT_TYPES,
    SHIPPING_SERVICES,
    ORDER_STATUSES,
    STATES,
)
from .validators import CustomUnicodeUsernameValidator


class CustomUserManager(BaseUserManager):
    """Classe para adequar as mudanças implementadas na classe CustomUser"""

    use_in_migrations = True

    def _create_user(self, email, username, password, **kwargs):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(email=email, username=username, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, username=None, password=None, **kwargs):
        kwargs.setdefault("is_staff", False)
        kwargs.setdefault("is_superuser", False)
        return self._create_user(email, username, password, **kwargs)

    def create_superuser(self, email, username=None, password=None, **kwargs):
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)

        if kwargs.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if kwargs.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, username, password, **kwargs)


class CustomUser(AbstractUser):
    """Classe que define o usuario"""

    username = models.CharField(
        _("username"), max_length=150, validators=[CustomUnicodeUsernameValidator()]
    )
    email = models.EmailField(
        _("email address"),
        unique=True,
        error_messages={"unique": _("Email já cadastrado no sistema."),},
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = CustomUserManager()

    def __str__(self):
        return str(self.username)


class Customer(models.Model):
    """Classe que define o cliente"""

    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, null=True, blank=True
    )
    cpf = models.CharField(max_length=14, null=True)
    birth_date = models.DateField(null=True)
    phone = models.CharField(max_length=15)
    gender = models.CharField(max_length=9, choices=GENDERS)
    device = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        if self.user:
            return self.user.username
        return str(self.device)


class Product(models.Model):
    """Classe que define o produto"""

    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    main_image = models.ImageField(null=True, blank=True)
    nutritional_infos_image = models.ImageField(null=True, blank=True)
    description = models.TextField(null=True)

    def __str__(self):
        return str(self.name)

    @property
    def image_url(self):
        try:
            return self.main_image.url
        except ValueError:
            return ""

    @property
    def nutritional_infos_url(self):
        try:
            return self.nutritional_infos_image.url
        except ValueError:
            return ""

    @property
    def installments_without_interests(self):
        _installments = {}
        for i in range(1, 7):
            installment = round(self.price / i, 2)
            while installment * i < self.price:
                installment += Decimal(0.01)
            _installments[i] = round(installment, 2)
        return _installments

    @property
    def installments_with_interests(self):
        interest_step = 2
        return {
            i: round((self.price * (100 + i * interest_step) / 100) / i, 2)
            for i in range(7, 13)
        }

    @property
    def cash_price(self):
        return self.price * Decimal(0.9)


class ShippingAddress(models.Model):
    """Classe que define o endereco de entrega"""

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    zip_code = models.CharField(max_length=9)
    address = models.CharField(max_length=200)
    neighborhood = models.CharField(max_length=200)
    number = models.IntegerField()
    complement = models.CharField(max_length=200, blank=True)
    reference = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200)
    uf = models.CharField(max_length=2, choices=STATES)
    country = models.CharField(max_length=6, default="Brasil")
    main = models.BooleanField(default=False)

    def __str__(self):
        address = [
            self.address,
            str(self.number),
            self.complement,
            self.reference,
            self.neighborhood,
            self.city,
            self.uf,
        ]
        return ", ".join(v for v in address if v) + f" - CEP: {self.zip_code}"


class Payment(models.Model):
    """Classe que define o pagamento"""

    payment_type = models.CharField(
        max_length=11, choices=PAYMENT_TYPES, blank=False, default=None
    )
    number_of_installments = models.IntegerField()
    value_of_installment = models.DecimalField(max_digits=7, decimal_places=2)

    def __str__(self):
        return self.get_payment_type_display()

    @property
    def method(self):
        return self.payment_type

    @property
    def total(self):
        return self.number_of_installments * self.value_of_installment


class ShippingService(models.Model):
    """Classe que representa o servico de frete de uma ordem"""

    _tracking_code = models.CharField(max_length=200, null=True)
    service_code = models.CharField(max_length=5, choices=SHIPPING_SERVICES, null=True)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    days_to_deliver = models.IntegerField()

    def __str__(self):
        return self.get_service_code_display()

    @property
    def tracking_code(self):
        if self._tracking_code is None:
            return "Aguardando confirmação"
        return self._tracking_code

    @property
    def deadline(self):
        """Metodo que obtem a data limite de entrega de uma ordem."""
        days_to_deliver = self.days_to_deliver
        deadline_date = self.order.completed_at
        while days_to_deliver > 0:
            deadline_date += timedelta(days=1)
            if deadline_date.weekday() >= 5:  # domingo = 6
                continue
            # TODO: Include holidays
            # if requested_date in holidays:
            #    continue
            days_to_deliver -= 1
        return deadline_date


class Order(models.Model):
    """Classe que define o pedido"""

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True)
    shipping_address = models.ForeignKey(
        ShippingAddress, on_delete=models.SET_NULL, null=True, blank=True
    )
    payment = models.OneToOneField(
        Payment, on_delete=models.SET_NULL, null=True, blank=True
    )
    shipping_service = models.OneToOneField(
        ShippingService, on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(max_length=9, choices=ORDER_STATUSES, default="analysing")
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    requested_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    transaction_id = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return str(self.id)

    @property
    def cart_items(self):
        return sum([item.quantity for item in self.orderitem_set.all()])

    @property
    def cash_total(self):
        return sum([item.cash_total for item in self.orderitem_set.all()])

    @property
    def cart_total(self):
        return sum([item.total for item in self.orderitem_set.all()])

    @property
    def discount(self):
        if self.payment and self.shipping_service and self.payment_type == "bank_slip":
            return self.cart_total + self.shipping_price - self.payment.total
        return 0

    @property
    def interests(self):
        if self.payment and self.shipping_service:
            if self.payment_type == "bank_slip":
                return self.cash_total + self.shipping_price - self.payment.total
            return self.payment.total - (self.cart_total + self.shipping_price)
        return 0

    @property
    def shipping_tracking_code(self):
        return self.shipping_service.tracking_code

    @property
    def shipping_price(self):
        return self.shipping_service.price

    @property
    def shipping_deadline(self):
        return self.shipping_service.deadline

    @property
    def payment_type(self):
        return self.payment.payment_type


class OrderItem(models.Model):
    """Class que representa um item de uma ordem"""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)

    @property
    def total(self):
        return self.product.price * self.quantity

    @property
    def cash_total(self):
        return self.product.cash_price * self.quantity
