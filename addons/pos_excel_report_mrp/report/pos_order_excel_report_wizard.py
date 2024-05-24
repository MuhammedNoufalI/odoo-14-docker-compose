from odoo import models, fields, api
from odoo.exceptions import ValidationError



class PosOrderExcelMrpReportWizard(models.Model):
    _name = 'pos.order.mrp.excel.report.wizard'

    date_start = fields.Datetime('Start Date')
    date_end = fields.Datetime('End Date')

    def fetch_report_from_order(self):
        pos_orders = self.env['pos.order'].search([('date_order', '>=', self.date_start), ('date_order', '<=', self.date_end)])
        if self.date_start > self.date_end:
            raise ValidationError('Start Date must be less than End Date')
        report = pos_orders.get_report_values(self.date_start, self.date_end)
        return report
