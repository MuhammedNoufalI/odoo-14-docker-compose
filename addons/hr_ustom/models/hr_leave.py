# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, AccessError, ValidationError
class HrHolidays(models.Model):
    _inherit = 'hr.leave'
    emp_attendance_id = fields.Many2one('employee.attendance',string='Employee Attendance')
    @api.constrains('emp_attendance_id')
    def check_total_hours(self):
        for rec in self:
            if rec.emp_attendance_id and rec.number_of_days > rec.emp_attendance_id.bonus:
                raise ValidationError("You can't request hours more than in employee attendance form")

    # @api.constrains('request_date_from', 'request_date_to', 'holiday_status_id')
    # def check_ability(self):
    #     for rec in self:
    #         if rec.holiday_status_id and rec.emp_attendance_id and rec.request_date_from and rec.request_date_to:
    #             allocations = self.env['hr.leave.allocation'].search(
    #                 [ ('date_from', '<=', rec.request_date_from),
    #                  ('date_to', '>=', rec.request_date_to), ('holiday_status_id', '=', rec.holiday_status_id.id)])
    #             if not any(alloc.number_of_days - alloc.leaves_taken >= rec.number_of_days for alloc in allocations):
    #                 raise ValidationError("You aren't allowed to create leave in this dates")