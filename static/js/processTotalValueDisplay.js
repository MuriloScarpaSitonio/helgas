var vars = $('script[src*=processTotalValueDisplay]')

function showDiscontedValue() {
    document.getElementById('total').classList.add('hidden')
    document.getElementById('total-discounted').classList.remove('hidden')
}

function ensureCorrectValue() {
    document.getElementById('total').classList.remove('hidden')
    document.getElementById('total-discounted').classList.add('hidden')
}


$('input[type=radio][name=shipping_services_form-service]').change(function () {
    var radios = document.getElementsByName('shipping_services_form-service')
    for (var i = 0; i < radios.length; i++) {
        if (radios[i].checked) {
            var service_price = document.getElementById('price_' + radios[i].value).innerText.split('R$')[1]

            var total = parseFloat(vars.attr('data-cart_total')) + parseFloat(service_price.replace(",", "."))
            document.getElementById('total_text').innerHTML = "R$" + total.toFixed(2).replace(".", ",")
            var total_discounted = parseFloat(vars.attr('data-cash_total')) + parseFloat(service_price.replace(",", "."))
            document.getElementById('total-discounted_text').innerHTML = "R$" + total_discounted.toFixed(2).replace(".", ",")

            $.ajax({
                url: $('#accordion').attr('data-installments-url'),
                data: { total },
                success: function (data) {
                    $('#id_credit_card_form-installments').html(data)
                }
            })
        }
    }
})