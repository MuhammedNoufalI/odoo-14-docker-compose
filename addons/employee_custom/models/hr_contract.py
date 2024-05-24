# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


# class Contract(models.Model):
#     _inherit = 'hr.contract'
#     total_salary = fields.Float('Total Salary', compute='compute_total_salary', store=True)
#
#     @api.depends('allowances_ids', 'allowances_ids.amount', 'wage')
#     def compute_total_salary(self):
#         for rec in self:
#             rec.total_salary = rec.wage + rec.get_all_allowances() + rec.get_all_deductions()
