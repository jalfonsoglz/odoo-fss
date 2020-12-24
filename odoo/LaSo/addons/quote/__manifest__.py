{
    'name' : 'Cotizador',
    'version' : '2.2',
    'author' : 'Laso Development',
    'website' : 'https://laso-development.com',
    'category' : 'Tools',
    'sequence' : 10,
    'licence' : 'AGPL-3',
    'summary' : 'Utilidad de gestión de cotizaciones',
    'depends' : ['base','sale','purchase','account_analytic_default_purchase'],
    'data' : [
        # security
        'security/quote_security.xml',
        'security/ir.model.access.csv',
        # views
        'views/quote.xml',
        'views/action.xml',
        'views/menu.xml',
        'views/product_product_view.xml'
        # reports
    ],
    'installable' : True,
    'application' : True,
    'auto_install' : False,
}
