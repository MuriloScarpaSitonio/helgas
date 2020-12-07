
if (location.hash == "#showCartDropDown=true") {
    if (location.pathname != "/cart/") {
        document.getElementById("cart-items").classList.add("show")
    }
    location.hash = ''
}

$(".dropdown-menu").on("click.bs.dropdown", function (e) {
    e.stopPropagation()
})

window.onclick = function (e) {
    document.getElementById("cart-items").classList.remove("show");
    document.getElementById("user-infos").classList.remove("show");
}
