# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    hr_expense_uuid = fields.Char('UUID', readonly=True,
        states={'draft': [('readonly', False)]})

    @api.constrains('hr_expense_uuid')
    def validate_uuid(self):
        uuid_pattern = r"[a-f0-9A-F]{8}-[a-f0-9A-F]{4}-[a-f0-9A-F]{4}-[a-f0-9A-F]{4}-[a-f0-9A-F]{12}"
        for record in self.filtered('hr_expense_uuid'):
            if not re.search(uuid_pattern, record.hr_expense_uuid):
                raise ValidationError("El UUID no parece ser valido !")

            po = self.env['purchase.order'].search([('purchase_order_uuid','=ilike', record.hr_expense_uuid)], limit=1)
            if po:
                raise ValidationError("UUID usado en Compra %s !"%po.name)
            am = self.env['account.move'].search([('account_move_uuid','=ilike',record.hr_expense_uuid)], limit=1)
            if am:
                raise ValidationError("UUID usado en Factura %s !"%am.name)

    _sql_constraints = [
        ('hr_expense_uuid_unique', 'unique (hr_expense_uuid)', "El UUID ya existe !"),
    ]
