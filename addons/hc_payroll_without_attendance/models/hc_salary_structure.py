# -*- coding: utf-8 -*-

from odoo import fields, models


class SalaryStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    is_attendance_based = fields.Boolean(string='Is Attendance Based Payroll')