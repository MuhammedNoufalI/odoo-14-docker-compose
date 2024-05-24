# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrPayslipBatches(models.Model):
    _inherit = 'hr.payslip.run'

    payroll_period_id = fields.Many2one('hc.payroll.period', string="Payroll Period")

     #inherited the fields from base to remove the default value
    date_start = fields.Date(string='Date From', required=True, readonly=True,
                             states={'draft': [('readonly', False)]})
    date_end = fields.Date(string='Date To', required=True, readonly=True,
                           states={'draft': [('readonly', False)]})

    @api.onchange('payroll_period_id')
    def onchange_date_range(self):
        if self.payroll_period_id:
            self.date_start = self.payroll_period_id.date_from
            self.date_end = self.payroll_period_id.date_to


class HrPayEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self):
        res = super(HrPayEmployees, self).compute_sheet()
        payroll_period_id = False
        if self.env.context.get('active_id'):
            payroll_period_id = self.env['hr.payslip.run'].browse(self.env.context.get('active_id')).payroll_period_id.id
        payslips = self.env['hr.payslip'].search([('payslip_run_id', '=', self.env.context.get('active_id'))])
        for payslip in payslips:
            payslip.write({
                'payroll_period_id': payroll_period_id
            })
            payslip.compute_sheet()
        return res