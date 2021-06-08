# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class Lead(models.Model):
    _inherit = "crm.lead"

    sequence = fields.Char(string = 'Folio',
                             required = True,
                             readonly = True,
                             index = True,
                             copy = False,
                             default=lambda self: _('New'))
    quote_count = fields.Integer(compute='_compute_quote_count', string="Number of Qoutes")
    quote_ids = fields.One2many('quote.quotation', 'opportunity_id', string='Qoutes')

    @api.depends('quote_ids')
    def _compute_quote_count(self):
        for lead in self:
            lead.quote_count = len(lead.quote_ids)

    def action_view_sale_quote(self):
        action = self.env.ref('quote.quotation_menu_action').read()[0]
        action['context'] = {
            'default_customer': self.partner_id.id,
            'default_opportunity_id': self.id
        }
        action['domain'] = [('opportunity_id', '=', self.id)]
        quotes = self.mapped('quote_ids')
        if len(quotes) == 1:
            action['views'] = [(self.env.ref('quote.view_quote_form').id, 'form')]
            action['res_id'] = quotes.id
        return action

    @api.model
    def create(self, vals):
        if vals.get('sequence', _('New')) == _('New'):
            seq_date = None
            if 'date_open' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_open']))
            if 'company_id' in vals:
                vals['sequence'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'crm.lead', sequence_date=seq_date) or _('New')
            else:
                vals['sequence'] = self.env['ir.sequence'].next_by_code('crm.lead', sequence_date=seq_date) or _('New')
        return super(Lead, self).create(vals)
