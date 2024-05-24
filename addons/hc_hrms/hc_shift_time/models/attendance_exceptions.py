# -*- coding: utf-8 -*-

import calendar

import simplejson
from lxml import etree
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HcAttendanceExceptions(models.Model):
    _name = 'hc.attendance.exception'
    _description = 'Hc Attendance Exceptions'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super(HcAttendanceExceptions, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                                  submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            for node in doc.xpath("//field"):
                modifiers = simplejson.loads(node.get("modifiers"))
                if 'readonly' not in modifiers:
                    modifiers['readonly'] = [['state', '!=', 'draft']]
                else:
                    if type(modifiers['readonly']) != bool:
                        modifiers['readonly'].insert(0, '|')
                        modifiers['readonly'] += [['state', '!=', 'draft']]
                node.set('modifiers', simplejson.dumps(modifiers))
                res['arch'] = etree.tostring(doc)
        return res

    name = fields.Char('Name', readonly=1)
    employee_id = fields.Many2one('hr.employee', string="Employee", tracking=True)
    notes = fields.Char('Notes', tracking=True)
    badge_number = fields.Char('Badge Number', tracking=True, compute='_get_employee_badge_number')
    datetime = fields.Datetime('Date Time', tracking=True)
    check_in = fields.Datetime(string="Checkin", tracking=True)
    check_out = fields.Datetime(string="Checkout", tracking=True)
    date = fields.Date(string="Date", compute='_compute_datetime_hc', tracking=True)
    attendance_id = fields.Many2one('hc.raw.attendance', string="Raw Attendance ID", tracking=True)
    branch_id = fields.Many2one('hc.branch', string="Branch", tracking=True, compute='_get_employee_branch_id')
    state = fields.Selection(
        [('draft', 'Draft'), ('requested', 'Exception Requested'), ('approved', 'Approve'), ('processed', 'Processed'),
         ('denied', 'denied')],
        string='State', required=True, default='draft', tracking=True)
    comments = fields.Text(string="Employee Comments",
                           help="Employee Can add the comments as in the reason for the exception ", tracking=True)
    resource_calendar_id = fields.Many2one('resource.calendar', string="Working Time",
                                           compute='_get_employee_working_time', tracking=True)
    is_missed_punch = fields.Boolean(string='Is Missed Punch', tracking=True)
    exception_line_ids = fields.One2many('hc.raw.attendance', 'exception_id', string="Exception Lines")
    hc_exception_line_ids = fields.One2many('hc.attendance.exception', 'id', string="HC Exception Lines")
    comp_exception_line_ids = fields.One2many('hc.attendance.exception', 'id', string="Exceptions")
    attendance_line_ids = fields.One2many('hr.attendance', 'exception_id', string="Attendance Ids")
    comp_attendance_line_ids = fields.One2many('hr.attendance', string="Attendance Lines",
                                               compute='_domain_attendance_list')

    raw_attendance_line_ids = fields.One2many('hc.raw.attendance', 'exception_id', string="Raw Attendance Ids", )

    def _get_employee_branch_id(self):
        for rec in self:
            if rec.employee_id.branch_id:
                rec.branch_id = rec.employee_id.branch_id.id
            else:
                rec.branch_id = False

    def _get_employee_badge_number(self):
        for rec in self:
            if rec.employee_id.oe_emp_sequence:
                rec.badge_number = rec.employee_id.oe_emp_sequence
            else:
                rec.badge_number = False

    def _get_employee_working_time(self):
        for rec in self:
            if rec.employee_id:
                contract = rec.employee_id.contract_ids.filtered(lambda emp: emp.state == 'open' or 'probation')
                if contract.resource_calendar_id:
                    rec.write({'resource_calendar_id': contract.resource_calendar_id.id})
                else:
                    rec.write({'resource_calendar_id': False})

    def _compute_datetime_hc(self):
        for rec in self:
            if rec.datetime:
                rec.write({'date': rec.datetime.date()})
            else:
                rec.date = None

    def _domain_attendance_list(self):
        for rec in self:
            if rec.create_date:
                rec.comp_attendance_line_ids = self.attendance_line_ids.search([('date', '=', rec.create_date.date()),
                                                                                ('employee_id', '=',
                                                                                 rec.employee_id.id)])

    @api.model_create_multi
    def create(self, vals):
        for rec in vals:
            if rec.get('name', _('New')) == _('New'):
                rec['name'] = self.env['ir.sequence'].next_by_code('exception.data.sequence') or _('New')

        return super(HcAttendanceExceptions, self).create(vals)

    def create_exception_request(self):
        for rec in self:
            if not rec.comments:
                raise UserError(_('Please Add the Comments Before Requesting!'))
            rec.write({'state': 'requested'})

    def button_approve(self):
        for rec in self:
            rec.write({'state': 'approved'})

    def button_deny(self):
        for rec in self:
            rec.write({'state': 'denied'})

    def button_hr_approve(self):
        for rec in self:
            allowed_missed_punch = rec.employee_id.branch_id.allowed_missed_punch_count
            max_day_in_month = \
                calendar.monthrange(rec.date.year, rec.date.month)[1]
            from_date = rec.date.replace(day=1)
            to_date = rec.date.replace(day=max_day_in_month)
            attendances = self.env['hr.attendance'].search([('employee_id', '=', rec.employee_id.id),
                                                            ('create_date', '<', to_date),
                                                            ('create_date', '>=', from_date),
                                                            ('is_missed_punch', '=', True)])
            if len(attendances) > allowed_missed_punch:
                raise ValidationError(
                    _('Sorry, Limit for updating The Missed Check In/Check Out for the Employee for this Month is Exceeded.'
                      'Please Contact Your Administrator!'))

            rec.write({'state': 'processed'})
        for raw in self.raw_attendance_line_ids:
            raw.write({'state': 'fixed'})
        for attendance in self.comp_attendance_line_ids:
            attendance.write({'is_missed_punch': self.is_missed_punch})
        # Create Attendance
        self.env['hc.raw.attendance'].calculate_attendance()

