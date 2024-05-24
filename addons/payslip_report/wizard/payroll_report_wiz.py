# -*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Savoir-faire Linux. All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import pytz
from datetime import datetime, date

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from pprint import pprint


def get_current_year(context):
    if not context:
        context = {}
    tz = context.get('tz', False)
    tz = tz and pytz.timezone(tz) or pytz.utc
    return datetime.now(tz).year


class PayrollAnalysis(models.TransientModel):
    """
    Wizard to generate payroll analysis report
    """
    _name = 'hr.payroll.report.wiz'
    _description = 'Payroll Report Wizard'

    period = fields.Selection(
        [
            ('current_year', 'Current Year'),
            ('previous_year', 'Previous Year'),
            ('every_year', 'Every Year'),
        ],
        string='Analysis Period',
        default='current_year'
    )
    start_date = fields.Datetime(
        'Start Date',
        default=lambda self: (
            date(get_current_year(self.env.context), 1, 1).strftime(
                DEFAULT_SERVER_DATE_FORMAT))
    )
    end_date = fields.Datetime(
        'End Date',
        default=lambda self: (
            date(get_current_year(self.env.context), 12, 31).strftime(
                DEFAULT_SERVER_DATE_FORMAT))
    )
    company_ids = fields.Many2many(
        'res.company',
        'payroll_report_company_rel',
        'payroll_report_id',
        'company_id', 'Companies',
    )
    employee_ids = fields.Many2many(
        'hr.employee',
        'payroll_report_employee_rel',
        'payroll_report_id',
        'employee_id',
        'Employees'
    )
    salary_rule_ids = fields.Many2many(
        'hr.salary.rule',
        'payroll_report_salary_rule_rel',
        'payroll_report_id',
        'salary_rule_id',
        'Salary Rules'
    )

    hr_payslip_report_template_id = fields.Many2one('hr.payslip.report.template', 'Template')

    @api.onchange('hr_payslip_report_template_id')
    def onchange_operation(self):
        if self.hr_payslip_report_template_id:
            self.salary_rule_ids = False
            self.name = self.hr_payslip_report_template_id.name
            self.salary_rule_ids = self.hr_payslip_report_template_id.salary_rule_ids.ids
            self.employee_ids = self.hr_payslip_report_template_id.employee_ids.ids

    @api.onchange('period')
    def onchange_period(self):
        if self.period:
            if self.period == 'every_year':
                self.start_date = False
                self.end_date = False

            year = get_current_year(self.env.context)

            if self.period == 'previous_year':
                year -= 1

            start_date = date(year, 1, 1).strftime(DEFAULT_SERVER_DATE_FORMAT)
            end_date = date(year, 12, 31).strftime(DEFAULT_SERVER_DATE_FORMAT)

            self.start_date = start_date
            self.end_date = end_date

    def payroll_analysis_open_window(self):
        """
        This method returns an action that displays analysis lines
        requested in the wizard
        """
        data = {'ids': self._context.get('active_ids', []), 'model': 'hr.payslip', 'form': self.read()[0]}
        if not data['form'].get('salary_rule_ids'):
            data['form']['salary_rule_ids'] = self.hr_payslip_report_template_id.salary_rule_ids.ids
        if not data['form'].get('employee_ids'):
            data['form']['employee_ids'] = self.hr_payslip_report_template_id.employee_ids.ids
        pprint(data)
        return self.env.ref('payslip_report.action_report_hr_payroll').report_action([], data=data)

    def export_xls(self):
        datas = {'ids': self._context.get('active_ids', []), 'model': 'hr.payslip', 'form': self.read()[0]}
        if not datas['form'].get('salary_rule_ids'):
            datas['form']['salary_rule_ids'] = self.hr_payslip_report_template_id.salary_rule_ids.ids
        if not datas['form'].get('employee_ids'):
            datas['form']['employee_ids'] = self.hr_payslip_report_template_id.employee_ids.ids

        print('----------------- i am here - 3---------------------')
        print('----------------- i am here - 3---------------------')
        print('----------------- i am here - 3---------------------')
        return self.env.ref('payslip_report.action_report_hr_payroll_xlsx').report_action(self, data=datas)
