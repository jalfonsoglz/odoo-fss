# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccoutMove(models.Model):
    _inherit = 'account.move'

    account_move_uuid = fields.Char('UUID', readonly=True,
        states={'draft': [('readonly', False)]})

    @api.constrains('account_move_uuid')
    def validate_uuid(self):
        uuid_pattern = r"[a-f0-9A-F]{8}-[a-f0-9A-F]{4}-[a-f0-9A-F]{4}-[a-f0-9A-F]{4}-[a-f0-9A-F]{12}"
        for record in self.filtered('account_move_uuid'):
            if not re.search(uuid_pattern, record.account_move_uuid):
                raise ValidationError("El UUID no parece ser valido !")

            he = self.env['hr.expense'].search([('hr_expense_uuid','=ilike', record.account_move_uuid)], limit=1)
            if he:
                raise ValidationError("UUID usado en Gasto %s !"%he.name)
            po = self.env['purchase.order'].search([('purchase_order_uuid','=ilike',record.account_move_uuid)], limit=1)
            if po:
                raise ValidationError("UUID usado en Compra %s !"%po.name)

    _sql_constraints = [
        ('account_move_uuid_unique', 'unique (account_move_uuid)', "El UUID ya existe !"),
    ]
