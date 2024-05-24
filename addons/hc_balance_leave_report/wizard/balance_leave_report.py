from odoo import models, fields, api


class InheritDepartWizard(models.TransientModel):
    _name = 'leave.balance.wiz'
    _description = 'Balance leave Report'

    employee_ids = fields.Many2many('hr.employee', string='Employee IDs')
    date = fields.Date("Date")

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
            'active_model': 'leave.balance.wiz'
        })
        for record in self:
            return self.env.ref(
                'hc_balance_leave_report.report_balance_leave_xlsx').report_action(self,
                                                                                    data=data)

