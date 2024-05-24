from odoo import models, fields, api


class InheritHrWorkEntryType(models.Model):
    _inherit = 'hr.payslip.worked_days'

    total_days = fields.Integer("Total Days")
    total_leaves = fields.Integer("Total Leaves")

    @api.depends('is_paid', 'number_of_hours', 'payslip_id', 'contract_id.wage', 'payslip_id.sum_worked_hours')
    def _compute_amount(self):
        for worked_days in self:
            hours = worked_days.payslip_id.employee_id.resource_calendar_id.work_period
            wage = worked_days.payslip_id.contract_id.wage / 30 / hours if hours else 0
            if not worked_days.contract_id:
                worked_days.amount = 0
                continue
            if worked_days.payslip_id.wage_type == "hourly":
                worked_days.amount = worked_days.payslip_id.contract_id.hourly_wage * worked_days.number_of_hours if worked_days.is_paid else 0
            else:
                worked_days.amount = worked_days.total_days * hours * wage - worked_days.total_leaves * hours * wage
