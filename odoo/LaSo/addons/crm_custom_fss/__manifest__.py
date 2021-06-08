# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": 'CRM custom FSS',
    "version": "0.1",
    'category': 'Hidden',
    "author": "gsisa.asilva@gmail.com",
    "depends": [
        'sale_custom_fss',
    ],
    'data': [
        'data/ir_sequence_data.xml',
        'views/crm_lead_view.xml',
    ],
    'qweb': [
    ],
    'installable': True,
}
