# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Quotation(models.Model):
    _name = "quote.quotation"
    _description = "Cotización"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = 'id desc, create_date desc'
    _check_company_auto = True

    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('review', 'Revisión'),
            ('approved', 'Aprobada')
        ],
        string='Estatus',
        copy=False,
        index=True,
        default='draft',
        track_visibility = 'onchange')

    name = fields.Char(string = 'Número de cotización',
                             required = True,
                             readonly = True,
                             states = {'draft' : [('readonly', False)]},
                             index = True)

    quote_date = fields.Datetime(string = 'Fecha de cotización',
                                 required = True,
                                 readonly = True,
                                 index = True,
                                 default = fields.Datetime.now,
                                 help = 'Fecha de creación de la cotización')

    customer_po = fields.Char(string = 'OC de cliente',
                              required = True,
                              readonly = True,
                              states = {'draft': [('readonly', False)]},
                              index = True)

    customer = fields.Many2one('res.partner',
                               string = 'Cliente',
                               readonly = True,
                               states = {'draft': [('readonly', False)]},
                               required = True,
                               change_default = True,
                               index = True)

    currency_id = fields.Many2one('res.currency',
                                  string = 'Moneda',
                                  required = True)

    quote_budget = fields.Monetary(string = 'Presupuesto',
                                   store = True,
                                   readonly = True,
                                   required=True,
                                   states = {'draft':[('readonly',False)]},
                                   track_visibility = 'onchange')

    amount_total = fields.Monetary(string = 'Total',
                                   store = True,
                                   readonly = True,
                                   compute = '_amount_all',
                                   track_visibility = 'onchange')

    account_analytic_id = fields.Many2one('account.analytic.account',
                                          string='Cuenta analítica')

    note = fields.Text('Notas')

    quote_line = fields.One2many('quote.quotation_line', 'quotation_id',
                                 string='Lineas de la cotización',
                                 readonly=False,
                                 copy=True,
                                 states = {'approved':[('readonly',True)]},
                                 auto_join=True)

    @api.depends('quote_line.price_total')
    def _amount_all(self):
        for quote in self:
            amount = 0.0
            for line in quote.quote_line:
                amount += line.price_total
            quote.update({
                'amount_total': amount
            })

    def action_approve(self):
        self.state = 'approved'
        orders = 0
        msj = "<h3><b>¡La cotización ha sido aprobada!</b></h3>"
        for line in self.quote_line:
            if line.product.product_tmpl_id.employee == False:

                order = self.env['purchase.order']
                purchase = order.create({
                    'partner_id': line.vendor.name.id,
                    'currency_id': line.currency_id.id,
                    'origin': line.quotation_id.name,
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
                orders+=1
        if orders > 1:
            msj += "<b><h4>" + str(orders) + " Solicitudes de compra generadas</h4></b>"
        else:
            msj += "<b><h4>Se generó una solicitud de compra</h4></b>"

        self.message_post(body=msj)

    def action_review(self):
        self.state = 'review'
