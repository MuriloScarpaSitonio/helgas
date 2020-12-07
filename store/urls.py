from django.urls import path
from . import views


urlpatterns = [
    path("", views.store, name="store"),
    path("cart/", views.cart, name="cart"),
    path("checkout/", views.checkout, name="checkout"),
    path(
        "register_address_from_checkout/",
        views.register_address_from_checkout,
        name="register_address_from_checkout",
    ),
    path("update_item/", views.update_item, name="update_item"),
    path("register/", views.register, name="register"),
    path("login/", views.login_user, name="login"),
    path("logout/", views.logout_user, name="logout"),
    path("forgot_password/", views.forgot_password, name="forgot_password"),
    path("password_reset_done/", views.password_reset_done, name="password_reset_done"),
    path(
        "password_reset_confirm/<uidb64>/<token>/",
        views.password_reset_confirm,
        name="password_reset_confirm",
    ),
    path(
        "password_reset_complete/",
        views.password_reset_complete,
        name="password_reset_complete",
    ),
    path("product/<product_id>", views.view_product, name="view_product"),
    path("user_page/", views.user_page, name="user_page"),
    path("user_page/order/<order_id>", views.view_order, name="view_order"),
    path("user_page/profile", views.view_profile, name="view_profile"),
    path("user_page/addresses/<address_id>", views.view_address, name="view_address"),
    path("user_page/addresses/", views.view_all_addresses, name="view_all_addresses"),
    path(
        "user_page/register_address/", views.register_address, name="register_address"
    ),
    path("get_shipping_infos/", views.get_shipping_infos, name="get_shipping_infos"),
    path("order/success/<transaction_id>", views.order_success, name="order_success"),
    path(
        "load_credit_card_installments/",
        views.load_credit_card_installments,
        name="load_credit_card_installments",
    ),
    path("remove_item/", views.remove_item, name="remove_item"),
    path("remove_address/", views.remove_address, name="remove_address"),
]
