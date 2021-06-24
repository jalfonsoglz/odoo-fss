# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    user_billing_manager_id = fields.Many2one(
        'res.users',
        'Billing manager(Quote)',
        config_parameter='sale_custom_fss.user_billing_manager_id')