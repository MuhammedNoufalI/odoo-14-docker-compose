# -*- coding:utf-8 -*-

from odoo import models, fields


class ChangeBranch(models.TransientModel):
    _name = 'change.branch.wiz'
    _description = 'Change Branch'


    def _default_employee_id(self):
        active_id = self._context.get('active_id')
        employee = self.env['hr.employee'].browse(active_id)
        return employee

    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee_id)
    branch_id = fields.Many2one('hc.branch', string='Branch')

    def change_branch(self):
        if self.employee_id and self.branch_id:
            self.employee_id.write({'branch_id': self.branch_id.id})
