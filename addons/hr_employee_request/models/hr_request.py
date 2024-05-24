# -*- coding: utf-8 -*-
from datetime import datetime, time , date
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from pytz import timezone, UTC

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import Warning
from odoo.tools.translate import _


class HrRequestType(models.Model):
    _name = 'hr.employee.request.type'
    _rec_name = 'name'
    _sql_constraints = [
        (
            'code_unique', 'unique(code)',
            "Code identifier should be unique and capitalized ! Please choose another one.")]

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Request Code', required=True)
    type = fields.Selection([('hours', 'Hours'), ('days', 'Days'), ('other', 'Both'), ('fixed_amount', 'Fixed Amount')], string='Request Calculations',
                            default='hours')
    fixed_amount = fields.Float()
    validation_type = fields.Selection([('groups', 'Groups'), ('users', 'Users')], required=True, default='groups')
    double_validation = fields.Boolean(string='Double Validation')
    first_validation_user = fields.Many2one(comodel_name='res.users', string='Validation User')
    second_validation_user = fields.Many2one(comodel_name='res.users', string='Validation User 2')
    first_validation_group = fields.Many2one(comodel_name='res.groups', string='Validation Group')
    second_validation_group = fields.Many2one(comodel_name='res.groups', string='Validation Group 2')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    active = fields.Boolean(default=True)


HrRequestType()


class HrRequest(models.Model):
    _name = 'hr.employee.request'
    _rec_name = 'employee_id'
    _order = "date_from desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _mail_post_access = 'read'

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)

    request_date = fields.Date(default=date.today())

    request_type_id = fields.Many2one(
        "hr.employee.request.type", string="Request Type", required=True, readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    display_type = fields.Selection(related='request_type_id.type')
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', index=True, readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, default=_default_employee,
        track_visibility='onchange')
    manager_id = fields.Many2one('hr.employee', string='Manager', readonly=True)
    department_id = fields.Many2one(
        'hr.department', string='Department', readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})

    notes = fields.Text('Reasons', readonly=True,
                        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    date_from = fields.Datetime(
        'Start Date', readonly=True, index=True, copy=False, required=True,
        default=fields.Datetime.now,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, track_visibility='onchange')
    date_to = fields.Datetime(
        'End Date', readonly=True, copy=False, required=True,
        default=fields.Datetime.now,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, track_visibility='onchange')
    number_of_days = fields.Float(
        'Duration (Days)', copy=False, readonly=True, track_visibility='onchange',
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        help='Number of days of the Request request according to your working schedule.')

    request_type = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag')],
        string='Allocation Mode', readonly=True, required=True, default='employee',
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        help='By Employee: Allocation/Request for individual Employee, By Employee Tag: Allocation/Request for group of employees in category')
    category_id = fields.Many2one(
        'hr.employee.category', string='Employee Tag', readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, help='Category of Employee')
    mode_company_id = fields.Many2one(
        'res.company', string='Company', readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})

    validation_type = fields.Selection('Validation Type', related='request_type_id.validation_type', readonly=False)
    request_date_from = fields.Date('Request Start Date')
    request_date_to = fields.Date('Request End Date')

    first_approver_id = fields.Many2one(
        'res.users', string='First Approval', readonly=True, copy=False)
    second_approver_id = fields.Many2one(
        'res.users', string='Second Approval', readonly=True, copy=False)

    user_id = fields.Many2one('res.users', string='User', related='employee_id.user_id', related_sudo=True,
                              compute_sudo=True, store=True, default=lambda self: self.env.uid, readonly=True)
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('cancel', 'Canceled'),
                                        ('refuse', 'Refused'),
                                        ('confirm', 'Confirm'),
                                        ('validate', 'Validate'),
                                        ('done', 'Done')], default='draft', required=True)
    no_days = fields.Float(default=0.00, string='Number of Days')
    no_hours = fields.Float(default=0.00, string='Number of Hours')
    payslip_status = fields.Boolean('Reported in last payslips',
                                    help='Green this button when the Request has been taken into account in the payslip.')
    number_of_days_display = fields.Float(
        'Duration in days', compute='_compute_number_of_days_display', copy=False, readonly=True,
        help='Number of days of the  request. Used for interface.')
    number_of_hours_display = fields.Float(
        'Duration in hours', compute='_compute_number_of_hours_display', copy=False, readonly=True,
        help='Number of hours of the request according to your working schedule. Used for interface.')
    fixed_amount_display = fields.Float(
        'Fixed Amount', compute='_compute_fixed_amount_display', copy=False, readonly=True, )

    _sql_constraints = [
        ('type_value',
         "CHECK((request_type='employee' AND employee_id IS NOT NULL) or "
         "(request_type='company' AND mode_company_id IS NOT NULL) or "
         "(request_type='category' AND category_id IS NOT NULL) or "
         "(request_type='department' AND department_id IS NOT NULL) )",
         "The employee, department, company or employee category of this request is missing. Please make sure that your user login is linked to an employee."),
        ('date_check2', "CHECK ((date_from <= date_to))", "The start date must be anterior to the end date."),
        ('duration_check', "CHECK ( number_of_days >= 0 )",
         "If you want to change the number of days you should use the 'period' mode"),
    ]

    @api.model
    def get_users_from_group(self, group_id):
        users_ids = []
        sql_query = """select uid from res_groups_users_rel where gid = %s"""
        params = (group_id,)
        self.env.cr.execute(sql_query, params)
        results = self.env.cr.fetchall()
        for users_id in results:
            users_ids.append(users_id[0])
        return users_ids

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_refuse(self):
        for rec in self:
            rec.state = 'refuse'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_confirm(self):
        for rec in self:
            if rec.request_type_id.double_validation:
                rec.state = 'confirm'
            else:
                rec.state = 'validate'

    def action_approve(self):
        for rec in self:
            if rec.validation_type == 'users':
                if self.env.user.id == rec.request_type_id.first_validation_user.id:
                    rec.first_approver_id = self.env.user.id
                    rec.state = 'validate'
                else:
                    raise Warning(_("You are not auth to make the approval on this request"))
            else:
                if self.env.user.id in self.get_users_from_group(rec.request_type_id.first_validation_group.id):
                    rec.first_approver_id = self.env.user.id
                    rec.state = 'validate'
                else:
                    raise Warning(_("You are not auth to make the approval on this request"))

    def action_validate(self):
        for rec in self:
            if rec.request_type_id.double_validation:
                if rec.validation_type == 'users':
                    if self.env.user.id == rec.request_type_id.second_validation_user.id:
                        rec.second_approver_id = self.env.user.id
                        rec.state = 'done'
                    else:
                        raise Warning(_("You are not auth to make the approval on this request"))
                else:
                    if self.env.user.id in self.get_users_from_group(rec.request_type_id.second_validation_group.id):
                        rec.second_approver_id = self.env.user.id
                        rec.state = 'done'
                    else:
                        raise Warning(_("You are not auth to make the approval on this request"))
            else:
                if rec.validation_type == 'users':
                    if self.env.user.id == rec.request_type_id.first_validation_user.id:
                        rec.first_approver_id = self.env.user.id
                        rec.second_approver_id = self.env.user.id
                        rec.state = 'done'
                    else:
                        raise Warning(_("You are not auth to make the approval on this request"))
                else:
                    if self.env.user.id in self.get_users_from_group(rec.request_type_id.first_validation_group.id):
                        rec.first_approver_id = self.env.user.id
                        rec.second_approver_id = self.env.user.id
                        rec.state = 'done'
                    else:
                        raise Warning(_("You are not auth to make the approval on this request"))

    @api.onchange('request_date_from', 'request_date_to',
                  'employee_id')
    def _onchange_request_parameters(self):
        if self.request_date_from and self.request_date_to:
            domain = [('calendar_id', '=',
                       self.employee_id.resource_calendar_id.id or self.env.user.company_id.resource_calendar_id.id)]
            attendances = self.env['resource.calendar.attendance'].search(domain, order='dayofweek, day_period DESC')
            attendance_from = next(
                (att for att in attendances if int(att.dayofweek) >= self.request_date_from.weekday()),
                attendances[0])
            attendance_to = next(
                (att for att in reversed(attendances) if int(att.dayofweek) <= self.request_date_to.weekday()),
                attendances[-1])
            hour_from = float_to_time(attendance_from.hour_from)
            hour_to = float_to_time(attendance_to.hour_to)
            tz = self.env.user.tz if self.env.user.tz else 'UTC'
            self.date_from = timezone(tz).localize(datetime.combine(self.request_date_from, hour_from)).astimezone(
                UTC).replace(tzinfo=None)
            self.date_to = timezone(tz).localize(datetime.combine(self.request_date_to, hour_to)).astimezone(
                UTC).replace(
                tzinfo=None)
            self._onchange_leave_dates()

    @api.onchange('request_type')
    def _onchange_type(self):
        if self.request_type == 'employee':
            if not self.employee_id:
                self.employee_id = self.env.user.employee_ids[:1].id
            self.mode_company_id = False
            self.category_id = False
        elif self.request_type == 'company':
            self.employee_id = False
            if not self.mode_company_id:
                self.mode_company_id = self.env.user.company_id.id
            self.category_id = False
        elif self.request_type == 'department':
            self.employee_id = False
            self.mode_company_id = False
            self.category_id = False
            if not self.department_id:
                self.department_id = self.env.user.employee_ids[:1].department_id.id
        elif self.request_type == 'category':
            self.employee_id = False
            self.mode_company_id = False
            self.department_id = False

    def _sync_employee_details(self):
        for request in self:
            if request.employee_id:
                request.department_id = request.employee_id.department_id

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self._sync_employee_details()
        self.holiday_status_id = False

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _onchange_leave_dates(self):
        if self.date_from and self.date_to:
            self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id)
        else:
            self.number_of_days = 0

    @api.depends('request_type_id')
    def _compute_fixed_amount_display(self):
        for request in self:
            if request.request_type_id.type == 'fixed_amount':
                request.fixed_amount_display = request.request_type_id.fixed_amount
            else:
                request.fixed_amount_display = 0

    @api.depends('number_of_days')
    def _compute_number_of_days_display(self):
        for request in self:
            request.number_of_days_display = request.number_of_days

    @api.depends('number_of_days')
    def _compute_number_of_hours_display(self):
        for request in self:
            calendar = request.employee_id.resource_calendar_id or self.env.user.company_id.resource_calendar_id
            if request.date_from and request.date_to:
                number_of_hours = calendar.get_work_hours_count(request.date_from, request.date_to)
                request.number_of_hours_display = number_of_hours or (request.number_of_days * HOURS_PER_DAY)
            else:
                request.number_of_hours_display = 0

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for request in self:
            domain = [
                ('date_from', '<', request.date_to),
                ('date_to', '>', request.date_from),
                ('employee_id', '=', request.employee_id.id),
                ('id', '!=', request.id),
                ('state', 'not in', ['cancel', 'refuse']),
            ]
            n_reqests = self.search_count(domain)
            if n_reqests:
                raise ValidationError(_('You can not have 2 requests that overlaps on the same day.'))

    @api.model
    def _get_number_of_days(self, date_from, date_to, employee_id):
        """ Returns a float equals to the timedelta between two dates given as string."""
        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            return employee.get_work_days_data(date_from, date_to)['days']

        today_hours = self.env.user.company_id.resource_calendar_id.get_work_hours_count(
            datetime.combine(date_from.date(), time.min),
            datetime.combine(date_from.date(), time.max),
            False)

        return self.env.user.company_id.resource_calendar_id.get_work_hours_count(date_from, date_to) / (
                today_hours or HOURS_PER_DAY)

    @api.model
    def create(self, values):
        employee_id = values.get('employee_id', False)
        if not values.get('department_id'):
            values.update({'department_id': self.env['hr.employee'].browse(employee_id).department_id.id})
        res = super(HrRequest,
                    self.with_context(mail_create_nolog=True, mail_create_nosubscribe=True)).create(values)
        return res

    def copy_data(self, default=None):
        raise UserError(_('A request cannot be duplicated.'))

    def unlink(self):
        for request in self.filtered(lambda holiday: holiday.state not in ['draft', 'cancel', 'confirm']):
            raise UserError(_('You cannot delete a request which is in %s state.') % (request.state,))
        return super(HrRequest, self).unlink()


HrRequest()
