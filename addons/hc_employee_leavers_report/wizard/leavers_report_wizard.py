import base64
import io
import json
from odoo import fields, models, api,_
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
from datetime import date, datetime, timedelta


class LeaversReport(models.TransientModel):
    _name = "hr.leavers.report"
    _description = 'Employee Leavers Report'

    def today_date(self):
        today = date.today()
        return today

    def yesterday_date(self):
        yesterday = date.today() - timedelta(days=1)
        return yesterday

    from_date = fields.Date(string='From Date', default=yesterday_date)
    to_date = fields.Date(string='To Date', required=True, default=today_date)
    employees = fields.Many2many('hr.employee', string='Employees', context={'active_test': False})

    def date_validation(self):
        if self.from_date:
            if self.from_date > self.to_date:
                raise ValidationError('From Date must be less than To Date')

    def action_print_leavers_report_pdf(self):
        if not self.employees:
            self.employees = self.env['hr.employee'].search(['&','&','&',('active','=', False),('departure_reason', 'in',['retired', 'fired', 'resigned']),('departure_date', '<=', self.to_date),('departure_date', '>=', self.from_date)])
        if self.employees:
            return self.env.ref('hc_employee_leavers_report.print_leavers_report_pdf').report_action(self)
        else:
            raise ValidationError(_("No details to print"))


















