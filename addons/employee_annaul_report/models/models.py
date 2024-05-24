# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EmployeeAnnualLeave(models.Model):
    _name = 'employee.annual.leave'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', 'Employee')
    total_leaves = fields.Float("Total Annual Leaves", compute="_get_ann_leaves_details")
    al_taken = fields.Float("Annual Leaves Taken", compute="_get_ann_leaves_details")
    al_remaining = fields.Float("Remaining", compute="_get_ann_leaves_details")
    company_id = fields.Many2one('res.company', 'Business Unit')

    def _get_ann_leaves_details(self):
        model_emp_ids = self.env['employee.annual.leave'].search([]).mapped('employee_id.id')
        all_emp_ids = self.env['hr.employee'].search([]).mapped('id')
        remaining_emp = list(set(all_emp_ids) - set(model_emp_ids))
        if remaining_emp:
            for i in remaining_emp:
                self.env['employee.annual.leave'].create({
                    'employee_id': i,
                    'total_leaves': 0,
                    'al_taken': 0,
                    'al_remaining': 0,
                    'company_id': self.env['hr.employee'].browse(i).company_id.id
                })

        for rec in self:
            all_ann_le_taken = self.env['hr.leave'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', '=', 'validate'),
                ('holiday_status_id.is_annual_leave', '=', True)
            ])
            all_ann_le_all = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('state', '=', 'validate'),
                ('holiday_status_id.is_annual_leave', '=', True)
            ])
            total_leaves = sum(all_ann_le_all.mapped('number_of_days'))
            al_taken = sum(all_ann_le_taken.mapped('number_of_days'))
            rec.total_leaves = total_leaves
            rec.al_taken = al_taken
            rec.al_remaining = total_leaves - al_taken if total_leaves >= al_taken else 0
            rec.company_id = self.env['hr.employee'].browse(rec.employee_id.id).company_id


class InheritHrEmployee(models.Model):
    _inherit = 'hr.employee'

    total_ann_leaves = fields.Float("Allocates Annual Leaves", compute="get_ann_leaves")
    taken_ann_leaves = fields.Float("Taken Annual Leaves", compute="get_ann_leaves")

    def get_ann_leaves(self):
        for rec in self:
            all_ann_le_taken = self.env['hr.leave'].search([
                ('employee_id', '=', rec.id),
                ('state', '=', 'validate'),
                ('holiday_status_id.is_annual_leave', '=', True)
            ])
            all_ann_le_all = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', rec.id),
                ('state', '=', 'validate'),
                ('holiday_status_id.is_annual_leave', '=', True)
            ])
            total_leaves = sum(all_ann_le_all.mapped('number_of_days'))
            al_taken = sum(all_ann_le_taken.mapped('number_of_days'))
            rec.total_ann_leaves = total_leaves
            rec.taken_ann_leaves = al_taken
