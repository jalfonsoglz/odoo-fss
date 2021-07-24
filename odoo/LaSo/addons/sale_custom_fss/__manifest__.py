# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": 'Sale custom FSS',
    "version": "0.2",
    'category': 'Hidden',
    "author": "gsisa.asilva@gmail.com",
    "depends": [
        'quote',
        'crm',
        'sale_margin',
    ],
    'data': [
        'views/quote.xml',
        'views/sale_margin_view.xml',
    ],
    'qweb': [
    ],
    'installable': True,
}
