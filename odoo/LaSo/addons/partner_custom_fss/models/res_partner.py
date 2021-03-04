# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_name(self):
        """ Utility method to allow name_get to be overrided without re-browse the partner """
        partner = self
        name = super(ResPartner, self)._get_name()
        if self._context.get('show_ref') and partner.ref:
            name = "%s ‒ %s" % (name, partner.ref)
        return name
