var updateButtons = document.getElementsByClassName('update-cart')

for (var i = 0; i < updateButtons.length; ++i) {
    updateButtons[i].addEventListener('click', function () {
        location.hash = "showCartDropDown=true"
        var productId = this.dataset.product
        var action = this.dataset.action
        var quantity = document.getElementById('product-quantity-' + productId)

        updateUserOrder(productId, action, quantity)
    })
}



function updateUserOrder(productId, action, quantity) {
    if (quantity != null) {
        var quantity = Number(quantity.value)
    }
    else {
        quantity = 1
    }

    //When sending POST data do backend in django we need do send in a CSFR token
    //https://docs.djangoproject.com/en/3.0/ref/csrf/
    fetch('/update_item/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ productId, action, quantity })
    })
        .then((response) => {
            return response.json()
        })
        .then((data) => {
            console.log('Data:', data)
            location.reload()
        })
}

function removeItem(productId) {
    location.hash = "showCartDropDown=true"
    fetch('/remove_item/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ productId })
    })
        .then((response) => {
            return response.json()
        })
        .then((data) => {
            console.log('Data:', data)
            location.reload()
        })
}