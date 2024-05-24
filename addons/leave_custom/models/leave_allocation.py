from dateutil.relativedelta import relativedelta
from pytz import timezone, UTC
from datetime import datetime, time
from odoo.addons.resource.models.resource import HOURS_PER_DAY

from odoo import models, fields, api, _, exceptions


class Leave(models.Model):
    _inherit = "hr.leave"

    @api.constrains('request_date_from', 'request_date_to')
    def check_leave_recursive_limit(self):
        if self.env.company.limit_last_days:
            for rec in self:
                if rec.request_date_from and rec.request_date_to:
                    to_date = fields.date.today() + relativedelta(days=-self.env.company.limit_last_days)
                    if rec.request_date_from < to_date:
                        raise exceptions.ValidationError("You can't request leave before {}".format(to_date))


class LeaveType(models.Model):
    _inherit = "hr.leave.type"

    is_leave = fields.Boolean()
    is_sick_leave = fields.Boolean()
    schedule_create = fields.Boolean('Use In Monthly Auto. Allocation')

    schedule_allocation = fields.Boolean(string='Schedule Allocation?', default=False)
    period_type = fields.Selection(string="Period Type", selection=[('monthly', 'Monthly'), ('annual', 'Annual'), ],
                                   required=False, )
    period = fields.Integer()
    day = fields.Integer()
    month = fields.Selection(string="Month",
                             selection=[('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                                        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), ('9', 'September'),
                                        ('10', 'October'), ('11', 'November'), ('12', 'December')], required=False, )
    notified_user_ids = fields.Many2many('res.users', 'notified_user_type_rel', 'userid', 'leave_type_id',
                                         string='Notified Users')
    allocation_days = fields.Float('Days Allocation', help="Number of Days Allocation for Accrual Leaves")
    allocation_for_male = fields.Boolean()
    allocation_for_female = fields.Boolean()


class LeaveAllocation(models.Model):
    _inherit = "hr.leave.allocation"
    date_from = fields.Date()
    date_to = fields.Date()
    active = fields.Boolean(default=True)
    schedule_create = fields.Boolean(copy=False)
    accumulated_leave_balance = fields.Float("Accumulated Leave Balance")

    schedule_allocation = fields.Boolean(string='Schedule Allocation?', default=False)
    period_type = fields.Selection(string="Period Type", selection=[('monthly', 'Monthly'), ('annual', 'Annual'), ],
                                   required=False, )
    period = fields.Integer()
    day = fields.Integer()
    month = fields.Selection(string="Month",
                             selection=[('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                                        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), ('9', 'September'),
                                        ('10', 'October'), ('11', 'November'), ('12', 'December')], required=False, )
    notified_user_ids = fields.Many2many('res.users', string='Notified Users')
    sixth_month_compleat = fields.Boolean('6th Month Compleat')
    one_year_bonus = fields.Boolean("Bonus")

    # recurring_leave = fields.Boolean()
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')])
    negative_balance = fields.Integer("Negative Balance")

    # @api.constrains('recurring_leave')
    # def check_for_date_restrictions(self):
    #     if self.holiday_status_id.

    def _action_validate_create_childs(self):
        childs = self.env['hr.leave.allocation']
        if self.state == 'validate' and self.holiday_type in ['category', 'department', 'company']:
            if self.holiday_type == 'category':
                employees = self.category_id.employee_ids
            elif self.holiday_type == 'department':
                employees = self.department_id.member_ids
            else:
                employees = self.env['hr.employee'].search([('company_id', '=', self.mode_company_id.id)])

            if self.gender:
                employees = employees.filtered(lambda x: x.gender == self.gender)
            for employee in employees:
                childs += self.with_context(
                    mail_notify_force_send=False,
                    mail_activity_automation_skip=True
                ).create(self._prepare_holiday_values(employee))
            # TODO is it necessary to interleave the calls?
            childs.action_approve()
            if childs and self.validation_type == 'both':
                childs.action_validate()
        return childs

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for line in self:
            if line.date_to and line.date_from and line.date_to <= line.date_from:
                raise exceptions.ValidationError('Date To Must Be Greater Than Date From!')

    def post_close(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'allocation.post',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_allocation_id': self.id,
                        'default_period': self.number_of_days_display - self.leaves_taken}
        }

    def activity_update(self):
        # super(LeaveAllocation, self.with_context(change_sender=True)).activity_update()
        to_clean, to_do = self.env['hr.leave.allocation'], self.env['hr.leave.allocation']
        for allocation in self:
            note = _('New Allocation Request created by %s: %s Days of %s') % (
                allocation.create_uid.name, allocation.number_of_days, allocation.holiday_status_id.name)
            if allocation.state == 'draft':
                to_clean |= allocation
            elif allocation.state == 'confirm':
                allocation.activity_schedule(
                    'hr_holidays.mail_act_leave_allocation_approval',
                    note=note,
                    user_id=allocation.sudo()._get_responsible_for_approval().id or self.env.user.id)
                for user in self.env.ref('leave_custom.group_timeoff_notification').users:
                    allocation.activity_schedule(
                        'hr_holidays.mail_act_leave_allocation_approval',
                        note=note,
                        user_id=user.id)
            elif allocation.state == 'validate1':
                allocation.activity_feedback(['hr_holidays.mail_act_leave_allocation_approval'])
                allocation.activity_schedule(
                    'hr_holidays.mail_act_leave_allocation_second_approval',
                    note=note,
                    user_id=allocation.sudo()._get_responsible_for_approval().id or self.env.user.id)
                for user in self.env.ref('leave_custom.group_timeoff_notification').users:
                    allocation.activity_schedule(
                        'hr_holidays.mail_act_leave_allocation_second_approval',
                        note=note,
                        user_id=user.id)
            elif allocation.state == 'validate':
                to_do |= allocation
            elif allocation.state == 'refuse':
                to_clean |= allocation
            ############################

            notify = self.env['user.notify']
            users = self.holiday_status_id.notified_user_ids + self.env.ref(
                'leave_custom.group_timeoff_notification').users
            if users:
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                subject = 'Leave Allocation'
                if not self.env.context.get('mail_create_nosubscribe'):
                    state = self.state
                    if self.state == 'draft':
                        state = 'To Submit'
                    elif self.state == 'cancel':
                        state = 'Canceled'
                    elif self.state == 'confirm':
                        state = 'To Approve'
                    elif self.state == 'refuse':
                        state = 'Refused'
                    elif self.state == 'validate1':
                        state = 'Second Approval'
                    elif self.state == 'validate':
                        state = 'Approved'
                    note = 'Leave Allocation Status converted to {}'.format(state)
                body = note + ' click here to open: <a target=_BLANK href="{}/web?#id='.format(
                    base_url) + str(
                    self.id) + '&view_type=form&model=hr.leave.allocation&action=" style="font-weight: bold">' + str(
                    self.holiday_status_id.name) + '</a>'
                if self.state not in ['draft', 'confirm']:
                    notify.send_user_notification(users, self,subject, body)
            ############################
        if to_clean:
            to_clean.activity_unlink(['hr_holidays.mail_act_leave_allocation_approval',
                                      'hr_holidays.mail_act_leave_allocation_second_approval'])
        if to_do:
            to_do.activity_feedback(['hr_holidays.mail_act_leave_allocation_approval',
                                     'hr_holidays.mail_act_leave_allocation_second_approval'])

    @api.depends('holiday_status_id', 'allocation_type', 'number_of_hours_display', 'number_of_days_display')
    def _compute_from_holiday_status_id(self):
        for allocation in self:
            allocation.number_of_days = allocation.number_of_days_display
            if allocation.type_request_unit == 'hour':
                allocation.number_of_days = allocation.number_of_hours_display / (
                        allocation.employee_id.sudo().resource_calendar_id.hours_per_day or HOURS_PER_DAY)

            # set default values
            if not allocation.interval_number and not allocation._origin.interval_number:
                allocation.interval_number = 1
            if not allocation.number_per_interval and not allocation._origin.number_per_interval:
                allocation.number_per_interval = 1
            if not allocation.unit_per_interval and not allocation._origin.unit_per_interval:
                allocation.unit_per_interval = 'hours'
            if not allocation.interval_unit and not allocation._origin.interval_unit:
                allocation.interval_unit = 'weeks'

            if allocation.holiday_status_id.validity_stop and allocation.date_to:
                new_date_to = datetime.combine(allocation.holiday_status_id.validity_stop, time.max)
                if new_date_to < datetime.combine(allocation.date_to, time.max):
                    allocation.date_to = new_date_to.date()

            if allocation.allocation_type == 'accrual':
                if allocation.holiday_status_id.request_unit == 'hour':
                    allocation.unit_per_interval = 'hours'
                else:
                    allocation.unit_per_interval = 'days'
            else:
                allocation.interval_number = 1
                allocation.interval_unit = 'weeks'
                allocation.number_per_interval = 1
                allocation.unit_per_interval = 'hours'

    @api.onchange('allocation_type', 'date_from', 'number_per_interval', 'unit_per_interval', 'interval_number',
                  'interval_unit', 'accumulated_leave_balance')
    def compute_days_to_be_added(self):
        if self.allocation_type == 'accrual':
            if fields.Date.today() and self.date_from and fields.Date.today() > self.date_from:
                if self.interval_unit == 'days':
                    difference = (fields.Date.today() - self.date_from).days
                elif self.interval_unit == 'weeks':
                    difference = (fields.Date.today().isocalendar()[0] - self.date_from.isocalendar()[0]) * 52 + (
                            fields.Date.today().isocalendar()[1] - self.date_from.isocalendar()[1])
                elif self.interval_unit == 'months':
                    difference = (fields.Date.today().year - self.date_from.year) * 12 + (
                            fields.Date.today().month - self.date_from.month)
                elif self.interval_unit == 'years':
                    difference = fields.Date.today().year - self.date_from.year
                if self.unit_per_interval == 'hours':
                    self.number_of_days_display = (
                                                          difference * self.number_per_interval) / 24 + self.accumulated_leave_balance
                if self.unit_per_interval == 'days':
                    self.number_of_days_display = difference * self.number_per_interval + self.accumulated_leave_balance

    def update_allocations_for_users(self):
        allocation_leaves = self.search([('allocation_type', '=', 'accrual'), ('schedule_allocation', '=', True)])
        allocation_leaves = allocation_leaves.filtered(lambda
                                                           x: x.number_per_interval != x.holiday_status_id.allocation_days and x.holiday_status_id.allocation_days > 0)
        for al in allocation_leaves:
            if fields.Date.today() == datetime(day=al.day, month=int(al.month), year=al.period).date():
                al.sudo().write({
                    'number_per_interval': al.holiday_status_id.allocation_days
                })


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    def activity_update(self):
        # super(HolidaysRequest, self).activity_update()
        to_clean, to_do = self.env['hr.leave'], self.env['hr.leave']
        for holiday in self:
            start = UTC.localize(holiday.date_from).astimezone(timezone(holiday.employee_id.tz or 'UTC'))
            end = UTC.localize(holiday.date_to).astimezone(timezone(holiday.employee_id.tz or 'UTC'))
            note = _('New %s Request created by %s from %s to %s') % (
                holiday.holiday_status_id.name, holiday.create_uid.name, start, end)
            if holiday.state == 'draft':
                to_clean |= holiday
            elif holiday.state == 'confirm':
                holiday.activity_schedule(
                    'hr_holidays.mail_act_leave_approval',
                    note=note,
                    user_id=holiday.sudo()._get_responsible_for_approval().id or self.env.user.id)
                for user in self.env.ref('leave_custom.group_timeoff_notification').users:
                    holiday.activity_schedule(
                        'hr_holidays.mail_act_leave_approval',
                        note=note,
                        user_id=user.id)
            elif holiday.state == 'validate1':
                holiday.activity_feedback(['hr_holidays.mail_act_leave_approval'])
                holiday.activity_schedule(
                    'hr_holidays.mail_act_leave_second_approval',
                    note=note,
                    user_id=holiday.sudo()._get_responsible_for_approval().id or self.env.user.id)
                for user in self.env.ref('leave_custom.group_timeoff_notification').users:
                    holiday.activity_schedule(
                        'hr_holidays.mail_act_leave_second_approval',
                        note=note,
                        user_id=user.id)
            elif holiday.state == 'validate':
                to_do |= holiday
            elif holiday.state == 'refuse':
                to_clean |= holiday
            ##########################
            notify = self.env['user.notify']
            users = self.holiday_status_id.notified_user_ids + self.env.ref(
                'leave_custom.group_timeoff_notification').users
            if users:
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                subject = 'Leave Request'
                if not self.env.context.get('mail_create_nosubscribe'):
                    state = self.state
                    if self.state == 'draft':
                        state = 'To Submit'
                    elif self.state == 'cancel':
                        state = 'Canceled'
                    elif self.state == 'confirm':
                        state = 'To Approve'
                    elif self.state == 'refuse':
                        state = 'Refused'
                    elif self.state == 'validate1':
                        state = 'Second Approval'
                    elif self.state == 'validate':
                        state = 'Approved'
                    note = 'Leave Request Status converted to {}'.format(state)
                body = note + ' click here to open: <a target=_BLANK href="{}/web?#id='.format(
                    base_url) + str(
                    self.id) + '&view_type=form&model=hr.leave&action=" style="font-weight: bold">' + str(
                    self.holiday_status_id.name) + '</a>'
                if self.state not in ['draft', 'confirm']:
                    notify.send_user_notification(users, self,subject, body)
            ##########################
        if to_clean:
            to_clean.activity_unlink(
                ['hr_holidays.mail_act_leave_approval', 'hr_holidays.mail_act_leave_second_approval'])
        if to_do:
            to_do.activity_feedback(
                ['hr_holidays.mail_act_leave_approval', 'hr_holidays.mail_act_leave_second_approval'])

    # @api.constrains('request_date_from', 'request_date_to', 'holiday_status_id')
    # def check_ability(self):
    #     for rec in self:
    #         if rec.holiday_status_id and rec.holiday_status_id.schedule_allocation and rec.request_date_from and rec.request_date_to:
    #             allocations = self.env['hr.leave.allocation'].search(
    #                 [('active', '=', True), ('date_from', '<=', rec.request_date_from),
    #                  ('date_to', '>=', rec.request_date_to), ('holiday_status_id', '=', rec.holiday_status_id.id)])
    #             if not any(alloc.number_of_days - alloc.leaves_taken >= rec.number_of_days for alloc in allocations):
    #                 raise exceptions.ValidationError("You aren't allowed to create leave in this dates")
