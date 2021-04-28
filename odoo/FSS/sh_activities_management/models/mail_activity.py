# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, modules,exceptions,_
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import clean_context
from datetime import datetime,timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import html2plaintext
import math


class MailActivity(models.Model):
    """ Inherited Mail Acitvity to add custom field"""
    _inherit = 'mail.activity'
    
    @api.model
    def default_company_id(self):
        return self.env.company

    active = fields.Boolean(default=True)
    supervisor_id = fields.Many2one('res.users',string="Supervisor")
    sh_activity_tags = fields.Many2many(
        "sh.activity.tags", string='Activity Tags')
    state = fields.Selection(selection_add=[("done", "Done")], compute="_compute_state",store=True)
    date_done = fields.Date("Completed Date", index=True, readonly=True)
    feedback = fields.Text("Feedback")
    
    text_note = fields.Char("Notes In Char format ",compute ='get_html_to_char_note')
    sh_user_ids = fields.Many2many('res.users', string="Assign Multi Users")
    sh_display_multi_user = fields.Boolean(compute='_compute_sh_display_multi_user')
    company_id = fields.Many2one('res.company',string='Company',default=default_company_id)
    color = fields.Integer('Color Index', default=0)
    sh_create_individual_activity = fields.Boolean('Individual activities for multi users ?')

    @api.model
    def create(self, vals):
        res = super(MailActivity, self).create(vals)
        if res.sh_user_ids and res.sh_create_individual_activity:
            for user in res.sh_user_ids:
                if res.user_id.id != user.id:
                    self.env['mail.activity'].sudo().create({
                        'res_model_id': res.res_model_id.id,
                        'res_id': res.res_id,
                        'date_deadline': res.date_deadline,
                        'sh_user_ids':[(6,0,user.ids)],
                        'supervisor_id':res.supervisor_id.id,
                        'activity_type_id': res.activity_type_id.id,
                        'summary': res.summary,
                        'note': res.note,
                    })
        return res

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

        template = self.env.ref('sh_activities_management.template_mail_activity_due_notify_email')
        notify_create_user_template = self.env.ref('sh_activities_management.template_mail_activity_due_notify_email_create_user')
        company_object = self.env['res.company'].search([('activity_due_notification','=',True)],limit = 1)
        
        if template and company_object and company_object.activity_due_notification:
            
            activity_obj = self.env['mail.activity'].search([])                             
            
            if activity_obj:
                for record in activity_obj:
                    if record.date_deadline and record.user_id and record.user_id.id != self.env.ref('base.user_root').id and record.user_id.partner_id and record.user_id.partner_id.email :

                        # On Due Date
                        if company_object.ondue_date_notify:           
                       
                            if datetime.strptime(str(record.date_deadline) , DEFAULT_SERVER_DATE_FORMAT).date() == datetime.now().date() : 
                                mail_res = template.send_mail(record.id,force_send=True)
                                if notify_create_user_template and company_object.notify_create_user_due:
                                    if record.user_id.id != record.create_uid.id and record.create_uid.id != self.env.ref('base.user_root').id:
                                        notify_create_user_template.send_mail(record.id,force_send=True)
                        # On After First Notify 
                        if company_object.after_first_notify and company_object.enter_after_first_notify :           
                            after_date = datetime.strptime(str(record.date_deadline) , DEFAULT_SERVER_DATE_FORMAT).date() + timedelta(days= company_object.enter_after_first_notify)    

                            if after_date == datetime.now().date() : 
                                mail_res = template.send_mail(record.id,force_send=True)
                                if notify_create_user_template and company_object.notify_create_user_after_first:
                                    if record.user_id.id != record.create_uid.id and record.create_uid.id != self.env.ref('base.user_root').id:
                                        notify_create_user_template.send_mail(record.id,force_send=True)
                        # On After Second Notify 
                        if company_object.after_second_notify and company_object.enter_after_second_notify :           
                            after_date = datetime.strptime(str(record.date_deadline) , DEFAULT_SERVER_DATE_FORMAT).date() + timedelta(days= company_object.enter_after_second_notify)    
                       
                            if after_date == datetime.now().date() : 
                                mail_res = template.send_mail(record.id,force_send=True)
                                if notify_create_user_template and company_object.notify_create_user_after_second:
                                    if record.user_id.id != record.create_uid.id and record.create_uid.id != self.env.ref('base.user_root').id:
                                        notify_create_user_template.send_mail(record.id,force_send=True)
                        # On Before First Notify 
                        if company_object.before_first_notify and company_object.enter_before_first_notify :           
                            before_date = datetime.strptime(str(record.date_deadline) , DEFAULT_SERVER_DATE_FORMAT).date() - timedelta(days= company_object.enter_before_first_notify)    

                            if before_date == datetime.now().date() : 
                                mail_res = template.send_mail(record.id,force_send=True)
                                if notify_create_user_template and company_object.notify_create_user_before_first:
                                    if record.user_id.id != record.create_uid.id and record.create_uid.id != self.env.ref('base.user_root').id:
                                        notify_create_user_template.send_mail(record.id,force_send=True)
                        # On Before Second Notify 
                        if company_object.before_second_notify and company_object.enter_before_second_notify :           
                            before_date = datetime.strptime(str(record.date_deadline) , DEFAULT_SERVER_DATE_FORMAT).date() - timedelta(days= company_object.enter_before_second_notify)    
                       
                            if before_date == datetime.now().date() : 
                                mail_res = template.send_mail(record.id,force_send=True)      
                                if notify_create_user_template and company_object.notify_create_user_before_second:
                                    if record.user_id.id != record.create_uid.id and record.create_uid.id != self.env.ref('base.user_root').id:
                                        notify_create_user_template.send_mail(record.id,force_send=True)                      

    
    def action_view_activity(self):
        self.ensure_one()
        try:
            model = self.env[self.res_model].browse(self.res_id).check_access_rule('read')
            return{
                'name':'Origin Activity',
                'res_model':self.res_model,
                'res_id':self.res_id,
                'view_mode':'form',
                'type':'ir.actions.act_window',
                'target':'current',
            }
        except exceptions.AccessError:
            raise exceptions.UserError(
                _('Assigned user %s has no access to the document and is not able to handle this activity.') %
                self.env.user.display_name)
    
    def action_done(self):
        """ Wrapper without feedback because web button add context as
        parameter, therefore setting context to feedback """
        return{
            'name':'Activity Feedback',
            'res_model':'activity.feedback',
            'type':'ir.actions.act_window',
            'view_mode':'form',
            'context':{'default_done_button_pressed':True},
            'target':'new',
            }
    
    
    def action_done_from_popup(self,feedback=False):
        messages, next_activities = self._action_done()
        self.state='done'
        self.active=False
        self.date_done = fields.Date.today()
        self.feedback = feedback
#         return messages.ids and messages.ids[0] or False

    def _action_done(self, feedback=False, attachment_ids=None):
        
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
                Activity = self.env['mail.activity'].sudo().with_context(activity_previous_deadline=activity.date_deadline)  # context key is required in the onchange to set deadline
                vals = Activity.default_get(Activity.fields_get())

                vals.update({
                    'previous_activity_type_id': activity.activity_type_id.id,
                    'res_id': activity.res_id,
                    'res_model': activity.res_model,
                    'res_model_id': self.env['ir.model']._get(activity.res_model).id,
                })
                virtual_activity = Activity.sudo().new(vals)
                virtual_activity._onchange_previous_activity_type_id()
                virtual_activity._onchange_activity_type_id()
                next_activities_values.append(virtual_activity._convert_to_write(virtual_activity._cache))

            # post message on activity, before deleting it
            record = self.env[activity.res_model].sudo().browse(activity.res_id)
            record.sudo().message_post_with_view(
                'mail.message_activity_done',
                values={
                    'activity': activity,
                    'feedback': feedback,
                    'display_assignee': activity.user_id != self.env.user
                },
                subtype_id=self.env['ir.model.data'].xmlid_to_res_id('mail.mt_activities'),
                mail_activity_type_id=activity.activity_type_id.id,
                attachment_ids=[(4, attachment_id) for attachment_id in attachment_ids] if attachment_ids else [],
            )
            messages |= record.sudo().message_ids[0]

        next_activities = self.env['mail.activity'].sudo().create(next_activities_values)
        self.active=False
        self.date_done = fields.Date.today()
        self.feedback = feedback
        self.state = "done"
#         self.unlink()  # will unlink activity, dont access `self` after that

        return messages, next_activities
    
    def action_done_schedule_next(self):
        """ Wrapper without feedback because web button add context as
        parameter, therefore setting context to feedback """
        return{
            'name':'Activity Feedback',
            'res_model':'activity.feedback',
            'type':'ir.actions.act_window',
            'view_mode':'form',
            'context':{'default_done_button_pressed':False},
            'target':'new',
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
        view_id = self.env.ref('sh_activities_management.sh_mail_activity_type_view_form_inherit').id
        messages, next_activities = self._action_done(feedback=feedback)  # will unlink activity, dont access self after that
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
                    WHERE user_id = %(user_id)s and active=True
                    GROUP BY m.id, states, act.res_model;
                    """
        self.env.cr.execute(query, {
            'today': fields.Date.context_today(self),
            'user_id': self.env.uid,
        })
        activity_data = self.env.cr.dictfetchall()
        model_ids = [a['id'] for a in activity_data]
        model_names = {n[0]: n[1] for n in self.env['ir.model'].browse(model_ids).name_get()}

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
                    'total_count': 0, 'today_count': 0, 'overdue_count': 0, 'planned_count': 0,
                }
            user_activities[activity['model']]['%s_count' % activity['states']] += activity['count']
            if activity['states'] in ('today', 'overdue'):
                user_activities[activity['model']]['total_count'] += activity['count']

            user_activities[activity['model']]['actions'] = [{
                'icon': 'fa-clock-o',
                'name': 'Summary',
            }]
        return list(user_activities.values())


class ActivityDashboard(models.Model):
    _name = 'activity.dashboard'
    _description = 'Activity Dashboard'
    
    
    @api.model
    def get_sh_crm_activity_planned_count_tbl(self,filter_date,filter_user,start_date,end_date,filter_supervisor):
        
        doman = []

        crm_days_filter = filter_date 
        custom_date_start = start_date
        custom_date_end = end_date 
        planned_activities_count = 0
        completed_activities_count = 0
        overdue_activities_count = 0        
        if crm_days_filter == 'today':
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            dt_flt1.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt1) )
             
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) )
        elif crm_days_filter == 'yesterday':
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            prev_day = (datetime.now().date() - relativedelta(days=1)).strftime('%Y/%m/%d')
            dt_flt1.append(prev_day)
            doman.append( tuple(dt_flt1) )
             
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            prev_day = (datetime.now().date() - relativedelta(days=1)).strftime('%Y/%m/%d')                                     
            dt_flt2.append(prev_day)
            doman.append( tuple(dt_flt2) ) 
        elif crm_days_filter == 'weekly': # current week 
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(weeks = 1,weekday=0) ).strftime("%Y/%m/%d") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 
            
        elif crm_days_filter == 'prev_week': # Previous week 
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(weeks = 2,weekday=0) ).strftime("%Y/%m/%d") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append( (datetime.now().date()- relativedelta(weeks = 1,weekday=6) ).strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 
           
        elif crm_days_filter == 'monthly': # Current Month                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() ).strftime("%Y/%m/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 

        elif crm_days_filter == 'prev_month': # Previous Month                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(months = 1) ).strftime("%Y/%m/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/01"))
            doman.append( tuple(dt_flt2) ) 
           
        elif crm_days_filter == 'cur_year': # Current Year                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() ).strftime("%Y/01/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 

        elif crm_days_filter == 'prev_year': # Previous Year                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(years = 1) ).strftime("%Y/01/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/01/01"))
            doman.append( tuple(dt_flt2) ) 
           
        elif crm_days_filter == 'custom':
            if  custom_date_start and custom_date_end:
                 
                dt_flt1 = []
                dt_flt1.append('date_deadline')
                dt_flt1.append('>')
                dt_flt1.append( datetime.strptime(str(custom_date_start),DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d") )
                doman.append( tuple(dt_flt1) ) 
            
                dt_flt2 = []
                dt_flt2.append('date_deadline')
                dt_flt2.append('<=')
                dt_flt2.append( datetime.strptime(str(custom_date_end),DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d"))
                doman.append( tuple(dt_flt2) ) 

#         doman = []
        # FILTER USER
        if filter_user not in ['',"",None,False]:
            doman.append(('|'))
            doman.append(('sh_user_ids','in',[int(filter_user)]))
            doman.append(('user_id', '=', int(filter_user)))
        else:
            if self.env.user.has_group('sh_activities_management.group_activity_supervisor')==True and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('user_id', '!=', self.env.user.id))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids','in',[self.env.user.id]))
                
            elif self.env.user.has_group('sh_activities_management.group_activity_supervisor')==False and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('|'))
                doman.append(('sh_user_ids','in',[self.env.user.id]))
                doman.append(('user_id', '=', self.env.user.id))
        if filter_supervisor not in ['',"",None,False]:
            doman.append(('supervisor_id','=',int(filter_supervisor)))
        else:
            if self.env.user.has_group('sh_activities_management.group_activity_supervisor')==True and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('supervisor_id','=',self.env.user.id))
            elif self.env.user.has_group('sh_activities_management.group_activity_supervisor')==False and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('supervisor_id','=',self.env.user.id))
                doman.append(('supervisor_id','!=',self.env.user.id))
                doman.append(('supervisor_id','=',False))
        doman.append(('|'))
        doman.append(('active','=',True))
        doman.append(('active','=',False))
        activities = self.env['mail.activity'].search(doman,limit = False, order='res_id desc')
        planned_activities = []
        overdue_activities = []
        all_activities = []
        completed_activities = []
        for activity in activities:
            all_activities.append(activity.id)
            if activity.active and activity.date_deadline >= fields.Date.today():
                planned_activities_count += 1
                planned_activities.append(activity.id)
            if activity.active and activity.date_deadline < fields.Date.today():
                overdue_activities_count += 1
                overdue_activities.append(activity.id)
            if not activity.active:
                completed_activities_count += 1
                completed_activities.append(activity.id)
        return self.env['ir.ui.view'].with_context().render_template('sh_activities_management.sh_crm_db_activity_count_box', {
            'planned_activities':planned_activities,
            'overdue_activities':overdue_activities,
            'all_activities':all_activities,
            'completed_activities':completed_activities,
            'planned_acitvities_count' : planned_activities_count,
            'overdue_activities_count':overdue_activities_count,
            'completed_activities_count':completed_activities_count,
            'all_activities_count':len(activities.ids),
            })
    
    
    @api.model
    def get_sh_crm_activity_todo_tbl(self,filter_date,filter_user,start_date,end_date,filter_supervisor,current_page):
        doman = [('active','=',True),('date_deadline','>=',fields.Date.today())]
        crm_days_filter = filter_date 
        custom_date_start = start_date
        custom_date_end = end_date     
        company_id = self.env.company   
        if crm_days_filter == 'today':
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            dt_flt1.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt1) )
             
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) )
        elif crm_days_filter == 'yesterday':
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            prev_day = (datetime.now().date() - relativedelta(days=1)).strftime('%Y/%m/%d')
            dt_flt1.append(prev_day)
            doman.append( tuple(dt_flt1) )
             
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            prev_day = (datetime.now().date() - relativedelta(days=1)).strftime('%Y/%m/%d')                                     
            dt_flt2.append(prev_day)
            doman.append( tuple(dt_flt2) ) 
      
        elif crm_days_filter == 'weekly': # current week 
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(weeks = 1,weekday=0) ).strftime("%Y/%m/%d") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 
            
        elif crm_days_filter == 'prev_week': # Previous week 
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(weeks = 2,weekday=0) ).strftime("%Y/%m/%d") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append( (datetime.now().date()- relativedelta(weeks = 1,weekday=6) ).strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 
           
        elif crm_days_filter == 'monthly': # Current Month                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() ).strftime("%Y/%m/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 

        elif crm_days_filter == 'prev_month': # Previous Month                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(months = 1) ).strftime("%Y/%m/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/01"))
            doman.append( tuple(dt_flt2) ) 
           
        elif crm_days_filter == 'cur_year': # Current Year                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() ).strftime("%Y/01/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 

        elif crm_days_filter == 'prev_year': # Previous Year                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(years = 1) ).strftime("%Y/01/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/01/01"))
            doman.append( tuple(dt_flt2) ) 
           
        elif crm_days_filter == 'custom':
            if  custom_date_start and custom_date_end:
                 
                dt_flt1 = []
                dt_flt1.append('date_deadline')
                dt_flt1.append('>')
                dt_flt1.append( datetime.strptime(str(custom_date_start),DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d") )
                doman.append( tuple(dt_flt1) ) 
            
                dt_flt2 = []
                dt_flt2.append('date_deadline')
                dt_flt2.append('<=')
                dt_flt2.append( datetime.strptime(str(custom_date_end),DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d"))
                doman.append( tuple(dt_flt2) ) 

#         doman = []
        # FILTER USER
        if filter_user not in ['',"",None,False]:
            doman.append(('|'))
            doman.append(('sh_user_ids','in',[int(filter_user)]))
            doman.append(('user_id', '=', int(filter_user)))
        else:
            if self.env.user.has_group('sh_activities_management.group_activity_supervisor')==True and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('user_id', '!=', self.env.user.id))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids','in',[self.env.user.id]))
                
            elif self.env.user.has_group('sh_activities_management.group_activity_supervisor')==False and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('|'))
                doman.append(('sh_user_ids','in',[self.env.user.id]))
                doman.append(('user_id', '=', self.env.user.id))
        if filter_supervisor not in ['',"",None,False]:
            doman.append(('supervisor_id','=',int(filter_supervisor)))
        else:
            if self.env.user.has_group('sh_activities_management.group_activity_supervisor')==True and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('supervisor_id','=',self.env.user.id))
            elif self.env.user.has_group('sh_activities_management.group_activity_supervisor')==False and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('supervisor_id','=',self.env.user.id))
                doman.append(('supervisor_id','!=',self.env.user.id))
                doman.append(('supervisor_id','=',False))
        activities = self.env['mail.activity'].sudo().search(
            doman, order='res_id desc')
        total_pages = 0.0
        total_planned_activities = len(activities.ids)
        record_limit = self.env.company.sh_planned_table
        if total_planned_activities > 0 and record_limit > 0:
            total_pages = math.ceil(float(total_planned_activities) / float(record_limit))
        current_page = int(current_page)
        start = self.env.company.sh_planned_table * (current_page-1)
        stop = current_page * self.env.company.sh_planned_table
        activities = activities[start:stop]
        return self.env['ir.ui.view'].with_context().render_template('sh_activities_management.sh_crm_db_activity_todo_tbl', {
            'activities': activities,
            'planned_acitvities_count': len(activities.ids),
            'total_pages':total_pages,
            'current_page':current_page,
        })
    
    
    @api.model
    def get_sh_crm_activity_all_tbl(self,filter_date,filter_user,start_date,end_date,filter_supervisor,current_page):
        
        doman = []

        crm_days_filter = filter_date 
        custom_date_start = start_date
        custom_date_end = end_date      
        company_id = self.env.company   
        if crm_days_filter == 'today':
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            dt_flt1.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt1) )
             
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) )
        elif crm_days_filter == 'yesterday':
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            prev_day = (datetime.now().date() - relativedelta(days=1)).strftime('%Y/%m/%d')
            dt_flt1.append(prev_day)
            doman.append( tuple(dt_flt1) )
             
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            prev_day = (datetime.now().date() - relativedelta(days=1)).strftime('%Y/%m/%d')                                     
            dt_flt2.append(prev_day)
            doman.append( tuple(dt_flt2) ) 
      
        elif crm_days_filter == 'weekly': # current week 
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(weeks = 1,weekday=0) ).strftime("%Y/%m/%d") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 
            
            
        elif crm_days_filter == 'prev_week': # Previous week 
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(weeks = 2,weekday=0) ).strftime("%Y/%m/%d") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append( (datetime.now().date()- relativedelta(weeks = 1,weekday=6) ).strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 
           
        elif crm_days_filter == 'monthly': # Current Month                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() ).strftime("%Y/%m/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 

        elif crm_days_filter == 'prev_month': # Previous Month                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(months = 1) ).strftime("%Y/%m/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/01"))
            doman.append( tuple(dt_flt2) ) 
           
        elif crm_days_filter == 'cur_year': # Current Year                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() ).strftime("%Y/01/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 

        elif crm_days_filter == 'prev_year': # Previous Year                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(years = 1) ).strftime("%Y/01/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/01/01"))
            doman.append( tuple(dt_flt2) ) 
           
        elif crm_days_filter == 'custom':
            if  custom_date_start and custom_date_end:
                 
                dt_flt1 = []
                dt_flt1.append('date_deadline')
                dt_flt1.append('>')
                dt_flt1.append( datetime.strptime(str(custom_date_start),DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d") )
                doman.append( tuple(dt_flt1) ) 
            
                dt_flt2 = []
                dt_flt2.append('date_deadline')
                dt_flt2.append('<=')
                dt_flt2.append( datetime.strptime(str(custom_date_end),DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d"))
                doman.append( tuple(dt_flt2) ) 

#         doman = []
        # FILTER USER
        if filter_user not in ['',"",None,False]:
            doman.append(('|'))
            doman.append(('sh_user_ids','in',[int(filter_user)]))
            doman.append(('user_id', '=', int(filter_user)))
        else:
            if self.env.user.has_group('sh_activities_management.group_activity_supervisor')==True and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('user_id', '!=', self.env.user.id))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids','in',[self.env.user.id]))
                
            elif self.env.user.has_group('sh_activities_management.group_activity_supervisor')==False and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('|'))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids','in',[self.env.user.id]))
        if filter_supervisor not in ['',"",None,False]:
            doman.append(('supervisor_id','=',int(filter_supervisor)))
        else:
            if self.env.user.has_group('sh_activities_management.group_activity_supervisor')==True and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('supervisor_id','=',self.env.user.id))
            elif self.env.user.has_group('sh_activities_management.group_activity_supervisor')==False and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('supervisor_id','=',self.env.user.id))
                doman.append(('supervisor_id','!=',self.env.user.id))
                doman.append(('supervisor_id','=',False))
        doman.append(('|'))
        doman.append(('active','=',True))
        doman.append(('active','=',False))
        activities = self.env['mail.activity'].sudo().search(
                doman, order='res_id desc')
        total_pages = 0.0
        total_activities = len(activities.ids)
        record_limit = self.env.company.sh_all_table
        if total_activities > 0 and record_limit > 0:
            total_pages = math.ceil(float(total_activities) / float(record_limit))
        current_page = int(current_page)
        start = self.env.company.sh_all_table * (current_page-1)
        stop = current_page * self.env.company.sh_all_table
        activities = activities[start:stop]
        return self.env['ir.ui.view'].with_context().render_template('sh_activities_management.sh_crm_db_activity_all_tbl', {
            'activities': activities,
            'all_acitvities_count': len(activities.ids),
            'total_pages':total_pages,
            'current_page':current_page,
        })
    
    @api.model
    def get_sh_crm_activity_completed_tbl(self,filter_date,filter_user,start_date,end_date,filter_supervisor,current_page):
        doman = [('active', '=', False)]
        crm_days_filter = filter_date 
        custom_date_start = start_date
        custom_date_end = end_date   
        company_id = self.env.company      
        if crm_days_filter == 'today':
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            dt_flt1.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt1) )
             
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) )
        elif crm_days_filter == 'yesterday':
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            prev_day = (datetime.now().date() - relativedelta(days=1)).strftime('%Y/%m/%d')
            dt_flt1.append(prev_day)
            doman.append( tuple(dt_flt1) )
             
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            prev_day = (datetime.now().date() - relativedelta(days=1)).strftime('%Y/%m/%d')                                     
            dt_flt2.append(prev_day)
            doman.append( tuple(dt_flt2) ) 
      
        elif crm_days_filter == 'weekly': # current week 
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(weeks = 1,weekday=0) ).strftime("%Y/%m/%d") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 
            
        elif crm_days_filter == 'prev_week': # Previous week 
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(weeks = 2,weekday=0) ).strftime("%Y/%m/%d") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append( (datetime.now().date()- relativedelta(weeks = 1,weekday=6) ).strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 
           
        elif crm_days_filter == 'monthly': # Current Month                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() ).strftime("%Y/%m/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 

        elif crm_days_filter == 'prev_month': # Previous Month                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(months = 1) ).strftime("%Y/%m/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/01"))
            doman.append( tuple(dt_flt2) ) 
           
        elif crm_days_filter == 'cur_year': # Current Year                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() ).strftime("%Y/01/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 

        elif crm_days_filter == 'prev_year': # Previous Year                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(years = 1) ).strftime("%Y/01/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/01/01"))
            doman.append( tuple(dt_flt2) ) 
           
        elif crm_days_filter == 'custom':
            if  custom_date_start and custom_date_end:
                 
                dt_flt1 = []
                dt_flt1.append('date_deadline')
                dt_flt1.append('>')
                dt_flt1.append( datetime.strptime(str(custom_date_start),DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d") )
                doman.append( tuple(dt_flt1) ) 
            
                dt_flt2 = []
                dt_flt2.append('date_deadline')
                dt_flt2.append('<=')
                dt_flt2.append( datetime.strptime(str(custom_date_end),DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d"))
                doman.append( tuple(dt_flt2) ) 

#         doman = []
        # FILTER USER
        if filter_user not in ['',"",None,False]:
            doman.append(('|'))
            doman.append(('user_id', '=', int(filter_user)))
            doman.append(('sh_user_ids', 'in', [int(filter_user)]))
        else:
            if self.env.user.has_group('sh_activities_management.group_activity_supervisor')==True and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('user_id', '!=', self.env.user.id))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))
                
            elif self.env.user.has_group('sh_activities_management.group_activity_supervisor')==False and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('|'))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))
        if filter_supervisor not in ['',"",None,False]:
            doman.append(('supervisor_id','=',int(filter_supervisor)))
        else:
            if self.env.user.has_group('sh_activities_management.group_activity_supervisor')==True and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('supervisor_id','=',self.env.user.id))
            elif self.env.user.has_group('sh_activities_management.group_activity_supervisor')==False and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('supervisor_id','=',self.env.user.id))
                doman.append(('supervisor_id','!=',self.env.user.id))
                doman.append(('supervisor_id','=',False))
        activities = self.env['mail.activity'].sudo().search(
                doman, order='res_id desc')
        total_pages = 0.0
        total_completed_activities = len(activities.ids)
        record_limit = self.env.company.sh_completed_table
        if total_completed_activities > 0 and record_limit > 0:
            total_pages = math.ceil(float(total_completed_activities) / float(record_limit))
        current_page = int(current_page)
        start = self.env.company.sh_completed_table * (current_page-1)
        stop = current_page * self.env.company.sh_completed_table
        activities = activities[start:stop]
        return self.env['ir.ui.view'].with_context().render_template('sh_activities_management.sh_crm_db_activity_completed_tbl', {
                'activities': activities,
                'completed_acitvities_count': len(activities.ids),
                'total_pages':total_pages,
                'current_page':current_page,
            })
        
    @api.model
    def get_sh_crm_activity_overdue_tbl(self,filter_date,filter_user,start_date,end_date,filter_supervisor,current_page):
        
        doman = [('active','=',True),('date_deadline','<',fields.Date.today())]

        crm_days_filter = filter_date 
        custom_date_start = start_date
        custom_date_end = end_date  
        company_id = self.env.company       
        if crm_days_filter == 'today':
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            dt_flt1.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt1) )
             
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) )
        elif crm_days_filter == 'yesterday':
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>=')
            prev_day = (datetime.now().date() - relativedelta(days=1)).strftime('%Y/%m/%d')
            dt_flt1.append(prev_day)
            doman.append( tuple(dt_flt1) )
             
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            prev_day = (datetime.now().date() - relativedelta(days=1)).strftime('%Y/%m/%d')                                     
            dt_flt2.append(prev_day)
            doman.append( tuple(dt_flt2) ) 
      
        elif crm_days_filter == 'weekly': # current week 
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(weeks = 1,weekday=0) ).strftime("%Y/%m/%d") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 
            
        elif crm_days_filter == 'prev_week': # Previous week 
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(weeks = 2,weekday=0) ).strftime("%Y/%m/%d") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append( (datetime.now().date()- relativedelta(weeks = 1,weekday=6) ).strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 
           
        elif crm_days_filter == 'monthly': # Current Month                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() ).strftime("%Y/%m/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 

        elif crm_days_filter == 'prev_month': # Previous Month                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(months = 1) ).strftime("%Y/%m/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/01"))
            doman.append( tuple(dt_flt2) ) 
        elif crm_days_filter == 'cur_year': # Current Year                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() ).strftime("%Y/01/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<=')
            dt_flt2.append(datetime.now().date().strftime("%Y/%m/%d"))
            doman.append( tuple(dt_flt2) ) 

        elif crm_days_filter == 'prev_year': # Previous Year                     
           
            dt_flt1 = []
            dt_flt1.append('date_deadline')
            dt_flt1.append('>')
            dt_flt1.append( (datetime.now().date() - relativedelta(years = 1) ).strftime("%Y/01/01") )
            doman.append( tuple(dt_flt1) ) 
            
            dt_flt2 = []
            dt_flt2.append('date_deadline')
            dt_flt2.append('<')
            dt_flt2.append(datetime.now().date().strftime("%Y/01/01"))
            doman.append( tuple(dt_flt2) ) 
           
        elif crm_days_filter == 'custom':
            if custom_date_start and custom_date_end:
                 
                dt_flt1 = []
                dt_flt1.append('date_deadline')
                dt_flt1.append('>')
                dt_flt1.append( datetime.strptime(str(custom_date_start),DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d") )
                doman.append( tuple(dt_flt1) ) 
            
                dt_flt2 = []
                dt_flt2.append('date_deadline')
                dt_flt2.append('<=')
                dt_flt2.append( datetime.strptime(str(custom_date_end),DEFAULT_SERVER_DATE_FORMAT).strftime("%Y/%m/%d"))
                doman.append( tuple(dt_flt2) ) 

#         doman = []
        # FILTER USER
        if filter_user not in ['',"",None,False]:
            doman.append(('|'))
            doman.append(('user_id', '=', int(filter_user)))
            doman.append(('sh_user_ids', 'in', [int(filter_user)]))
        else:
            if self.env.user.has_group('sh_activities_management.group_activity_supervisor')==True and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('user_id', '!=', self.env.user.id))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))
                
            elif self.env.user.has_group('sh_activities_management.group_activity_supervisor')==False and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('|'))
                doman.append(('user_id', '=', self.env.user.id))
                doman.append(('sh_user_ids', 'in', [self.env.user.id]))
        if filter_supervisor not in ['',"",None,False]:
            doman.append(('supervisor_id','=',int(filter_supervisor)))
        else:
            if self.env.user.has_group('sh_activities_management.group_activity_supervisor')==True and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('supervisor_id','=',self.env.user.id))
            elif self.env.user.has_group('sh_activities_management.group_activity_supervisor')==False and self.env.user.has_group('sh_activities_management.group_activity_user')==True and self.env.user.has_group('sh_activities_management.group_activity_manager')==False:
                doman.append(('|'))
                doman.append(('|'))
                doman.append(('supervisor_id','=',self.env.user.id))
                doman.append(('supervisor_id','!=',self.env.user.id))
                doman.append(('supervisor_id','=',False))
        activities = self.env['mail.activity'].sudo().search(
                doman, order='res_id desc')
        total_pages = 0.0
        total_overdue_activities = len(activities.ids)
        record_limit = self.env.company.sh_due_table
        if total_overdue_activities > 0 and record_limit > 0:
            total_pages = math.ceil(float(total_overdue_activities) / float(record_limit))
        current_page = int(current_page)
        start = self.env.company.sh_due_table * (current_page-1)
        stop = current_page * self.env.company.sh_due_table
        activities = activities[start:stop]
        return self.env['ir.ui.view'].with_context().render_template('sh_activities_management.sh_crm_db_activity_overdue_tbl', {
                'activities': activities,
                'overdue_acitvities_count': len(activities.ids),
                'total_pages':total_pages,
                'current_page':current_page,
            })


    @api.model
    def get_user_list(self):
        company_id = self.env.company                           
        domain = [
            ('company_ids','in',[company_id.id])
            ]
        
        users = self.env["res.users"].sudo().search_read(domain)
                           
        return users   



