# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    margin_percent = fields.Float(string="Margin(%)", compute='_product_margin_percent')
    requisitor_ref = fields.Char(string = 'Número de Solicitud de Requisitor', copy = False)

    @api.depends('margin','amount_total')
    def _product_margin_percent(self):
        for order in self:
            order.margin_percent = order.margin / order.amount_total if order.amount_total else 0.0

    def action_quotation_sent(self):
        for order in self:
            self.env['quote.quotation'].search([('order_id','=',order.id),('state','=','review')]).write({'state':'sent'})
        return super(SaleOrder, self).action_quotation_sent()

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            quotes = self.env['quote.quotation'].search([('order_id','=',order.id)])
            for lead in quotes.mapped('opportunity_id'):
                lead.action_set_won_rainbowman()

            for quote in quotes.filtered(lambda r: r.state in ['review','sent']):
                quote._action_approve()

    def action_confirm_from_quote(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            quotes = self.env['quote.quotation'].search([('order_id','=',order.id)])
            for lead in quotes.mapped('opportunity_id'):
                lead.action_set_won_rainbowman()
        return res

    def write(self, values):
        print('write::values', values)
        return super(SaleOrder, self).write(values)