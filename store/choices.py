GENDERS = [("MAS", "Masculino"), ("FEM", "Feminino")]

STATES = [
    ("", "Escolha um estado"),
    ("AC", "Acre"),
    ("AL", "Alagoas"),
    ("AP", "Amapá"),
    ("AM", "Amazonas"),
    ("BA", "Bahia"),
    ("CE", "Ceará"),
    ("DF", "Distrito Federal"),
    ("ES", "Espírito Santo"),
    ("GO", "Goiás"),
    ("MA", "Maranhão"),
    ("MT", "Mato Grosso"),
    ("NS", "Mato Grosso do Sul"),
    ("MG", "Minas Gerais"),
    ("PA", "Pará"),
    ("PB", "Paraíba"),
    ("PR", "Paraná"),
    ("PE", "Pernambuco"),
    ("PI", "Piauí"),
    ("RJ", "Rio de Janeiro"),
    ("RN", "Rio Grande do Norte"),
    ("RS", "Rio Grande do Sul"),
    ("RO", "Rondônia"),
    ("RR", "Roraima"),
    ("SC", "Santa Catarina"),
    ("SP", "São Paulo"),
    ("SE", "Sergipe"),
    ("TO", "Tocantins"),
]


ORDER_STATUSES = [
    ("analysing", "Em análise"),
    ("requested", "Aguardando pagamento"),
    ("payed", "Pagamento confirmado"),
    ("preparing", "Preparando pedido"),
    ("shipped", "Pedido enviado"),
]

SEDEX = "04014"
PAC = "04510"

SHIPPING_SERVICES = [(SEDEX, "SEDEX"), (PAC, "PAC")]

PAYMENT_TYPES = [
    ("credit_card", "Cartão de crédito"),
    ("paypal", "PayPal"),
    ("bank_slip", "Boleto bancário"),
]


ADDRESS_TYPE_CHOICES = [(True, "Principal"), (False, "Secundário")]
