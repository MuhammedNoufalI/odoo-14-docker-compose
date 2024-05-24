# -*- coding: utf-8 -*-

import math
from odoo import api, fields, models
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools import float_compare
from odoo.tools.translate import _
from datetime import datetime, date
from datetime import timedelta


class HrHolidays(models.Model):
    _inherit = 'hr.leave'
    #
    # date_from = fields.Datetime('Start Date', readonly=True, index=True, copy=False,required=True,default=fields.Date.today,
    #                             states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, track_visibility='onchange')
    # date_to = fields.Datetime('End Date', readonly=True, copy=False,required=True,default=fields.Date.today,
    #                           states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, track_visibility='onchange')
    #
    permission_type = fields.Selection(string="Permission Type",
                                       selection=[('morning', 'Morning'), ('afternoon', 'Afternoon'), ],
                                       required=False, )
    is_hours = fields.Boolean(compute='check_type_is_hour')

    @api.depends('holiday_status_id')
    def check_type_is_hour(self):
        for rec in self:
            if rec.holiday_status_id.request_unit == 'hour':
                rec.is_hours = True
            else:
                rec.is_hours = False

    # @api.multi
    def _sync_employee_details(self):
        for holiday in self:
            holiday.manager_id = holiday.employee_id.parent_id.id
            if holiday.employee_id:
                holiday.department_id = holiday.employee_id.department_id

    # @api.model
    # def _get_number_of_days(self, request_date_from, request_date_to, employee_id):
    #     """ Returns a float equals to the timedelta between two dates given as string."""
    #     from_dt = fields.Datetime.from_string(request_date_from)
    #     to_dt = fields.Datetime.from_string(request_date_to)
    #
    #     tomorow_date =date.today() + timedelta(days=1)
    #     dif_date = tomorow_date - date.today()
    #     # #print(dif_date)
    #
    #     # if employee_id:
    #     #     employee = self.env['hr.employee'].browse(employee_id)
    #     #     resource = employee.resource_id.sudo()
    #     #     if resource and resource.calendar_id:
    #     #         hours = resource.calendar_id.get_working_hours(from_dt, to_dt, resource_id=resource.id,
    #     #                                                        compute_leaves=True)
    #     #         uom_hour = resource.calendar_id.uom_id
    #     #         uom_day = self.env.ref('product.product_uom_day')
    #     #         if uom_hour and uom_day:
    #     #             return uom_hour._compute_quantity(hours, uom_day)
    #     ############################### edit
    #     if to_dt > from_dt:
    #         time_delta = (to_dt - from_dt) + dif_date
    #         return math.ceil(time_delta.days + float(time_delta.seconds) / 86400)
    #     if to_dt == from_dt:
    #         time_delta = dif_date
    #         return math.ceil(time_delta.days + float(time_delta.seconds) / 86400)
    #     ################################ edit

    def send_mail(self, obj_id, subject, email_to, body_html):
        values = {}
        ir_model_data = self.env['ir.model.data']
        template = \
            ir_model_data.get_object_reference('gm_hr_custom', 'holidays_send_mail')[1]
        # #print '-------------------------', template

        email_template_obj = self.env['mail.template']

        template_ids = email_template_obj.browse(template)
        # #print '-------------------------', template_ids
        object = self.env['hr.leave'].browse(obj_id).sudo()
        employee = ""
        if object.employee_id.name:
            employee = object.employee_id.name

        # if template_ids:
        #     values = email_template_obj.generate_email(cr, uid, template, ids, context=context)
        int_obj = self.env['res.company']
        int_cmp = int_obj.search([], limit=1)
        # values['name'] = template_ids.name
        values['subject'] = subject
        # values['model_id'] = template_ids.model_id
        values['email_from'] = int_cmp.email or ''
        # values['lang'] = template_ids.lang
        values['auto_delete'] = True
        values['email_to'] = email_to.email
        values['body_html'] = \
            u"".join(u'<![CDATA["<div style="text-align: right;direction:rtl">' +
                     u'<p dir="rtl" style="text-align: right"> السيد %s </p>' % (email_to.name) +
                     u'<p style="font-size: 1.1em;text-align: right">السلام عليكم ورحمة الله.</p>' +
                     u'<br/><br/>' +
                     u'<p dir="rtl" style="text-align: right">' + u'وصف الاجازة:%s' % (object.name) + u' </p>' +
                     u'<br/>' +
                     u'<p dir="rtl" style="text-align: right">طالب الاجازه   %s  </p>' % (employee) +
                     u'<br/>' +
                     u'<p style="font-size: 1.1em;text-align: right;">' +
                     u'</p></div>')
        values['body'] = template_ids.body_html
        values['res_id'] = False
        mail_mail_obj = self.env['mail.mail']
        msg_id = mail_mail_obj.create(values)
        if msg_id:
            mail_mail_obj.send([msg_id])
        return True

    @api.model
    def create(self, values):
        res = super(HrHolidays, self).create(values)
        if self.env.context.get('import_file'):
            return res
        else:
            template = self.env.ref('gm_hr_custom.holidays_send_mail', False)
            group_id = self.env.ref('hr_holidays.group_hr_holidays_manager')
            users = []
            for rec in group_id.users:
                print("users", rec.name)
                users.append(rec.partner_id.id)
            thread_pool = self.env['mail.thread']
            thread_pool.message_notify(
                partner_ids=users,
                subject="تم انشاء طلب اجازة",
                body=template.body_html,
                email_from=self.env.user.company_id.email, )
            recipient_partners_1 = []
            for user in self.env['hr.employee'].browse(values.get('employee_id')).department_id.manager_id.user_id:
                recipient_partners_1.append(user.partner_id.id)
                thread_pool = self.env['mail.thread']
                thread_pool.message_post(
                    type="notification",
                    subtype="mt_comment",
                    subject="Leave Notification",
                    body="Employee : ( " + self.env['hr.employee'].browse(
                        values.get('employee_id')).name + " ) has a leave request. ",
                    partner_ids=user.partner_id.id)
            return res

    # @api.multi
    def action_approve(self):
        recipient_partners_2 = []
        res = super(HrHolidays, self).action_approve()
        template = self.env.ref('gm_hr_custom.holidays_send_mail', False)
        for rec in self.env['res.users'].search([]).filtered(
                lambda user: user.has_group('hr_holidays.group_hr_holidays_manager')).mapped('partner_id'):
            if not template:
                return
            subject = "تم قبول طلب الاجازة"
            email_to = rec
            body_html = template.body_html
            self.sudo().send_mail(self.id, subject, email_to, body_html)
        if self.holiday_status_id.leave_validation_type:
            # #print("double_validationdouble_validationdouble_validationdouble_validationdouble_validation")
            for user in self.env.ref('hr.group_hr_manager').users:
                recipient_partners_2.append(user.partner_id.id)
            post_vars = {'subject': "Leave Notification",
                         'body': "Employee : ( " + self.employee_id.name + " ) has a leave request. ",
                         'partner_ids': user.partner_id.id}
            thread_pool = self.env['mail.thread']
            thread_pool.message_notify(
                partner_ids=recipient_partners_2,
                subject="Leave Notification ",
                body="Employee : ( " + self.employee_id.name + " ) has a leave request. ",
                email_from=self.env.user.company_id.email, )

        return res

    # @api.multi
    def action_validate(self):
        res = super(HrHolidays, self).action_validate()
        template = self.env.ref('gm_hr_custom.holidays_send_mail', False)
        for rec in self.env['res.users'].search([]).filtered(
                lambda user: user.has_group('hr_holidays.group_hr_holidays_manager')).mapped('partner_id'):
            if not template:
                return
            subject = "تم قبول طلب الاجازة"
            email_to = rec
            body_html = template.body_html
            self.sudo().send_mail(self.id, subject, email_to, body_html)
        return res

    # @api.multi
    def action_refuse(self):
        res = super(HrHolidays, self).action_refuse()
        template = self.env.ref('gm_hr_custom.holidays_send_mail', False)
        for rec in self.env['res.users'].search([]).filtered(
                lambda user: user.has_group('hr_holidays.group_hr_holidays_manager')).mapped('partner_id'):
            if not template:
                return
            subject = "تم رفض طلب الاجازه"
            email_to = rec
            body_html = template.body_html
            self.sudo().send_mail(self.id, subject, email_to, body_html)
        return res


class HrHolidayStatus(models.Model):
    _inherit = 'hr.leave.type'

    is_permission = fields.Boolean(string="Is Permission", )
