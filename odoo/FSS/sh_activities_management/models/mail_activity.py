# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, modules, exceptions, _
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import clean_context
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import html2plaintext
import math

class MailActivityMixin(models.AbstractModel):
    _inherit = 'mail.activity.mixin'

    def _read_progress_bar(self, domain, group_by, progress_bar):
        group_by_fname = group_by.partition(':')[0]
        if not (progress_bar['field'] == 'activity_state' and self._fields[group_by_fname].store):
            return super()._read_progress_bar(domain, group_by, progress_bar)

        # optimization for 'activity_state'

        # explicitly check access rights, since we bypass the ORM
        self.check_access_rights('read')
        self._flush_search(domain, fields=[group_by_fname], order='id')
        self.env['mail.activity'].flush(['res_model', 'res_id', 'user_id', 'date_deadline'])

        query = self._where_calc(domain)
        self._apply_ir_rules(query, 'read')
        gb = group_by.partition(':')[0]
        annotated_groupbys = [
            self._read_group_process_groupby(gb, query)
            for gb in [group_by, 'activity_state']
        ]
        groupby_dict = {gb['groupby']: gb for gb in annotated_groupbys}
        for gb in annotated_groupbys:
            if gb['field'] == 'activity_state':
                gb['qualified_field'] = '"_last_activity_state"."activity_state"'
        groupby_terms, orderby_terms = self._read_group_prepare('activity_state', [], annotated_groupbys, query)
        select_terms = [
            '%s as "%s"' % (gb['qualified_field'], gb['groupby'])
            for gb in annotated_groupbys
        ]
        from_clause, where_clause, where_params = query.get_sql()
        tz = self._context.get('tz') or self.env.user.tz or 'UTC'
        select_query = """
            SELECT 1 AS id, count(*) AS "__count", {fields}
            FROM {from_clause}
            JOIN (
                SELECT res_id,
                CASE
                    WHEN min(date_deadline - (now() AT TIME ZONE COALESCE(res_partner.tz, %s))::date) > 0 THEN 'planned'
                    WHEN min(date_deadline - (now() AT TIME ZONE COALESCE(res_partner.tz, %s))::date) < 0 THEN 'overdue'
                    WHEN min(date_deadline - (now() AT TIME ZONE COALESCE(res_partner.tz, %s))::date) = 0 THEN 'today'
                    ELSE null
                END AS activity_state
                FROM mail_activity
                JOIN res_users ON (res_users.id = mail_activity.user_id)
                JOIN res_partner ON (res_partner.id = res_users.partner_id)
                WHERE res_model = '{model}' and mail_activity.active = True
                GROUP BY res_id
            ) AS "_last_activity_state" ON ("{table}".id = "_last_activity_state".res_id)
            WHERE {where_clause}
            GROUP BY {group_by}
        """.format(
            fields=', '.join(select_terms),
            from_clause=from_clause,
            model=self._name,
            table=self._table,
            where_clause=where_clause or '1=1',
            group_by=', '.join(groupby_terms),
        )
        self.env.cr.execute(select_query, [tz] * 3 + where_params)
        fetched_data = self.env.cr.dictfetchall()
        self._read_group_resolve_many2one_fields(fetched_data, annotated_groupbys)
        data = [
            {key: self._read_group_prepare_data(key, val, groupby_dict)
             for key, val in row.items()}
            for row in fetched_data
        ]
        return [
            self._read_group_format_result(vals, annotated_groupbys, [group_by], domain)
            for vals in data
        ]


class MailActivity(models.Model):
    """ Inherited Mail Acitvity to add custom field"""
    _inherit = 'mail.activity'

    @api.model
    def default_company_id(self):
        return self.env.company

    active = fields.Boolean(default=True)
    supervisor_id = fields.Many2one('res.users',
                                    string="Supervisor",
                                    domain=[('share', '=', False)])
    sh_activity_tags = fields.Many2many("sh.activity.tags",
                                        string='Activity Tags')
    state = fields.Selection(selection_add=[("done", "Done"),
                                            ('cancel', 'Cancelled')],
                             compute="_compute_state",
                             search='_search_state')
    sh_state = fields.Selection(related='state', store=True)
    date_done = fields.Date("Completed Date", index=True, readonly=True)
    feedback = fields.Text("Feedback")

    text_note = fields.Char("Notes In Char format ",
                            compute='get_html_to_char_note')
    sh_user_ids = fields.Many2many('res.users',
                                   string="Assign Multi Users",
                                   domain=[('share', '=', False)])
    sh_display_multi_user = fields.Boolean(
        compute='_compute_sh_display_multi_user')
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 default=default_company_id)
    color = fields.Integer('Color Index', default=0)
    sh_create_individual_activity = fields.Boolean(
        'Individual activities for multi users ?')
    state_compute = fields.Boolean()
    sh_activity_alarm_ids = fields.Many2many('sh.activity.alarm',
                                             string='Reminders')
    sh_date_deadline = fields.Datetime(
        'Reminder Due Date', default=lambda self: fields.Datetime.now())
    activity_cancel = fields.Boolean()
    activity_done = fields.Boolean()

    reference = fields.Reference(string='Related Document',
                                 selection='_reference_models')

    @api.model
    def _reference_models(self):
        models = self.env['ir.model'].sudo().search([('state', '!=', 'manual')
                                                     ])
        return [(model.model, model.name) for model in models
                if not model.model.startswith('ir.')]

    @api.onchange('reference')
    def onchange_reference(self):
        if self.reference:
            if self.reference._name:
                model_id = self.env['ir.model'].sudo().search(
                    [('model', '=', self.reference._name)], limit=1)
                if model_id:
                    self.res_model_id = model_id.id
                    self.res_id = self.reference.id
                    self.res_model = self.reference._name

    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        for activity in self:
            activity.res_name = ''
            if activity.res_model and activity.res_id:
                activity.res_name = self.env[activity.res_model].browse(
                    activity.res_id).name_get()[0][1]

    @api.onchange('state')
    def onchange_state(self):
        self.ensure_one()
        self.activity_done = False
        self.activity_cancel = False
        self._compute_state()

    @api.depends('date_deadline')
    def _compute_state(self):
        res = super(MailActivity, self)._compute_state()
        for record in self.filtered(lambda activity: not activity.active):
            if record.activity_cancel:
                record.state = 'cancel'
            if record.activity_done:
                record.state = 'done'
        return res

    def _search_state(self, operator, value):
        not_done_ids = []
        done_ids = []
        if value == 'done':
            for record in self.sudo().search([('active', '=', False),
                                              ('date_done', '!=', False)]):
                done_ids.append(record.id)
        if value == 'cancel':
            for record in self.sudo().search([('active', '=', False),
                                              ('date_done', '=', False)]):
                done_ids.append(record.id)
        if value == 'today':
            for record in self.sudo().search([('date_deadline', '=',
                                               fields.Date.today())]):
                done_ids.append(record.id)
        if value == 'planned':
            for record in self.sudo().search([('date_deadline', '>',
                                               fields.Date.today())]):
                done_ids.append(record.id)
        if value == 'overdue':
            for record in self.sudo().search([('date_deadline', '<',
                                               fields.Date.today())]):
                done_ids.append(record.id)
        if operator == '=':
            return [('id', 'in', done_ids)]
        elif operator == 'in':
            return [('id', 'in', done_ids)]
        elif operator == '!=':
            return [('id', 'in', not_done_ids)]
        elif operator == 'not in':
            return [('id', 'in', not_done_ids)]
        else:
            return []

    @api.onchange('date_deadline')
    def _onchange_sh_date_deadline(self):
        if self:
            for rec in self:
                if rec.date_deadline:
                    rec.sh_date_deadline = rec.date_deadline + timedelta(
                        hours=0, minutes=0, seconds=0)

    @api.model
    def create(self, vals):
        res = super(MailActivity, self).create(vals)
        if res.sh_user_ids and res.sh_create_individual_activity:
            for user in res.sh_user_ids:
                if res.user_id.id != user.id:
                    self.env['mail.activity'].sudo().create({
                        'res_model_id':
                        res.res_model_id.id,
                        'res_id':
                        res.res_id,
                        'date_deadline':
                        res.date_deadline,
                        'sh_user_ids': [(6, 0, user.ids)],
                        'supervisor_id':
                        res.supervisor_id.id,
                        'activity_type_id':
                        res.activity_type_id.id,
                        'summary':
                        res.summary,
                        'sh_activity_tags': [(6, 0, res.sh_activity_tags.ids)],
                        'sh_activity_alarm_ids':
                        [(6, 0, res.sh_activity_alarm_ids.ids)],
                        'sh_date_deadline':
                        res.sh_date_deadline,
                        'note':
                        res.note,
                    })
        return res

    def write(self, vals):
        if self:
            for rec in self:
                if vals.get('active') and vals.get('active') == True:
                    rec.onchange_state()
                    rec._compute_state()
        return super(MailActivity, self).write(vals)

    def action_cancel(self):
        if self:
            for rec in self:
                rec.state = 'cancel'
                rec.active = False
                rec.date_done = False
                rec.activity_cancel = True
                rec._compute_state()

    def unlink(self):
        for activity in self:
            activity.state = 'cancel'
            activity.active = False
            activity.activity_cancel = True
            activity._compute_state()
        return False

    def unarchive(self, active=True):
        self.ensure_one()
        self.activity_cancel = False
        self.active = True
        self._compute_state()

    @api.depends('company_id')
    def _compute_sh_display_multi_user(self):
        if self:
            for rec in self:
                rec.sh_display_multi_user = False
                if rec.company_id and rec.company_id.sh_display_multi_user:
                    rec.sh_display_multi_user = True

    @api.depends('note')
    def get_html_to_char_note(self):
        if self:
            for rec in self:
                if rec.note:
                    rec.text_note = html2plaintext(rec.note)
                else:
                    rec.text_note = ''

    @api.model
    def notify_mail_activity_fun(self):

        template = self.env.ref(
            'sh_activities_management.template_mail_activity_due_notify_email')
        notify_create_user_template = self.env.ref(
            'sh_activities_management.template_mail_activity_due_notify_email_create_user'
        )
        company_object = self.env['res.company'].search(
            [('activity_due_notification', '=', True)], limit=1)

        if template and company_object and company_object.activity_due_notification:

            activity_obj = self.env['mail.activity'].search([])

            if activity_obj:
                for record in activity_obj:
                    if record.date_deadline and record.user_id and record.user_id.id != self.env.ref(
                            'base.user_root'
                    ).id and record.user_id.partner_id and record.user_id.partner_id.email:

                        # On Due Date
                        if company_object.ondue_date_notify:

                            if datetime.strptime(
                                    str(record.date_deadline),
                                    DEFAULT_SERVER_DATE_FORMAT).date(
                                    ) == datetime.now().date():
                                mail_res = template.send_mail(record.id,
                                                              force_send=True)
                                if notify_create_user_template and company_object.notify_create_user_due:
                                    if record.user_id.id != record.create_uid.id and record.create_uid.id != self.env.ref(
                                            'base.user_root').id:
                                        notify_create_user_template.send_mail(
                                            record.id, force_send=True)
                        # On After First Notify
                        if company_object.after_first_notify and company_object.enter_after_first_notify:
                            after_date = datetime.strptime(
                                str(record.date_deadline),
                                DEFAULT_SERVER_DATE_FORMAT).date() + timedelta(
                                    days=company_object.
                                    enter_after_first_notify)

                            if after_date == datetime.now().date():
                                mail_res = template.send_mail(record.id,
                                                              force_send=True)
                                if notify_create_user_template and company_object.notify_create_user_after_first:
                                    if record.user_id.id != record.create_uid.id and record.create_uid.id != self.env.ref(
                                            'base.user_root').id:
                                        notify_create_user_template.send_mail(
                                            record.id, force_send=True)
                        # On After Second Notify
                        if company_object.after_second_notify and company_object.enter_after_second_notify:
                            after_date = datetime.strptime(
                                str(record.date_deadline),
                                DEFAULT_SERVER_DATE_FORMAT).date() + timedelta(
                                    days=company_object.
                                    enter_after_second_notify)

                            if after_date == datetime.now().date():
                                mail_res = template.send_mail(record.id,
                                                              force_send=True)
                                if notify_create_user_template and company_object.notify_create_user_after_second:
                                    if record.user_id.id != record.create_uid.id and record.create_uid.id != self.env.ref(
                                            'base.user_root').id:
                                        notify_create_user_template.send_mail(
                                            record.id, force_send=True)
                        # On Before First Notify
                        if company_object.before_first_notify and company_object.enter_before_first_notify:
                            before_date = datetime.strptime(
                                str(record.date_deadline),
                                DEFAULT_SERVER_DATE_FORMAT).date() - timedelta(
                                    days=company_object.
                                    enter_before_first_notify)

                            if before_date == datetime.now().date():
                                mail_res = template.send_mail(record.id,
                                                              force_send=True)
                                if notify_create_user_template and company_object.notify_create_user_before_first:
                                    if record.user_id.id != record.create_uid.id and record.create_uid.id != self.env.ref(
                                            'base.user_root').id:
                                        notify_create_user_template.send_mail(
                                            record.id, force_send=True)
                        # On Before Second Notify
                        if company_object.before_second_notify and company_object.enter_before_second_notify:
                            before_date = datetime.strptime(
                                str(record.date_deadline),
                                DEFAULT_SERVER_DATE_FORMAT).date() - timedelta(
                                    days=company_object.
                                    enter_before_second_notify)

                            if before_date == datetime.now().date():
                                mail_res = template.send_mail(record.id,
                                                              force_send=True)
                                if notify_create_user_template and company_object.notify_create_user_before_second:
                                    if record.user_id.id != record.create_uid.id and record.create_uid.id != self.env.ref(
                                            'base.user_root').id:
                                        notify_create_user_template.send_mail(
                                            record.id, force_send=True)

    def action_view_activity(self):
        self.ensure_one()
        try:
            model = self.env[self.res_model].browse(
                self.res_id).check_access_rule('read')
            return {
                'name': 'Origin Activity',
                'res_model': self.res_model,
                'res_id': self.res_id,
                'view_mode': 'form',
                'type': 'ir.actions.act_window',
                'target': 'current',
            }
        except exceptions.AccessError:
            raise exceptions.UserError(
                _('Assigned user %s has no access to the document and is not able to handle this activity.'
                  ) % self.env.user.display_name)

    def action_edit_activity(self):
        self.ensure_one()
        view_id = self.env.ref(
            'sh_activities_management.sh_mail_activity_type_view_form_inherit'
        ).id
        return {
            'name': _('Schedule an Activity'),
            'view_mode': 'form',
            'res_model': 'mail.activity',
            'views': [(view_id, 'form')],
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_done(self):
        """ Wrapper without feedback because web button add context as
        parameter, therefore setting context to feedback """
        return {
            'name': 'Activity Feedback',
            'res_model': 'activity.feedback',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'context': {
                'default_done_button_pressed': True
            },
            'target': 'new',
        }

    def action_done_from_popup(self, feedback=False):
        self.ensure_one()
        messages, next_activities = self._action_done()
        self.state = 'done'
        self.active = False
        self.feedback = feedback
        self.activity_done = True
        if self.state == 'done':
            self.date_done = fields.Date.today()
        self._compute_state()
#         return messages.ids and messages.ids[0] or False

    def _action_done(self, feedback=False, attachment_ids=None):
        self.ensure_one()
        """ Private implementation of marking activity as done: posting a message, deleting activity
            (since done), and eventually create the automatical next activity (depending on config).
            :param feedback: optional feedback from user when marking activity as done
            :param attachment_ids: list of ir.attachment ids to attach to the posted mail.message
            :returns (messages, activities) where
                - messages is a recordset of posted mail.message
                - activities is a recordset of mail.activity of forced automically created activities
        """
        # marking as 'done'
        messages = self.env['mail.message']
        next_activities_values = []
        for activity in self:
            # extract value to generate next activities
            if activity.force_next:
                Activity = self.env['mail.activity'].sudo().with_context(
                    activity_previous_deadline=activity.date_deadline
                )  # context key is required in the onchange to set deadline
                vals = Activity.default_get(Activity.fields_get())

                vals.update({
                    'previous_activity_type_id':
                    activity.activity_type_id.id,
                    'res_id':
                    activity.res_id,
                    'res_model':
                    activity.res_model,
                    'res_model_id':
                    self.env['ir.model']._get(activity.res_model).id,
                })
                virtual_activity = Activity.sudo().new(vals)
                virtual_activity._onchange_previous_activity_type_id()
                virtual_activity._onchange_activity_type_id()
                next_activities_values.append(
                    virtual_activity._convert_to_write(
                        virtual_activity._cache))

            # post message on activity, before deleting it
            record = self.env[activity.res_model].sudo().browse(
                activity.res_id)
            record.sudo().message_post_with_view(
                'mail.message_activity_done',
                values={
                    'activity': activity,
                    'feedback': feedback,
                    'display_assignee': activity.user_id != self.env.user
                },
                subtype_id=self.env['ir.model.data'].xmlid_to_res_id(
                    'mail.mt_activities'),
                mail_activity_type_id=activity.activity_type_id.id,
                attachment_ids=[
                    (4, attachment_id) for attachment_id in attachment_ids
                ] if attachment_ids else [],
            )
            messages |= record.sudo().message_ids[0]

        next_activities = self.env['mail.activity'].sudo().create(
            next_activities_values)
        self.active = False
        self.date_done = fields.Date.today()
        self.activity_done = True
        self.feedback = feedback
        self.state = "done"
        self._compute_state()
        #         self.unlink()  # will unlink activity, dont access `self` after that

        return messages, next_activities

    def action_done_schedule_next(self):
        """ Wrapper without feedback because web button add context as
        parameter, therefore setting context to feedback """
        return {
            'name': 'Activity Feedback',
            'res_model': 'activity.feedback',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'context': {
                'default_done_button_pressed': False
            },
            'target': 'new',
        }


#         return self.action_feedback_schedule_next()

    def action_feedback_schedule_next(self, feedback=False):
        ctx = dict(
            clean_context(self.env.context),
            default_previous_activity_type_id=self.activity_type_id.id,
            activity_previous_deadline=self.date_deadline,
            default_res_id=self.res_id,
            default_res_model=self.res_model,
        )
        view_id = self.env.ref(
            'sh_activities_management.sh_mail_activity_type_view_form_inherit'
        ).id
        messages, next_activities = self._action_done(
            feedback=feedback
        )  # will unlink activity, dont access self after that
        if next_activities:
            return False
        return {
            'name': _('Schedule an Activity'),
            'context': ctx,
            'view_mode': 'form',
            'res_model': 'mail.activity',
            'views': [(view_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def systray_get_activities(self):
        query = """SELECT m.id, count(*), act.res_model as model,
                        CASE
                            WHEN %(today)s::date - act.date_deadline::date = 0 Then 'today'
                            WHEN %(today)s::date - act.date_deadline::date > 0 Then 'overdue'
                            WHEN %(today)s::date - act.date_deadline::date < 0 Then 'planned'
                        END AS states
                    FROM mail_activity AS act
                    JOIN ir_model AS m ON act.res_model_id = m.id
                    WHERE user_id = %(user_id)s and active=true
                    GROUP BY m.id, states, act.res_model;
                    """
        self.env.cr.execute(query, {
            'today': fields.Date.context_today(self),
            'user_id': self.env.uid,
        })
        activity_data = self.env.cr.dictfetchall()
        model_ids = [a['id'] for a in activity_data]
        model_names = {
            n[0]: n[1]
            for n in self.env['ir.model'].browse(model_ids).name_get()
        }
    
        user_activities = {}
        for activity in activity_data:
            if not user_activities.get(activity['model']):
                module = self.env[activity['model']]._original_module
                icon = module and modules.module.get_module_icon(module)
                user_activities[activity['model']] = {
                    'name': model_names[activity['id']],
                    'model': activity['model'],
                    'type': 'activity',
                    'icon': icon,
                    'total_count': 0,
                    'today_count': 0,
                    'overdue_count': 0,
                    'planned_count': 0,
                }
    
            user_activities[activity['model']][
                '%s_count' % activity['states']] += activity['count']
            if activity['states'] in ('today', 'overdue'):
                user_activities[
                    activity['model']]['total_count'] += activity['count']
    
            user_activities[activity['model']]['actions'] = [{
                'icon': 'fa-clock-o',
                'name': 'Summary',
            }]
        activities = list(user_activities.values())
        if self.env['ir.module.module'].sudo().search([('name', '=', 'note'),
                                                       ('state', '=',
                                                        'installed')]):
            notes_count = self.env['note.note'].search_count([('user_id', '=',
                                                               self.env.uid)])
    
            if notes_count:
                note_index = next((index
                                   for (index, a) in enumerate(activities)
                                   if a["model"] == "note.note"), None)
                note_label = _('Notes')
                if note_index is not None:
                    activities[note_index]['name'] = note_label
                else: 
                    activities.append({
                        'type':
                        'activity',
                        'name':
                        note_label,
                        'model':
                        'note.note',
                        'icon':
                        modules.module.get_module_icon(
                            self.env['note.note']._original_module),
                        'total_count':
                        0,
                        'today_count':
                        0,
                        'overdue_count':
                        0,
                        'planned_count':
                        0
                    })
        if self.env['ir.module.module'].sudo().search([('name', '=', 'calendar'),('state', '=','installed')]):
            meetings_lines = self.env['calendar.event'].search_read(
                self._systray_get_calendar_event_domain(),
                ['id', 'start', 'name', 'allday', 'attendee_status'],
                order='start')
            meetings_lines = [line for line in meetings_lines if line['attendee_status'] != 'declined']
            if meetings_lines:
                meeting_label = _("Today's Meetings")
                meetings_systray = {
                    'type': 'meeting',
                    'name': meeting_label,
                    'model': 'calendar.event',
                    'icon': modules.module.get_module_icon(self.env['calendar.event']._original_module),
                    'meetings': meetings_lines,
                }
                activities.insert(0, meetings_systray)
        for activity in activities:
            if activity['model'] != 'res.partner':
                continue
            activity['icon'] = '/sh_activities_management/static/description/contacts_icon.png'
        return activities

    

class ActivityDashboard(models.Model):
    _name = 'activity.dashboard'
    _description = 'Activity Dashboard'

    @api.model
    def get_sh_crm_activity_planned_count_tbl(self, filter_date, filter_user,
                                              start_date, end_date,
                                              filter_supervisor, filter_model,
                                              filter_record):

        doman = []

        crm_days_filter = filter_date
        custom_date_start = start_date
        custom_date_end = end_date
        if crm_days_filter == 'today':

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            dt_flt1.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))
        elif crm_days_filter == 'yesterday':

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            prev_day = (datetime.now().date() -
                        relativedelta(days=1)).strftime('%Y/%m/%d')
            dt_flt1.append(prev_day)
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            prev_day = (datetime.now().date() -
                        relativedelta(days=1)).strftime('%Y/%m/%d')
            dt_flt2.append(prev_day)
            doman.append(tuple(dt_flt2))
        elif crm_days_filter == 'weekly':  # current week

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append(
                (datetime.now().date() -
                 relativedelta(weeks=1, weekday=0)).strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'prev_week':  # Previous week

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append(
                (datetime.now().date() -
                 relativedelta(weeks=2, weekday=0)).strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(
                (datetime.now().date() -
                 relativedelta(weeks=1, weekday=6)).strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'monthly':  # Current Month

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date()).strftime("%Y/%m/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'prev_month':  # Previous Month

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date() -
                            relativedelta(months=1)).strftime("%Y/%m/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/01"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'cur_year':  # Current Year

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date()).strftime("%Y/01/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'prev_year':  # Previous Year

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date() -
                            relativedelta(years=1)).strftime("%Y/01/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/01/01"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'custom':
            if custom_date_start and custom_date_end:

                dt_flt1 = []
                dt_flt1.append('date_deadline')
                dt_flt1.append('>')
                dt_flt1.append(
                    datetime.strptime(
                        str(custom_date_start),
                        DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d"))
                doman.append(tuple(dt_flt1))

                dt_flt2 = []
                dt_flt2.append('date_deadline')
                dt_flt2.append('<=')
                dt_flt2.append(
                    datetime.strptime(
                        str(custom_date_end),
                        DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d"))
                doman.append(tuple(dt_flt2))

#         doman = []
# FILTER USER
        if filter_user not in ['', "", None, False]:
            doman.append(('|'))
            doman.append(('sh_user_ids', 'in', [int(filter_user)]))
            doman.append(('user_id', '=', int(filter_user)))
        else:
            if self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('user_id', '!=', self.env.user.id))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))

            elif self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == False and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))
                doman.append(('user_id', '=', self.env.user.id))
        if filter_supervisor not in ['', "", None, False]:
            doman.append(('supervisor_id', '=', int(filter_supervisor)))
        else:
            if self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('supervisor_id', '=', self.env.user.id))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))
            elif self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == False and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('supervisor_id', '=', self.env.user.id))
                doman.append(('supervisor_id', '!=', self.env.user.id))
                doman.append(('supervisor_id', '=', False))
        doman.append(('|'))
        doman.append(('active', '=', True))
        doman.append(('active', '=', False))
        if filter_model not in ['', "", None, False]:
            if filter_record not in ['', "", None, False]:
                doman.append(('res_id', '=', filter_record))
                doman.append(('res_model_id', '=', int(filter_model)))
            else:
                doman.append(('res_model_id', '=', int(filter_model)))
        activities = self.env['mail.activity'].search(doman,
                                                      limit=False,
                                                      order='res_id desc')
        planned_activities = activities.filtered(
            lambda x: x.active and x.date_deadline and x.date_deadline >=
            fields.Date.today()).ids
        overdue_activities = activities.filtered(
            lambda x: x.active and x.date_deadline and x.date_deadline < fields
            .Date.today()).ids
        all_activities = activities.ids
        completed_activities = activities.filtered(
            lambda x: not x.active and x.state == 'done').ids
        cancelled_activities = activities.filtered(
            lambda x: not x.active and x.state == 'cancel').ids
        return self.env['ir.ui.view'].with_context().render_template(
            'sh_activities_management.sh_crm_db_activity_count_box', {
                'planned_activities': planned_activities,
                'overdue_activities': overdue_activities,
                'all_activities': all_activities,
                'completed_activities': completed_activities,
                'planned_acitvities_count': len(planned_activities),
                'overdue_activities_count': len(overdue_activities),
                'completed_activities_count': len(completed_activities),
                'cancelled_activities_count': len(cancelled_activities),
                'cancelled_activities': cancelled_activities,
                'all_activities_count': len(activities.ids),
            })

    @api.model
    def get_sh_crm_activity_todo_tbl(self, filter_date, filter_user,
                                     start_date, end_date, filter_supervisor,
                                     current_page, filter_model,
                                     filter_record):
        doman = [('active', '=', True),
                 ('date_deadline', '>=', fields.Date.today())]
        crm_days_filter = filter_date
        custom_date_start = start_date
        custom_date_end = end_date
        if crm_days_filter == 'today':

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            dt_flt1.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))
        elif crm_days_filter == 'yesterday':

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            prev_day = (datetime.now().date() -
                        relativedelta(days=1)).strftime('%Y/%m/%d')
            dt_flt1.append(prev_day)
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            prev_day = (datetime.now().date() -
                        relativedelta(days=1)).strftime('%Y/%m/%d')
            dt_flt2.append(prev_day)
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'weekly':  # current week

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append(
                (datetime.now().date() -
                 relativedelta(weeks=1, weekday=0)).strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'prev_week':  # Previous week

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append(
                (datetime.now().date() -
                 relativedelta(weeks=2, weekday=0)).strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(
                (datetime.now().date() -
                 relativedelta(weeks=1, weekday=6)).strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'monthly':  # Current Month

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date()).strftime("%Y/%m/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'prev_month':  # Previous Month

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date() -
                            relativedelta(months=1)).strftime("%Y/%m/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/01"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'cur_year':  # Current Year

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date()).strftime("%Y/01/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'prev_year':  # Previous Year

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date() -
                            relativedelta(years=1)).strftime("%Y/01/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/01/01"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'custom':
            if custom_date_start and custom_date_end:

                dt_flt1 = []
                dt_flt1.append('date_deadline')
                dt_flt1.append('>')
                dt_flt1.append(
                    datetime.strptime(
                        str(custom_date_start),
                        DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d"))
                doman.append(tuple(dt_flt1))

                dt_flt2 = []
                dt_flt2.append('date_deadline')
                dt_flt2.append('<=')
                dt_flt2.append(
                    datetime.strptime(
                        str(custom_date_end),
                        DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d"))
                doman.append(tuple(dt_flt2))

#         doman = []
# FILTER USER
        if filter_user not in ['', "", None, False]:
            doman.append(('|'))
            doman.append(('sh_user_ids', 'in', [int(filter_user)]))
            doman.append(('user_id', '=', int(filter_user)))
        else:
            if self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('user_id', '!=', self.env.user.id))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))

            elif self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == False and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))
                doman.append(('user_id', '=', self.env.user.id))
        if filter_supervisor not in ['', "", None, False]:
            doman.append(('supervisor_id', '=', int(filter_supervisor)))
        else:
            if self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('supervisor_id', '=', self.env.user.id))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))
            elif self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == False and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('supervisor_id', '=', self.env.user.id))
                doman.append(('supervisor_id', '!=', self.env.user.id))
                doman.append(('supervisor_id', '=', False))
        if filter_model not in ['', "", None, False]:
            if filter_record not in ['', "", None, False]:
                doman.append(('res_id', '=', filter_record))
                doman.append(('res_model_id', '=', int(filter_model)))
            else:
                doman.append(('res_model_id', '=', int(filter_model)))
        activities = self.env['mail.activity'].sudo().search(
            doman, order='res_id desc')
        total_pages = 0.0
        total_planned_activities = len(activities.ids)
        record_limit = self.env.company.sh_planned_table
        if total_planned_activities > 0 and record_limit > 0:
            total_pages = math.ceil(
                float(total_planned_activities) / float(record_limit))
        current_page = int(current_page)
        start = self.env.company.sh_planned_table * (current_page - 1)
        stop = current_page * self.env.company.sh_planned_table
        activities = activities[start:stop]
        return self.env['ir.ui.view'].with_context().render_template(
            'sh_activities_management.sh_crm_db_activity_todo_tbl', {
                'activities': activities,
                'planned_acitvities_count': len(activities.ids),
                'total_pages': total_pages,
                'current_page': current_page,
            })

    @api.model
    def get_sh_crm_activity_all_tbl(self, filter_date, filter_user, start_date,
                                    end_date, filter_supervisor, current_page,
                                    filter_model, filter_record):
        doman = []
        crm_days_filter = filter_date
        custom_date_start = start_date
        custom_date_end = end_date
        if crm_days_filter == 'today':

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            dt_flt1.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))
        elif crm_days_filter == 'yesterday':

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            prev_day = (datetime.now().date() -
                        relativedelta(days=1)).strftime('%Y/%m/%d')
            dt_flt1.append(prev_day)
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            prev_day = (datetime.now().date() -
                        relativedelta(days=1)).strftime('%Y/%m/%d')
            dt_flt2.append(prev_day)
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'weekly':  # current week

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append(
                (datetime.now().date() -
                 relativedelta(weeks=1, weekday=0)).strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'prev_week':  # Previous week

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append(
                (datetime.now().date() -
                 relativedelta(weeks=2, weekday=0)).strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(
                (datetime.now().date() -
                 relativedelta(weeks=1, weekday=6)).strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'monthly':  # Current Month

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date()).strftime("%Y/%m/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'prev_month':  # Previous Month

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date() -
                            relativedelta(months=1)).strftime("%Y/%m/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/01"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'cur_year':  # Current Year

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date()).strftime("%Y/01/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'prev_year':  # Previous Year

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date() -
                            relativedelta(years=1)).strftime("%Y/01/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/01/01"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'custom':
            if custom_date_start and custom_date_end:

                dt_flt1 = []
                dt_flt1.append('date_deadline')
                dt_flt1.append('>')
                dt_flt1.append(
                    datetime.strptime(
                        str(custom_date_start),
                        DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d"))
                doman.append(tuple(dt_flt1))

                dt_flt2 = []
                dt_flt2.append('date_deadline')
                dt_flt2.append('<=')
                dt_flt2.append(
                    datetime.strptime(
                        str(custom_date_end),
                        DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d"))
                doman.append(tuple(dt_flt2))

#         doman = []
# FILTER USER
        if filter_user not in ['', "", None, False]:
            doman.append(('|'))
            doman.append(('sh_user_ids', 'in', [int(filter_user)]))
            doman.append(('user_id', '=', int(filter_user)))
        else:
            if self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('user_id', '!=', self.env.user.id))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))

            elif self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == False and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))
        if filter_supervisor not in ['', "", None, False]:
            doman.append(('supervisor_id', '=', int(filter_supervisor)))
        else:
            if self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('supervisor_id', '=', self.env.user.id))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))
            elif self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == False and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('supervisor_id', '=', self.env.user.id))
                doman.append(('supervisor_id', '!=', self.env.user.id))
                doman.append(('supervisor_id', '=', False))
        doman.append(('|'))
        doman.append(('active', '=', True))
        doman.append(('active', '=', False))
        if filter_model not in ['', "", None, False]:
            if filter_record not in ['', "", None, False]:
                doman.append(('res_id', '=', filter_record))
                doman.append(('res_model_id', '=', int(filter_model)))
            else:
                doman.append(('res_model_id', '=', int(filter_model)))
        activities = self.env['mail.activity'].sudo().search(
            doman, order='res_id desc')
        total_pages = 0.0
        total_activities = len(activities.ids)
        record_limit = self.env.company.sh_all_table
        if total_activities > 0 and record_limit > 0:
            total_pages = math.ceil(
                float(total_activities) / float(record_limit))
        current_page = int(current_page)
        start = self.env.company.sh_all_table * (current_page - 1)
        stop = current_page * self.env.company.sh_all_table
        activities = activities[start:stop]
        return self.env['ir.ui.view'].with_context().render_template(
            'sh_activities_management.sh_crm_db_activity_all_tbl', {
                'activities': activities,
                'all_acitvities_count': len(activities.ids),
                'total_pages': total_pages,
                'current_page': current_page,
            })

    @api.model
    def get_sh_crm_activity_completed_tbl(self, filter_date, filter_user,
                                          start_date, end_date,
                                          filter_supervisor, current_page,
                                          filter_model, filter_record):
        doman = [('active', '=', False), ('state', '=', 'done')]
        crm_days_filter = filter_date
        custom_date_start = start_date
        custom_date_end = end_date
        if crm_days_filter == 'today':

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            dt_flt1.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))
        elif crm_days_filter == 'yesterday':

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            prev_day = (datetime.now().date() -
                        relativedelta(days=1)).strftime('%Y/%m/%d')
            dt_flt1.append(prev_day)
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            prev_day = (datetime.now().date() -
                        relativedelta(days=1)).strftime('%Y/%m/%d')
            dt_flt2.append(prev_day)
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'weekly':  # current week

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append(
                (datetime.now().date() -
                 relativedelta(weeks=1, weekday=0)).strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'prev_week':  # Previous week

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append(
                (datetime.now().date() -
                 relativedelta(weeks=2, weekday=0)).strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(
                (datetime.now().date() -
                 relativedelta(weeks=1, weekday=6)).strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'monthly':  # Current Month

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date()).strftime("%Y/%m/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'prev_month':  # Previous Month

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date() -
                            relativedelta(months=1)).strftime("%Y/%m/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/01"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'cur_year':  # Current Year

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date()).strftime("%Y/01/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'prev_year':  # Previous Year

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date() -
                            relativedelta(years=1)).strftime("%Y/01/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/01/01"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'custom':
            if custom_date_start and custom_date_end:

                dt_flt1 = []
                dt_flt1.append('date_deadline')
                dt_flt1.append('>')
                dt_flt1.append(
                    datetime.strptime(
                        str(custom_date_start),
                        DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d"))
                doman.append(tuple(dt_flt1))

                dt_flt2 = []
                dt_flt2.append('date_deadline')
                dt_flt2.append('<=')
                dt_flt2.append(
                    datetime.strptime(
                        str(custom_date_end),
                        DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d"))
                doman.append(tuple(dt_flt2))

#         doman = []
# FILTER USER
        if filter_user not in ['', "", None, False]:
            doman.append(('|'))
            doman.append(('user_id', '=', int(filter_user)))
            doman.append(('sh_user_ids', 'in', [int(filter_user)]))
        else:
            if self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('user_id', '!=', self.env.user.id))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))

            elif self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == False and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))
        if filter_supervisor not in ['', "", None, False]:
            doman.append(('supervisor_id', '=', int(filter_supervisor)))
        else:
            if self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('supervisor_id', '=', self.env.user.id))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))
            elif self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == False and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('supervisor_id', '=', self.env.user.id))
                doman.append(('supervisor_id', '!=', self.env.user.id))
                doman.append(('supervisor_id', '=', False))
        if filter_model not in ['', "", None, False]:
            if filter_record not in ['', "", None, False]:
                doman.append(('res_id', '=', filter_record))
                doman.append(('res_model_id', '=', int(filter_model)))
            else:
                doman.append(('res_model_id', '=', int(filter_model)))
        activities = self.env['mail.activity'].sudo().search(
            doman, order='res_id desc')
        total_pages = 0.0
        total_completed_activities = len(activities.ids)
        record_limit = self.env.company.sh_completed_table
        if total_completed_activities > 0 and record_limit > 0:
            total_pages = math.ceil(
                float(total_completed_activities) / float(record_limit))
        current_page = int(current_page)
        start = self.env.company.sh_completed_table * (current_page - 1)
        stop = current_page * self.env.company.sh_completed_table
        activities = activities[start:stop]
        return self.env['ir.ui.view'].with_context().render_template(
            'sh_activities_management.sh_crm_db_activity_completed_tbl', {
                'activities': activities,
                'completed_acitvities_count': len(activities.ids),
                'total_pages': total_pages,
                'current_page': current_page,
            })

    @api.model
    def get_sh_crm_activity_overdue_tbl(self, filter_date, filter_user,
                                        start_date, end_date,
                                        filter_supervisor, current_page,
                                        filter_model, filter_record):
        doman = [('active', '=', True),
                 ('date_deadline', '<', fields.Date.today())]
        crm_days_filter = filter_date
        custom_date_start = start_date
        custom_date_end = end_date
        if crm_days_filter == 'today':

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            dt_flt1.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))
        elif crm_days_filter == 'yesterday':

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            prev_day = (datetime.now().date() -
                        relativedelta(days=1)).strftime('%Y/%m/%d')
            dt_flt1.append(prev_day)
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            prev_day = (datetime.now().date() -
                        relativedelta(days=1)).strftime('%Y/%m/%d')
            dt_flt2.append(prev_day)
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'weekly':  # current week

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append(
                (datetime.now().date() -
                 relativedelta(weeks=1, weekday=0)).strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'prev_week':  # Previous week

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append(
                (datetime.now().date() -
                 relativedelta(weeks=2, weekday=0)).strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(
                (datetime.now().date() -
                 relativedelta(weeks=1, weekday=6)).strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'monthly':  # Current Month

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date()).strftime("%Y/%m/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'prev_month':  # Previous Month

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date() -
                            relativedelta(months=1)).strftime("%Y/%m/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/01"))
            doman.append(tuple(dt_flt2))
        elif crm_days_filter == 'cur_year':  # Current Year

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date()).strftime("%Y/01/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'prev_year':  # Previous Year

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date() -
                            relativedelta(years=1)).strftime("%Y/01/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/01/01"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'custom':
            if custom_date_start and custom_date_end:

                dt_flt1 = []
                dt_flt1.append('date_deadline')
                dt_flt1.append('>')
                dt_flt1.append(
                    datetime.strptime(
                        str(custom_date_start),
                        DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d"))
                doman.append(tuple(dt_flt1))

                dt_flt2 = []
                dt_flt2.append('date_deadline')
                dt_flt2.append('<=')
                dt_flt2.append(
                    datetime.strptime(
                        str(custom_date_end),
                        DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d"))
                doman.append(tuple(dt_flt2))

#         doman = []
# FILTER USER
        if filter_user not in ['', "", None, False]:
            doman.append(('|'))
            doman.append(('user_id', '=', int(filter_user)))
            doman.append(('sh_user_ids', 'in', [int(filter_user)]))
        else:
            if self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('user_id', '!=', self.env.user.id))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))

            elif self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == False and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))
        if filter_supervisor not in ['', "", None, False]:
            doman.append(('supervisor_id', '=', int(filter_supervisor)))
        else:
            if self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('supervisor_id', '=', self.env.user.id))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))
            elif self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == False and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('supervisor_id', '=', self.env.user.id))
                doman.append(('supervisor_id', '!=', self.env.user.id))
                doman.append(('supervisor_id', '=', False))
        if filter_model not in ['', "", None, False]:
            if filter_record not in ['', "", None, False]:
                doman.append(('res_id', '=', filter_record))
                doman.append(('res_model_id', '=', int(filter_model)))
            else:
                doman.append(('res_model_id', '=', int(filter_model)))
        activities = self.env['mail.activity'].sudo().search(
            doman, order='res_id desc')
        total_pages = 0.0
        total_overdue_activities = len(activities.ids)
        record_limit = self.env.company.sh_due_table
        if total_overdue_activities > 0 and record_limit > 0:
            total_pages = math.ceil(
                float(total_overdue_activities) / float(record_limit))
        current_page = int(current_page)
        start = self.env.company.sh_due_table * (current_page - 1)
        stop = current_page * self.env.company.sh_due_table
        activities = activities[start:stop]
        return self.env['ir.ui.view'].with_context().render_template(
            'sh_activities_management.sh_crm_db_activity_overdue_tbl', {
                'activities': activities,
                'overdue_acitvities_count': len(activities.ids),
                'total_pages': total_pages,
                'current_page': current_page,
            })

    @api.model
    def get_sh_crm_activity_cancelled_tbl(self, filter_date, filter_user,
                                          start_date, end_date,
                                          filter_supervisor, current_page,
                                          filter_model, filter_record):
        doman = [('active', '=', False), ('state', '=', 'cancel')]
        crm_days_filter = filter_date
        custom_date_start = start_date
        custom_date_end = end_date
        if crm_days_filter == 'today':

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            dt_flt1.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))
        elif crm_days_filter == 'yesterday':

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            prev_day = (datetime.now().date() -
                        relativedelta(days=1)).strftime('%Y/%m/%d')
            dt_flt1.append(prev_day)
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            prev_day = (datetime.now().date() -
                        relativedelta(days=1)).strftime('%Y/%m/%d')
            dt_flt2.append(prev_day)
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'weekly':  # current week

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append(
                (datetime.now().date() -
                 relativedelta(weeks=1, weekday=0)).strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'prev_week':  # Previous week

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append(
                (datetime.now().date() -
                 relativedelta(weeks=2, weekday=0)).strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(
                (datetime.now().date() -
                 relativedelta(weeks=1, weekday=6)).strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'monthly':  # Current Month

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date()).strftime("%Y/%m/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'prev_month':  # Previous Month

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date() -
                            relativedelta(months=1)).strftime("%Y/%m/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/01"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'cur_year':  # Current Year

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date()).strftime("%Y/01/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'prev_year':  # Previous Year

            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append((datetime.now().date() -
                            relativedelta(years=1)).strftime("%Y/01/01"))
            doman.append(tuple(dt_flt1))

            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/01/01"))
            doman.append(tuple(dt_flt2))

        elif crm_days_filter == 'custom':
            if custom_date_start and custom_date_end:

                dt_flt1 = []
                dt_flt1.append('date_deadline')
                dt_flt1.append('>')
                dt_flt1.append(
                    datetime.strptime(
                        str(custom_date_start),
                        DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d"))
                doman.append(tuple(dt_flt1))

                dt_flt2 = []
                dt_flt2.append('date_deadline')
                dt_flt2.append('<=')
                dt_flt2.append(
                    datetime.strptime(
                        str(custom_date_end),
                        DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d"))
                doman.append(tuple(dt_flt2))


#         doman = []
# FILTER USER
        if filter_user not in ['', "", None, False]:
            doman.append(('|'))
            doman.append(('user_id', '=', int(filter_user)))
            doman.append(('sh_user_ids', 'in', [int(filter_user)]))
        else:
            if self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('user_id', '!=', self.env.user.id))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))

            elif self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == False and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))
        if filter_supervisor not in ['', "", None, False]:
            doman.append(('supervisor_id', '=', int(filter_supervisor)))
        else:
            if self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('supervisor_id', '=', self.env.user.id))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))
            elif self.env.user.has_group(
                    'sh_activities_management.group_activity_supervisor'
            ) == False and self.env.user.has_group(
                    'sh_activities_management.group_activity_user'
            ) == True and self.env.user.has_group(
                    'sh_activities_management.group_activity_manager'
            ) == False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('supervisor_id', '=', self.env.user.id))
                doman.append(('supervisor_id', '!=', self.env.user.id))
                doman.append(('supervisor_id', '=', False))
        if filter_model not in ['', "", None, False]:
            if filter_record not in ['', "", None, False]:
                doman.append(('res_id', '=', filter_record))
                doman.append(('res_model_id', '=', int(filter_model)))
            else:
                doman.append(('res_model_id', '=', int(filter_model)))
        activities = self.env['mail.activity'].sudo().search(
            doman, order='res_id desc')
        total_pages = 0.0
        total_cancelled_activities = len(activities.ids)
        record_limit = self.env.company.sh_cancel_table
        if total_cancelled_activities > 0 and record_limit > 0:
            total_pages = math.ceil(
                float(total_cancelled_activities) / float(record_limit))
        current_page = int(current_page)
        start = self.env.company.sh_cancel_table * (current_page - 1)
        stop = current_page * self.env.company.sh_cancel_table
        activities = activities[start:stop]
        return self.env['ir.ui.view'].with_context().render_template(
            'sh_activities_management.sh_crm_db_activity_cancelled_tbl', {
                'activities': activities,
                'cancelled_acitvities_count': len(activities.ids),
                'total_pages': total_pages,
                'current_page': current_page,
            })

    @api.model
    def get_user_list(self):
        company_id = self.env.company
        domain = [('company_ids', 'in', [company_id.id]),
                  ('share', '=', False)]
        users = self.env["res.users"].sudo().search_read(domain)
        return users

    @api.model
    def get_document_models(self):
        document_models = False
        if self.env.company.sh_document_model:
            if self.env.company.sh_document_model_ids:
                domain = [('id', 'in',
                           self.env.company.sh_document_model_ids.ids)]
                document_models = self.env["ir.model"].sudo().search_read(
                    domain)
        return document_models

    @api.model
    def get_document_model_records(self, filter_model):
        document_model_records = False
        if filter_model not in ["", None, False]:
            model_id = self.env['ir.model'].sudo().browse(int(filter_model))
            if model_id:
                model_records = self.env[model_id.model].sudo().search([
                    ('activity_ids', '!=', False)
                ])
                domain = [('id', 'in', model_records.ids)]
                document_model_records = self.env[
                    model_id.model].sudo().search_read(domain)
        return document_model_records