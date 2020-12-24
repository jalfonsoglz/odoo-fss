# -*- coding: utf-8 -*-

from odoo import api, fields, models
#from odoo.exceptions import UserError

class Quotation(models.Model):
    _name = "quote.quotation_line"
    _description = "Linea de cotización"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = 'id desc, create_date desc'
    _check_company_auto = True

    quotation_id = fields.Many2one('quote.quotation',
                               string = 'Referencia de cotización',
                               required = True,
                               ondelete = 'cascade',
                               index = True)

    product = fields.Many2one('product.product',
                                 string = 'Producto',
                                 change_default = True,
                                 ondelete = 'restrict')

    name = fields.Text('Descripcion',
                       required=True)

    vendor = fields.Many2one('product.supplierinfo',
                             store=True,
                             string = 'Proveedor',
                             ondelete = 'restrict')

    price_unit = fields.Float('Precio',
                              required=True,
                              digits='Product price',
                              default = 0.0)

    product_qty = fields.Float(string = 'Qty',
                               digits = 'Product Unit of Measure',
                               required = True,
                               default = 1.0)

    price_total = fields.Monetary(compute='_compute_amount',
                                  string='Sub total',
                                  store=True)

    currency_id = fields.Many2one(related='quotation_id.currency_id',
                                  depends=['quotation_id'],
                                  store = True,
                                  string = 'Moneda',
                                  readonly = True)

    commitment_date = fields.Datetime('Fecha de entrega',
                                      required=True)

    @api.depends('price_unit', 'product_qty')
    def _compute_amount(self):
        for line in self:
            line.update({
                'price_total' : line.price_unit * line.product_qty
            })

    @api.onchange('product')
    def _onchange_product(self):
        self.vendor = False
        if self.product:
            self.name = self.product.name
            return {'domain':{'vendor':[('product_tmpl_id', '=', self.product.seller_ids.product_tmpl_id.id)]}}
        else:
            self.name = False
            return {'domain':{'vendor':[]}}

    @api.onchange('vendor')
    def _onchange_vendor(self):
        if self.vendor:
            self.price_unit = self.vendor.price
        else:
            self.price_unit = 0.0
