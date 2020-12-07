from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from .models import (
    Customer,
    CustomUser,
    Order,
    OrderItem,
    Payment,
    Product,
    ShippingAddress,
    ShippingService,
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Classe para adequar as mudanças implementadas na classe CustomUser"""

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("username",)}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2"),}),
    )
    list_display = ("email", "username", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)


admin.site.register(Customer)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(Product)
admin.site.register(ShippingAddress)
admin.site.register(ShippingService)
