import { getZipCodeInfos } from "./utils.js"

var address = document.getElementById("id_address")
var number = document.getElementById("id_number")
var complement = document.getElementById("id_complement")
var neighborhood = document.getElementById("id_neighborhood")
var city = document.getElementById("id_city")
var uf = document.getElementById("id_uf")
var buttons_div = document.getElementById("buttons")

$("#id_zip_code").keyup(function () {
    if ($(this).val().length == 9) {
        var loader = document.getElementById('i-loader')
        var loading_text = document.getElementById('zipCodeLoadingText')
        var error_text = document.getElementById('zipCodeError')
        var address_col = document.getElementById('address-col')
        var number_col = document.getElementById('number-col')
        var neighborhood_complement_reference_row = document.getElementById("neighborhood-complement-reference-row")
        var city_uf_country_row = document.getElementById("city-uf-country-row")

        loader.classList.remove('hidden')
        loading_text.classList.remove('hidden')
        error_text.classList.add('hidden')
        address_col.classList.add('hidden')
        number_col.classList.add('hidden')
        neighborhood_complement_reference_row.classList.add('hidden')
        city_uf_country_row.classList.add('hidden')
        buttons_div.classList.add("hidden")

        getZipCodeInfos($(this).val().replace(/\D/g, ''))
            .then((zip_code_infos) => {
                if (zip_code_infos.erro == undefined) {
                    loader.classList.add('hidden')
                    loading_text.classList.add('hidden')

                    address.setAttribute("value", zip_code_infos.logradouro)
                    neighborhood.setAttribute("value", zip_code_infos.bairro)
                    complement.setAttribute("value", zip_code_infos.complemento)
                    city.setAttribute("value", zip_code_infos.localidade)
                    var options = uf.options
                    for (var i = 0; i < options.length; i++) {
                        if (options[i].value == zip_code_infos.uf) {
                            options[i].selected = true
                        }
                    }
                    $('#id_uf option:not(:selected)').prop('disabled', true);

                    address_col.classList.remove('hidden')
                    number_col.classList.remove('hidden')
                    neighborhood_complement_reference_row.classList.remove('hidden')
                    city_uf_country_row.classList.remove('hidden')
                    buttons_div.classList.remove("hidden")
                }
                else {
                    loader.classList.add('hidden')
                    loading_text.classList.add('hidden')
                    error_text.classList.remove('hidden')
                }
            })
    }
})