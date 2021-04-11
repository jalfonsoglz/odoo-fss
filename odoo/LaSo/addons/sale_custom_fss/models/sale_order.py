# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    margin_percent = fields.Float(string="Margin(%)", compute='_product_margin_percent')

    @api.depends('margin','amount_total')
    def _product_margin_percent(self):
        for order in self:
            order.margin_percent = order.margin / order.amount_total if order.amount_total else 0.0
