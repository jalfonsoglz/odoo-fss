# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_order_uuid = fields.Char('UUID', readonly=True,
        states={'draft': [('readonly', False)]})

    @api.constrains('purchase_order_uuid')
    def validate_uuid(self):
        uuid_pattern = r"[a-f0-9A-F]{8}-[a-f0-9A-F]{4}-[a-f0-9A-F]{4}-[a-f0-9A-F]{4}-[a-f0-9A-F]{12}"
        for record in self.filtered('purchase_order_uuid'):
            if not re.search(uuid_pattern, record.purchase_order_uuid):
                raise ValidationError("El UUID no parece ser valido !")

            he = self.env['hr.expense'].search([('hr_expense_uuid','=ilike', record.purchase_order_uuid)], limit=1)
            if he:
                raise ValidationError("UUID usado en Gasto %s !"%he.name)
            am = self.env['account.move'].search([('account_move_uuid','=ilike',record.purchase_order_uuid)], limit=1)
            if am:
                raise ValidationError("UUID usado en Factura %s !"%am.name)

    _sql_constraints = [
        ('purchase_order_uuid_unique', 'unique (purchase_order_uuid)', "El UUID ya existe !"),
    ]
