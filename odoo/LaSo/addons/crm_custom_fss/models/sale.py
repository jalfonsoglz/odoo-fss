# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        for oppor in self.mapped('opportunity_id'):
            oppor.action_set_won_rainbowman()
        return super(SaleOrder, self).action_confirm()
