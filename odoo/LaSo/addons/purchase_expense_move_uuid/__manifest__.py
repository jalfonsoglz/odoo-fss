# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": 'Purchase, Expense and AccountMove UUID',
    "version": "0.1",
    'category': 'Hidden',
    "author": "gsisa.asilva@gmail.com",
    "depends": [
        'purchase','hr_expense','account',
    ],
    'data': [
        'views/purchase_order_view.xml',
        'views/hr_expense_view.xml',
        'views/account_move_view.xml',
    ],
    'qweb': [
    ],
    'installable': True,
}
