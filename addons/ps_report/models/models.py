# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from pytz import timezone
from datetime import date, timedelta


class salaryrule(models.Model):
    _inherit = 'hr.salary.rule'
    rule_type = fields.Selection(string="Rule Type",
                                 selection=[('basic', 'Basic'), ('housing', 'Housing'), ('other', 'Other'), ],
                                 required=False, )


class payslip(models.Model):
    _inherit = 'hr.payslip'

    worked_days = fields.Char(string='WORKED DAYS')
    leave_days = fields.Char(string='LEAVE DAYS')
    unpaid_days = fields.Char(string='UNPAID DAYS')
    sick_days = fields.Char(string='SICK DAYS')
    total_days = fields.Char(string='Total Days')
    leave_data_view = fields.Boolean(compute='_get_leave_data_view')

    def _get_leave_data_view(self):
        for rec in self:
            if rec.struct_id.is_attendance_based:
                rec.leave_data_view = True
            else:
                rec.leave_data_view = False

    def get_lines(self):
        list1 = self.line_ids.filtered_domain([('amount', '>=', 0)])
        list11 = [x for x in list1]
        list2 = self.line_ids.filtered_domain([('amount', '<', 0)])
        list22 = [x for x in list2]
        deck = []
        earn = sum(list1.mapped('total'))
        deduc = sum(list2.mapped('amount'))
        for i in range(max((len(list11), len(list22)))):
            while True:
                try:
                    card = (list11[i], list22[i])
                except IndexError:
                    if len(list11) > len(list22):
                        list22.append(self.env['hr.payslip.line'])
                        card = (list11[i], list22[i])
                    elif len(list11) < len(list22):
                        list11.append(self.env['hr.payslip.line'])
                        card = (list11[i], list22[i])
                    continue
                deck.append(card)
                break
        return [deck, earn, deduc, self.emp_month_leaves]

    def get_payslip_deduction(self):
        list2 = []
        deduction_list = self.line_ids.filtered_domain(
            [('amount', '>', 0), ('category_id.code', 'in', ['DED'])])
        for deduction in deduction_list:
            lines = {
                'amount': deduction.amount,
                'name': deduction.display_name,
            }
            list2.append(lines)
        return list2

    def get_payslip_earnings(self):
        earnings_list = self.line_ids.filtered_domain(
            [('amount', '>', 0), ('category_id.code', 'in', ['BASIC', 'ALW'])])
        list1 = []
        for earnings in earnings_list:
            lines = {
                'amount': earnings.amount,
                'name': earnings.display_name,
            }
            list1.append(lines)

        return list1

    def get_data(self):
        for rec in self:
            basic_sum = 0
            housing_sum = 0
            other = 0
            total = 0
            if rec.contract_id:
                basic_sum = rec.contract_id.basic
                other = sum(
                    rec.contract_id.salary_rule_ids.filtered_domain([('salary_rule_id.code', '=', 'TRA')]).mapped(
                        'amount'))
                housing_sum = sum(
                    rec.contract_id.salary_rule_ids.filtered_domain([('salary_rule_id.code', '=', 'ACC')]).mapped(
                        'amount'))
            total = basic_sum + housing_sum + other
            return [basic_sum, housing_sum, other, total]

    def get_leaves(self):
        for rec in self:
            domain = [('employee_id', '=', rec.employee_id.id), ('state', '=', 'validate'),
                      ('date_from', '>=', rec.date_from), ('date_to', '<=', rec.date_to)]
            m_s_leaves = sum(
                self.env['hr.leave'].search(domain + [('holiday_status_id.is_sick_leave', '=', True)]).mapped(
                    'number_of_days'))
            unpaid_leaves = sum(
                self.env['hr.leave'].search(domain + [('holiday_status_id.unpaid', '=', True)]).mapped(
                    'number_of_days'))
            annual_leave = sum(
                self.env['hr.leave'].search(domain + [('holiday_status_id.is_annual_leave', '=', True)]).mapped(
                    'number_of_days'))
            total_days = rec.total_days
            worked_days = total_days - (m_s_leaves + unpaid_leaves - annual_leave)
            return [m_s_leaves, unpaid_leaves, annual_leave, worked_days, total_days]

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_leave_details(self):
        for rec in self:
            attendance = self.env['hr.attendance'].search([('date', '>=', rec.date_from),
                                                           ('date', '<=', rec.date_to),
                                                           ('employee_id', '=', rec.employee_id.id)])
            domain = [('employee_id', '=', rec.employee_id.id), ('state', '=', 'validate'),
                      ('request_date_from', '>=', rec.date_from), ('request_date_to', '<=', rec.date_to)]

            sick_leave = sum(
                self.env['hr.leave'].search(domain + [('holiday_status_id.is_sick_leave', '=', True)]).mapped(
                    'number_of_days'))
            unpaid_leve = sum(
                self.env['hr.leave'].search(domain + [('holiday_status_id.unpaid', '=', True)]).mapped(
                    'number_of_days'))
            annual_leave = sum(
                self.env['hr.leave'].search(domain + [('holiday_status_id.is_annual_leave', '=', True)]).mapped(
                    'number_of_days'))
            leave_days = attendance.filtered(lambda r: r.time_off == True)
            # unpaid_leve = leave_days.filtered(lambda r: r.unpaid_leave == True)
            # sick_leave = len(leave_days.filtered(lambda r: r.leave_id.is_sick_leave == True))
            # work_days = len(attendance) - len(leave_days)

            rec.leave_days = str(annual_leave)
            rec.unpaid_days = str(unpaid_leve)
            rec.sick_days = str(sick_leave)
            rec.total_days = len(attendance)
            work_days = len(attendance) - float(rec.leave_days) - float(rec.unpaid_days) - int(rec.sick_days)
            rec.worked_days = str(work_days)
            # rec.total_days = int(rec.worked_days) + float(rec.leave_days) + float(rec.unpaid_days) + int(rec.sick_days)

    def employee_contract_salary(self):
        for rec in self:
            basic = 0
            housing = 0
            other = 0
            contract_id = rec.employee_id.contract_ids
            net_total = contract_id.total_salary
            for rule in contract_id.salary_rule_ids:
                if rule.salary_rule_id.code == 'BASIC':
                    basic = rule.amount
                elif rule.salary_rule_id.code == 'ACC':
                    housing = rule.amount
                elif rule.salary_rule_id.code == 'TRA':
                    other = rule.amount
            lines = {
                'basic': basic,
                'housing': housing,
                'other': other,
                'net_total': net_total
            }
            vals = lines
            return vals

    def get_employee_worked_days_data(self):
        for rec in self:
            attendance = self.env['hr.attendance'].search([('checkin_date', '>=', rec.date_from),
                                                           ('checkout_date', '<=', rec.date_to),
                                                           ('employee_id', '=', rec.employee_id.id)])
            domain = [('employee_id', '=', rec.employee_id.id), ('state', '=', 'validate'),
                      ('request_date_from', '>=', rec.date_from), ('request_date_to', '<=', rec.date_to)]

            sick_leave = sum(
                self.env['hr.leave'].search(domain + [('holiday_status_id.is_sick_leave', '=', True)]).mapped(
                    'number_of_days'))
            unpaid_leve = sum(
                self.env['hr.leave'].search(domain + [('holiday_status_id.unpaid', '=', True)]).mapped(
                    'number_of_days'))
            annual_leave = sum(
                self.env['hr.leave'].search(domain + [('holiday_status_id.is_annual_leave', '=', True)]).mapped(
                    'number_of_days'))
            annual_leave = str(annual_leave)
            unpaid_days = str(unpaid_leve)
            sick_days = str(sick_leave)
            total_days = len(attendance)
            worked_days = len(attendance) - float(annual_leave) - float(unpaid_days) - int(sick_days)

            lines = {
                'worked_days': worked_days,
                'annual_leave': annual_leave,
                'unpaid_days': unpaid_days,
                'sick_days': sick_days,
                'total_days': total_days
            }
            vals = lines
            return vals
