# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.rrule import rrule, MONTHLY
from odoo import api, fields, models
# from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from odoo.tools.misc import formatLang, DEFAULT_SERVER_DATETIME_FORMAT


class PaySlipReportXls(models.AbstractModel):
    _name = 'report.payslip_report.action_report_hr_payroll_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    # from_date = ''
    # to_date = ''
    # employee_ids = False
    # salary_rule_ids = False

    def _get_data(self, data):

        salary_rule_ids = self.env['hr.salary.rule'].browse(data['form']['salary_rule_ids']).sorted(
            key=lambda v: v.sequence)
        column_headings = self._get_salary_rule_names(salary_rule_ids)
        data, payrule_total = self._get_table_data(data, salary_rule_ids)
        total_list = ['', 'Total', '', '', '']
        for rule in salary_rule_ids:
            total_list.append(payrule_total.get(rule.id, 0.0))
        res = {'column_headings': column_headings,
               'data': data,
               'total': total_list
               }
        return res

    def _get_salary_rule_names(self, salary_rule_ids):
        rules = salary_rule_ids
        rule_names = ['Employee Number', 'Employee', 'Job Title', 'Bank name', 'Account Number']
        for rule in rules:
            rule_names.append(rule.code.replace(" ", "\n"))
        return rule_names

    def _get_table_data(self, data, salary_rule_ids):
        from_date = data['form']['start_date']
        to_date = data['form']['end_date']
        employee_ids = data['form']['employee_ids']
        payslip_obj = self.env['hr.payslip']
        employee_obj = self.env['hr.employee']
        data = []
        payrule_total = {}

        for employee in employee_ids:
            employ = employee_obj.browse(employee)

            payslip_ids = payslip_obj.search([('employee_id', '=', employee),
                                              ('date_from', '<=', to_date),
                                              ('date_from', '>=', from_date)])
            if not payslip_ids:
                continue
            for payslip in payslip_ids:
                refund = False
                if payslip.credit_note:
                    refund = True
                data_list = [employ.id]
                data_list.append(employ.name)
                data_list.append(employ.job_id.name)
                data_list.append(employ.bank_account_id.bank_id.name)
                data_list.append(employ.bank_account_id.acc_number)
                payslip_lines_ids = payslip.line_ids
                if not payslip_lines_ids:
                    continue
                for rule_id in salary_rule_ids:
                    rule_found = False
                    for payslip_line_rec in payslip_lines_ids:
                        if payslip_line_rec.salary_rule_id.id == rule_id.id:
                            if refund:
                                amount = -payslip_line_rec.total
                            else:
                                amount = payslip_line_rec.total
                            data_list.append(amount)
                            rule_found = True
                            if rule_id.id in payrule_total:
                                payrule_total[rule_id.id] += amount
                            else:
                                payrule_total[rule_id.id] = amount
                    if not rule_found:
                        data_list.append(0.00)
                data.append(data_list)

        return data, payrule_total

    def generate_xlsx_report(self, workbook, data, objs):
        print('i am in generate_xlsx_report')
        print('i am in generate_xlsx_report')
        print('i am in generate_xlsx_report')
        date_from = data['form']['start_date']
        date_to = data['form']['end_date']
        val = ''
        if date_from and date_to:
            date_from = datetime.strptime(date_from, DEFAULT_SERVER_DATETIME_FORMAT)
            date_to = datetime.strptime(date_to, DEFAULT_SERVER_DATETIME_FORMAT)
            dates = [dt for dt in rrule(MONTHLY, dtstart=date_from, until=date_to)]
            for record in dates:
                val += record.strftime("%B") + "/" + record.strftime("%Y") + "-"
        elif date_from and not date_to:
            my_date = datetime.strptime(date_from, DEFAULT_SERVER_DATETIME_FORMAT)
            val = (str(my_date.strftime("%B")) + '/' +
                   str(my_date.strftime("%Y")))
        elif not date_from and date_to:
            my_date = datetime.strptime(date_to, DEFAULT_SERVER_DATETIME_FORMAT)
            val = (str(my_date.strftime("%B")) + '/' +
                   str(my_date.strftime("%Y")))
        else:
            val = ''

        get_data = self._get_data(data)
        sheet = workbook.add_worksheet('Payslip Info')
        format1 = workbook.add_format(
            {'font_size': 10, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'center',
             'bold': True})
        format11 = workbook.add_format(
            {'font_size': 8, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True,
             'bold': True})
        format21 = workbook.add_format(
            {'font_size': 9, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True,
             'bold': True})

        sheet.merge_range('A1:D1', 'SASCA', format1)
        sheet.merge_range('A2:D2', 'Human Resource Management', format1)
        sheet.merge_range('A3:D3', 'Finncial Department', format1)
        sheet.merge_range('F4:I4', 'Salaries for Employees', format1)
        sheet.merge_range('E5:I5', 'From: ' + str(date_from) + ' To ' + str(date_to), format1)
        sheet.merge_range('F6:H6', 'Month / Year', format1)

        if val:
            sheet.merge_range('A7:L7', val, format11)
        for index, res in enumerate(get_data['column_headings']):
            sheet.write(8, index, res, format1)
        row = 8
        for result in get_data['data']:
            row += 1
            for index, res in enumerate(result):
                sheet.write(row, index, res, format21)

        for index, res in enumerate(get_data['total']):
            sheet.write(row + 1, index, res, format1)

# PaySlipReportXls('report.payslip_report.hr_payslip_report.xlsx', 'hr.payslip')
