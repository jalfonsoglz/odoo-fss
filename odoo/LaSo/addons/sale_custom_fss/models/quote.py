# -*- coding: utf-8 -*-

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _

class Quotation(models.Model):
    _inherit = "quote.quotation"

    state = fields.Selection(selection_add=[('sent', 'Enviada'),('approved', 'Aprobada'),('done', 'Completada')])
    customer_po = fields.Char(string = 'OC de cliente',
                              required = False,
                              readonly = False,
                              states = {'done': [('readonly', True)]},
                              index = True)
    sequence = fields.Char(string = 'Folio',
                             required = True,
                             readonly = True,
                             index = True,
                             copy = False,
                             default=lambda self: _('New'))
    requisitor_ref = fields.Char(string = 'Número de Solicitud de Requisitor',
                             copy = False,
                             states = {'done': [('readonly', True)]},)

    order_id = fields.Many2one('sale.order',
                               string = 'Presupuesto',
                               readonly = True,
                               copy = False,
                               index = True)

    po_count = fields.Integer(string='Purchase Orders', compute='_compute_purchase_order')

    opportunity_id = fields.Many2one(
        'crm.lead', string='Opportunity', domain="[('type', '=', 'opportunity')]", copy = False)

    user_id = fields.Many2one('res.users', string='Responsable', index=True, tracking=True)
    with_standard_price = fields.Boolean(compute='_compute_with_standard_price')

    account_id = fields.Many2one('account.account', string='Cuenta Contable',
        domain=[('deprecated', '=', False)], ondelete='restrict')
    partner_shipping_id = fields.Many2one('res.partner',
        string='Dirección de Entrega',
        readonly=False,
        states = {'approved': [('readonly', True)], 'done': [('readonly', True)]},)
    delivery_date = fields.Date(
        string='Fecha de Entrega a Cliente',
        readonly=False,
        states = {'approved': [('readonly', True)], 'done': [('readonly', True)]},)

    @api.depends('quote_line','quote_line.price_unit')
    def _compute_with_standard_price(self):
        for record in self:
            record.with_standard_price = record.quote_line and all(record.quote_line.mapped('price_unit'))

    def _compute_purchase_order(self):
        for order in self:
            order.po_count = len(self.env['purchase.order'].search([('origin','=',order.sequence)]))

    def action_create_order(self):
        for quote in self:
            order = self.env['sale.order'].create({
                'partner_id': quote.customer.id,
                'partner_invoice_id': quote.customer.id,
                'partner_shipping_id': quote.customer.id,
                'quote_id': quote.id,
                'origin': quote.sequence,
                'client_order_ref': quote.customer_po,
                'requisitor_ref': quote.requisitor_ref,
                #'pricelist_id': self.pricelist.id,
                'order_line': [(0, 0, {
                    'name': line.name,
                    'product_id': line.product.id,
                    'product_uom_qty': line.product_qty,
                    'product_uom': line.product.uom_id.id,
                    'purchase_price': line.price_unit,
                }) for line in quote.quote_line],
            })
            quote.order_id = order.id
            order.message_post_with_view('mail.message_origin_link',
                    values={'self': order, 'origin': quote},
                    subtype_id=self.env.ref('mail.mt_note').id)


    def action_view_purchase(self):
        action = self.env.ref('purchase.purchase_rfq').read()[0]

        purchases = self.env['purchase.order'].search([('origin','=',self.sequence)])

        if len(purchases) > 1:
            action['domain'] = [('id', 'in', purchases.ids)]
        elif purchases:
            form_view = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = purchases.id
        return action

    def _action_approve(self):
        orders = 0
        msj = "<h3><b>¡La cotización ha sido aprobada!</b></h3>"
        for line in self.quote_line:
            if line.product.product_tmpl_id.employee == False:

                order = self.env['purchase.order']
                purchase = order.create({
                    'partner_id': line.vendor.name.id,
                    'currency_id': line.currency_id.id,
                    #'origin': line.quotation_id.name,
                    'origin': line.quotation_id.sequence,
                    'order_line': [(0,0,{
                        'product_id':line.product.id,
                        'name': line.name,
                        'product_qty': line.product_qty,
                        'price_unit': line.price_unit,
                        'date_planned': line.commitment_date,
                        'product_uom':line.product.uom_id.id,
                        'account_analytic_id': self.account_analytic_id.id
                    })]
                })
                purchase.message_post_with_view('mail.message_origin_link',
                    values={'self': purchase, 'origin': line.quotation_id},
                    subtype_id=self.env.ref('mail.mt_note').id)
                if self.user_id:
                    purchase.user_id = self.user_id
                orders+=1
        if orders > 1:
            msj += "<b><h4>" + str(orders) + " Solicitudes de compra generadas</h4></b>"
        else:
            msj += "<b><h4>Se generó una solicitud de compra</h4></b>"
        for quote in self:
            quote.message_post(body=msj)
        self.state = 'approved'

    def action_approve(self):
        self.filtered(lambda r: r.state in ('review','sent'))._action_approve()
        sale_order_to_confirm = self.mapped('order_id').filtered(lambda r: r.state in ['draft','sent'])
        sale_order_to_confirm.action_confirm()

        for lead in self.mapped('opportunity_id'):
            lead.action_set_won_rainbowman()

    def button_request_price(self):
        for quote in self.filtered('user_id'):
            self.env['mail.activity'].create({
                'summary': 'Solicitud de precio:%s'%quote.name,
                'date_deadline': date.today() + relativedelta(days=1),
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'user_id': quote.user_id.id,
                'res_model_id': self.env['ir.model']._get(self._name).id,
                'res_id': quote.id,
            })
        self.state = 'review'

    @api.model
    def create(self, vals):
        if vals.get('sequence', _('New')) == _('New'):
            seq_date = None
            if 'quote_date' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['quote_date']))
            if 'company_id' in vals:
                vals['sequence'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'quote.quotation', sequence_date=seq_date) or _('New')
            else:
                vals['sequence'] = self.env['ir.sequence'].next_by_code('quote.quotation', sequence_date=seq_date) or _('New')
        return super(Quotation, self).create(vals)
