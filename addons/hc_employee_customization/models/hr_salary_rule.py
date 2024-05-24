# -*- coding:utf-8 -*-

from odoo import api, fields, models


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    _description = 'Salary Rule'

    update_to_contract = fields.Boolean(string='Update To Employee Contract', copy=False)

    @api.model
    def create(self, vals):
        res = super(HrSalaryRule, self).create(vals)
        if vals.get('update_to_contract'):
            contracts = self.env['hr.contract'].search([])
            if contracts:
                for contract in contracts:
                    contract.salary_rule_ids = [(0,0,{'salary_rule_id':res.id, 'amount': 0})]
        return res
