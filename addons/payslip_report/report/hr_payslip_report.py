# -*- coding: utf-8 -*-
#
# Odootec <http://www.odootec.com>, Copyright (C) 2015 - Today.
#
# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from datetime import datetime
from dateutil.rrule import rrule, MONTHLY

from odoo import api, models
from odoo.tools.misc import formatLang, DEFAULT_SERVER_DATETIME_FORMAT
from pprint import pprint


class HrPayslipParser(models.AbstractModel):
    _name = 'report.payslip_report.hr_payslip_report'

    # from_date = ''
    # to_date = ''
    # employee_ids = False
    # salary_rule_ids = False

    def _get_data(self, data):

        salary_rule_ids = self.env['hr.salary.rule'].browse(data['form']['salary_rule_ids']).sorted(
            key=lambda v: v.sequence)
        column_headings = self._get_salary_rule_names(salary_rule_ids)

        pprint('salary rule names------------')
        pprint(column_headings)
        # data, payrule_total = self._get_table_data(data, salary_rule_ids)
        total_list = ['', 'Total', '', '', '']
        # for rule in salary_rule_ids:
        #     total_list.append(payrule_total.get(rule.id, 0.0))
        data, total_sum = self.data_for_new_report(data, salary_rule_ids)
        res = {'column_headings': self.get_new_columns(),
               # 'column_headings': column_headings,
               # 'data': data,
               'data': data,
               'total': total_list,
               'company_id': self.env.user.company_id.name,
               'total_sum': [total_sum]
               }
        return res

    def data_for_new_report(self, data=None, salary_rule_ids=None):
        from_date = data['form']['start_date']
        to_date = data['form']['end_date']
        employee_ids = data['form']['employee_ids']
        payslip_obj = self.env['hr.payslip']
        employee_obj = self.env['hr.employee']
        data = []
        payrule_total = {}
        total_gross = 0.0
        total_net = 0.0
        total_gross_charge = 0.0
        total_bus_unt_sal = 0.0
        for employee in employee_ids:
            employ = employee_obj.browse(employee)
            payslip_ids = payslip_obj.search([('employee_id', '=', employee),
                                              ('date_from', '<=', to_date),
                                              ('date_from', '>=', from_date),
                                              ('state', '=', 'done')])
            if not payslip_ids:
                continue
            index = 0
            for payslip in payslip_ids:
                index += 1
                refund = False
                if payslip.credit_note:
                    refund = True
                basic = sum(
                    payslip.line_ids.filtered_domain([('salary_rule_id.rule_type', '=', 'basic')]).mapped('total'))
                basic = round(basic, 2) if basic else 0
                deduction = -1 * sum(payslip.line_ids.filtered(lambda line: line.amount < 0).mapped('amount'))
                housing = sum(
                    payslip.line_ids.filtered_domain([('salary_rule_id.rule_type', '=', 'housing')]).mapped('total'))
                other = sum(
                    payslip.line_ids.filtered_domain([('salary_rule_id.rule_type', '=', 'other')]).mapped('total'))
                gross_actual = sum(
                    payslip.line_ids.filtered_domain([('salary_rule_id.code', '=', 'GROSS')]).mapped('amount'))
                gross_earned = sum(
                    payslip.line_ids.filtered_domain([('salary_rule_id.code', '=', 'GROSS')]).mapped(
                        'total')) - deduction
                net_salary = sum(
                    payslip.line_ids.filtered_domain([('salary_rule_id.code', '=', 'NET')]).mapped('total'))
                data_list = [index, employ.oe_emp_sequence, employ.company_id.name,
                             employ.name, employ.department_id.name, employ.job_id.name,
                             employ.joining_date,
                             payslip.worked_days_line_ids[0].number_of_days,
                             payslip.emp_month_leaves, payslip.month_unpaid_leaves, payslip.parental_leaves,
                             payslip.compassionate_leaves, payslip.maternity_leaves, payslip.maternity_leaves_half,
                             payslip.month_absence,
                             payslip.month_annual_leave,
                             '-', basic, housing, other, gross_actual, '-', gross_earned, deduction, int(net_salary),
                             '-',
                             '-', 'Remarks']
                data.append(data_list)
                total_gross += gross_actual
                total_net += net_salary
                total_gross_charge += gross_earned
        return data, {'total_gross': total_gross,
                      'total_net': total_net,
                      'total_gross_charge': total_gross_charge,
                      'business_unit': total_bus_unt_sal}

    def get_new_columns(self):
        heading_list = [
            "SI No.",
            "Emp Code",
            "Business Unit Work Location",
            "Name",
            "Department",
            "Designation",
            "Date of Joining",
            "Worked Days",
            "Sick Days",
            "unpaid Absent",

            "Parental Leaves",
            "Bereavement Leaves",
            "M/L Full",
            "M/L Half",
            "Absences",

            "Annual/Holiday Leave",
            "Cross Charge Day",
            "Basic Actual",
            "Living Out Allowance Actual",
            "Other Allowance Actual",
            "Gross Actual",
            "Total Earned",
            "Gross Earned",
            "Total Deduction",
            "Net Salary Present Month",
            "Cross Charge Amount",
            "Cross Charge Location",
            "Remarks"
        ]
        return heading_list

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

            pprint('------------ payslip_ids ---------------')
            pprint(payslip_ids)
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

    @api.model
    def _get_report_values(self, docids, data=None):

        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
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
        print('---------- i am here 1 ------------------')
        print('---------- i am here 1 ------------------')
        print('---------- i am here 1 ------------------')
        print('---------- i am here 1 ------------------')
        get_data = self._get_data(data)
        pprint(get_data)
        pprint({
            'doc_ids': docids,
            'get_data': get_data,
            'doc_model': model,
            'date_from': date_from,
            'date_to': date_to,
            'date_word': val,
            'data': data,
            'docs': docs,
            'formatLang': formatLang
        })

        print('------------- here -222222222')
        return {
            'doc_ids': docids,
            'get_data': get_data,
            'doc_model': model,
            'date_from': date_from,
            'date_to': date_to,
            'date_word': val,
            'data': data,
            'docs': docs,
            'formatLang': formatLang
        }
