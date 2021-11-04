# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date, datetime
from dateutil.relativedelta import relativedelta


from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sale_type = fields.Selection(
        [
            ('fix', 'Servicio Fijo'),
            ('supply', 'Suministro'),
            ('construction', 'Obra'),
            ('extra_time', 'Tiempo Extra'),
            ('project', 'Proyectos'),
        ],
        string='Tipo de Cotización', readonly=True, copy=False,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
    )

    margin_percent = fields.Float(string="Margin(%)", compute='_product_margin_percent')
    requisitor_ref = fields.Char(string = 'Número de Solicitud de Requisitor', copy = False)
    is_shipped = fields.Boolean(compute="_compute_is_shipped", store=True, copy = False)
    quote_id = fields.Many2one('quote.quotation', string='Documento Origen', readonly=True, ondelete='restrict', index=True, copy=False)

    @api.depends('picking_ids', 'picking_ids.state')
    def _compute_is_shipped(self):
        for order in self:
            if order.picking_ids and all([x.state in ['done', 'cancel'] for x in order.picking_ids]):
                order.is_shipped = True
                quotes = self.env['quote.quotation'].search([('order_id','=',order.id),('state','=','approved')])
                quotes.write({'state':'done'})
                billing_manager_id = self.env['ir.config_parameter'].sudo().get_param('sale_custom_fss.user_billing_manager_id')
                billing_manager = self.env['res.users'].browse(int(billing_manager_id)).exists()
                if billing_manager:
                    for quote in quotes:
                        self.env['mail.activity'].create({
                            'summary': 'Facturar:%s'%order.name,
                            'date_deadline': date.today() + relativedelta(days=2),
                            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                            'user_id': billing_manager.id,
                            'res_model_id': self.env['ir.model']._get(order._name).id,
                            'res_id': order.id,
                        })
            else:
                order.is_shipped = False

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
            quotes = self.env['quote.quotation'].search([('order_id','=',order.id),('state','in',['sent','review'])])
            quotes.action_approve()

    def action_confirm_from_quote(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            quotes = self.env['quote.quotation'].search([('order_id','=',order.id)])
            for lead in quotes.mapped('opportunity_id'):
                lead.action_set_won_rainbowman()
        return res
