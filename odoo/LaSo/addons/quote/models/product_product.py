from odoo import api, fields, models

class ProductProduct(models.Model):
    _inherit = ['product.template']

    employee = fields.Boolean('Es empleado',
                    default=False,
                    help='Si este campo esta marcado, el producto no generará RFQ desde el cotizador')