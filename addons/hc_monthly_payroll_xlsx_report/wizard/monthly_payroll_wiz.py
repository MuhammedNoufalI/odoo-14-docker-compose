from odoo import models, fields, api


class MonthlyPayrollWizard(models.TransientModel):
    _name = 'monthly.payroll.wiz'
    _description = 'Monthly Payroll Report Wizard'

    payroll_period = fields.Many2one('hc.payroll.period', string="Payroll Period")
    company_id = fields.Many2one('res.company', 'Business Unit')
    date_start = fields.Date(string='Date From', required=True)
    date_end = fields.Date(string='Date To', required=True)

    @api.onchange('payroll_period')
    def onchange_date_range(self):
        if self.payroll_period:
            self.date_start = self.payroll_period.date_from
            self.date_end = self.payroll_period.date_to

    def print_excel_report(self):
        self.ensure_one()
        form_data = self.read()[0]
        data = {
            'ids': self.env.context.get('active_ids', []),
            'form': form_data
        }
        self = self.with_context({
            'data': data,
            'custom_method': True,
            'active_model': 'monthly.payroll.wiz'
        })
        for record in self:
            return self.env.ref(
                'hc_monthly_payroll_xlsx_report.report_monthly_payroll_wiz_xlsx').report_action(self, data=data)
