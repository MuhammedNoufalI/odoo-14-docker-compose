# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InheritHrAttendance(models.Model):
    _inherit = 'hr.attendance'

    employee_badge_no = fields.Char("Employee ID", compute="_get_emp_info")
    employee_department = fields.Many2one("hr.department", "Department", compute="_get_emp_info")
    business_unit = fields.Char("Business Unit", compute="_get_emp_info")

    @api.depends('employee_id')
    def _get_emp_info(self):
        for rec in self:
            rec.employee_department = rec.employee_id.department_id.id if rec.employee_id.department_id else None
            rec.employee_badge_no = rec.employee_id.oe_emp_sequence
            rec.business_unit = rec.employee_id.business_unit
