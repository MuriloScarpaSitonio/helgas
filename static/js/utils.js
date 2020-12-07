export function getZipCodeError(errorCode, errorMsg) {
    if (errorCode == '-3') {
        return 'CEP inválido!'
    }
    if (errorCode == '-6') {
        return 'Infelizmente os Correios não oferece serviço para o trecho do CEP informado!'
    }
    if (errorCode == '-33') {
        return 'Sistema dos Correios está fora do ar, logo, não foi possível obter o valor do frete!'
    }
    return "Erro retornado pelos correios: " + errorMsg
}


export async function getZipCodeInfos(value) {
    const response = await fetch("https://viacep.com.br/ws/" + value + "/json/");
    return response.json();
}


export async function getShippingInfos(zip_code) {
    const response = await fetch('/get_shipping_infos/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ zip_code })
    })
    return response.json()
}