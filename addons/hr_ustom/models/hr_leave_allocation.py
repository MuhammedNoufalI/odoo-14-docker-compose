# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, AccessError, ValidationError


class HrAlloc(models.Model):
    _inherit = 'hr.leave.allocation'
    emp_attendance_id = fields.Many2one('employee.attendance', string='Employee Attendance')

    @api.constrains('emp_attendance_id')
    def check_total_hours(self):
        for rec in self:
            if rec.emp_attendance_id and rec.number_of_hours_display > rec.emp_attendance_id.bonus:
                raise ValidationError("You can't request hours more than in employee attendance form")

    date_from = fields.Date()
    date_to = fields.Date()

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for line in self:
            if line.date_to and line.date_from and line.date_to <= line.date_from:
                raise ValidationError('Date To Must Be Greater Than Date From!')
