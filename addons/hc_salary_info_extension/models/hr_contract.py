from odoo import fields, models
import time
from datetime import datetime, timedelta


class HrContractExtension(models.Model):
    _inherit = "hr.contract"

    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure',readonly=False,
                                related='structure_type_id.default_struct_id')

    basic = fields.Monetary(
        'Basic',
        compute='_compute_basic_amount'
    )
    wage = fields.Float(string="Gross", digits=(16, 2), required=True, compute='_compute_basic_amount', help="Basic Salary of the employee")

    def _compute_basic_amount(self):
        for rec in self:
            rec.wage = rec.total_salary
            if rec.salary_rule_ids:
                rec.basic = sum(rec.salary_rule_ids.filtered_domain([('salary_rule_id.code', '=', 'BASIC')]).mapped('amount'))
            else:
                rec.basic = False




