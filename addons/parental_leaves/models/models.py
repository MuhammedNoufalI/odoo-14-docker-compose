# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class EmployeeChild(models.Model):
    _name = 'hr.employee.child'

    name = fields.Char("Name")
    dob = fields.Date("Date of Birth")
    child_parent_id = fields.Many2one('hr.employee')
    age_in_months = fields.Float("Age In Months", compute="_get_age_in_month")
    already_avail = fields.Boolean("Already Avail")

    @api.depends('name', 'dob')
    def _get_age_in_month(self):
        for rec in self:
            now = datetime.now()
            rec.age_in_months = relativedelta(now, rec.dob).months


class InheritHrEmployee(models.Model):
    _inherit = 'hr.employee'

    emp_child_ids = fields.One2many('hr.employee.child', 'child_parent_id', string="Employee Child's")


class InheritHrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    is_parental = fields.Boolean("Is Parental Leave")


class InheritHrLeave(models.Model):
    _inherit = 'hr.leave'

    def action_approve(self):
        self.ensure_one()
        res = super().action_approve()
        for rec in self:
            if rec.holiday_status_id.is_parental:
                if rec.number_of_days > 5:
                    raise ValidationError(_("Parental Leaves can not be greater then 5"))
                else:
                    if rec.employee_id.emp_child_ids:
                        remaining_parental_leave = rec.employee_id.emp_child_ids.filtered(
                            lambda rec: not rec.already_avail)
                        if not remaining_parental_leave:
                            raise ValidationError(_("You don't have any parental leave remaining"))
                        else:
                            allow = any([rec.age_in_months < 6 for rec in remaining_parental_leave])
                            if not allow:
                                raise ValidationError(_("Your are not allowed to get this leaves"))
                            else:
                                remaining_parental_leave[0].already_avail = True
                                return res
                    raise ValidationError(_("Your are not allowed to get  Parental leaves"))
            return res


class InheritPayslip(models.Model):
    _inherit = 'hr.payslip'

    parental_leaves = fields.Integer("Parental Leaves", compute="_onchange_employee_date")

    @api.depends('employee_id', 'date_from', 'date_to')
    def _onchange_employee_date(self):
        for rec in self:
            if rec.employee_id and rec.date_from and rec.date_to:
                rec.parental_leaves = sum(self.env['hr.leave'].search(
                    [('employee_id', '=', rec.employee_id.id), ('state', '=', 'validate'),
                     ('holiday_status_id.is_parental', '=', True), ('date_from', '>=', rec.date_from),
                     ('date_to', '<=', rec.date_to)]).mapped(
                    'number_of_days'))
            else:
                rec.parental_leaves = 0
