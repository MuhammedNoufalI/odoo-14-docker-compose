# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EmployeeAttendances(models.Model):
    _name = 'employee.attendance.payslip'

    employee_id = fields.Many2one("hr.employee", "employee_id")
    check_in = fields.Datetime("Shift Check In")
    check_out = fields.Datetime("Shift Check Out")
    actual_checkin = fields.Datetime("Actual Check In")
    actual_check_out = fields.Datetime("Actual Check Out")
    mandatory_hours = fields.Float("Shift Mandatory Hours")
    actual_mandatory_hours = fields.Float("Actual Mandatory Hours")
    checked_in_hours = fields.Float("Checked in Hours")

    extra_hours = fields.Float(string="Extra Hours", tracking=True)
    break_hours = fields.Float(string="Break Hours", tracking=True)
    resource_calendar_id = fields.Many2one('resource.calendar', string="Working Time", tracking=True)
    late_hour = fields.Float(string="Late Hours", tracking=True)
    early_hour = fields.Float(string="Early Hours", tracking=True)
    flexible_break_hour = fields.Float(string="Shift Flexible Break Hours",
                                       help="Flexible Break Hours Allowed in the Shift", tracking=True)
    missed_effort = fields.Float(string="Missed Hours", tracking=True)
    public_holiday = fields.Boolean(string="Public Holiday", tracking=True)
    is_special_holiday = fields.Boolean(string="Special Holiday", tracking=True)
    is_weekend = fields.Boolean(string="Weekend", tracking=True)
    time_off = fields.Boolean(string="Is Leave", tracking=True)
    paid_leave = fields.Boolean(string="Paid Leave", tracking=True)
    used_flexible_break_hour = fields.Float(string="Used Flexible Break Hours", tracking=True)
    unpaid_leave = fields.Boolean(string="UnPaid Leave", tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('processed', 'Processed'), ('submit', 'Submitted'), ('confirmed', 'Confirmed')],
        string='State', tracking=True, copy=False,
        default='draft')
    emp_attendance_monthly = fields.Many2one('hr.payslip', string="Employee Attendance Monthly")


class InheritHrPayslip(models.Model):
    _inherit = 'hr.payslip'

    emp_attendance_monthly = fields.One2many("employee.attendance.payslip", 'emp_attendance_monthly',
                                             string="Employee Month Attendance Lines")

    attendance_check = fields.Boolean("Hidden Check", compute="_get_month_attendance")

    @api.onchange("employee_id", 'date_from', 'date_to')
    def _onchange_emp_dates(self):
        for rec in self:
            rec.emp_attendance_monthly = None
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('check_in', '>=', rec.date_from),
                ('check_out', '<=', rec.date_to)
            ])
            if attendances:
                for attendance in attendances:
                    rec.emp_attendance_monthly = [(0, 0, {
                        'check_in': attendance.check_in,
                        'check_out': attendance.check_out,
                        'actual_checkin': attendance.actual_checkin,
                        'actual_check_out': attendance.actual_checkout,
                        'extra_hours': attendance.extra_hours,
                        'break_hours': attendance.break_hours,
                        'resource_calendar_id': attendance.resource_calendar_id.id,
                        'late_hour': attendance.late_hour,
                        'early_hour': attendance.early_hour,
                        'flexible_break_hour': attendance.flexible_break_hour,
                        'used_flexible_break_hour': attendance.used_flexible_break_hour,
                        'missed_effort': attendance.missed_effort,
                        'public_holiday': attendance.public_holiday,
                        'is_special_holiday': attendance.is_special_holiday,
                        'is_weekend': attendance.is_weekend,
                        'time_off': attendance.time_off,
                        'paid_leave': attendance.paid_leave,
                        'unpaid_leave': attendance.unpaid_leave,
                        'state': attendance.state,
                        'mandatory_hours': attendance.mandatory_hours,
                        'actual_mandatory_hours': attendance.actual_mandatory_hours,
                    })]

    @api.depends('attendance_check')
    def _get_month_attendance(self):
        for rec in self:
            rec._onchange_emp_dates()
            rec.attendance_check = True
