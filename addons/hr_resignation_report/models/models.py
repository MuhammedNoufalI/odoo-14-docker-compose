# -*- coding: utf-8 -*-
import copy

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import calendar


class CrossChargeSummary(models.Model):
    _name = 'gross.charge.summary'

    business_unit = fields.Many2one('res.company', "Business Unit")
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    years_worked = fields.Float("Years Worked")
    resignation_id = fields.Many2one('hr.resignation', 'Resignation ID')
    cross_amount = fields.Float(string="cross Charge Amount")


class InheritHrResignation(models.Model):
    _inherit = 'hr.resignation'

    cross_charge_lines = fields.One2many('gross.charge.summary',
                                         'resignation_id',
                                         string="Gross Charge")
    amount_total = fields.Float("Amount Total", compute="_get_amount_total")

    other_bonus = fields.Float("Bonus/tips/other arrears")
    other_deduction = fields.Float('Asset recovery/training agreement')
    remarks = fields.Text("Remarks")

    def _get_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.cross_charge_lines.mapped('cross_amount'))

    def get_data(self):
        for rec in self:
            # get years in service logic starts here
            join_date = rec.employee_id.joining_date
            exp_lv_date = rec.expected_revealing_date
            start_date = datetime(join_date.year, join_date.month, join_date.day)
            end_date = datetime(exp_lv_date.year, exp_lv_date.month, exp_lv_date.day)
            delta = end_date - start_date + timedelta(days=1)
            years_in_service = delta.days / 365

            # get leaves in less than 5 and greater than 5 tenure logic started here
            lev_in_5_tenure, lev_more_5_tenure = self.get_leaves(rec, join_date, exp_lv_date)
            total_worked_years = (delta.days - (lev_in_5_tenure + lev_more_5_tenure)) / 365

            # get gratuity days less than 5 years tenure and greater than 5 years of tenure
            total_worked_days_lt, total_worked_days_gt = (self._get_worked_days
                                                          (years_in_service, lev_in_5_tenure, lev_more_5_tenure, delta))
            gratuity_id = self.env['hr.gratuity'].search(
                [('employee_id', '=', rec.employee_id.id), ('state', '=', 'approve')], limit=1)
            if gratuity_id:
                grt_days_in_5_tenure = self.calculat_gratuity_days(total_worked_years, years_in_service,join_date,exp_lv_date,lev_in_5_tenure)
                grt_more_5_tenure = self.grt_more_5_tenure_days(years_in_service, total_worked_days_gt)
            else:
                grt_days_in_5_tenure = 0.00
                grt_more_5_tenure = 0.00



            # employee gratuity
            gratuity_id = self.env['hr.gratuity'].search(
                [('employee_id', '=', rec.employee_id.id), ('state', '=', 'approve')], limit=1)

            # per_day_wage = self.get_per_day_wage(rec, gratuity_id)

            # Days worked in the final month
            # final_month_days = self.get_final_month_days(rec)
            final_month_days = self.last_worked_days_monthly

            # get eligible month salary
            # eligible_month_salary = self.get_eligible_month_salary(rec.employee_id, rec.resign_date, final_month_days)


            # get loan data
            loan_amount = self.get_loan_amount(rec)
            gratuity_per_day = self.employee_id.contract_id.basic /30

            # Get gratuity amount in five years
            gratuity_amount_5_years = gratuity_per_day * grt_days_in_5_tenure
            gratuity_amount_more_5_years = grt_more_5_tenure * gratuity_per_day
            # non_served_notice_period = self.non_served_notice(join_date,exp_lv_date)
            # get gratuity more than 5 years


            total_payable_gratuity = gratuity_amount_5_years + gratuity_amount_more_5_years
            other_allowance,living_out_allowance = self._get_other_allowance(rec)
            days_in_month = 30
            per_day_wage = (self.employee_id.contract_id.basic+ other_allowance+living_out_allowance)/ days_in_month
            eligible_month_salary = final_month_days * per_day_wage

            # leave balance
            total_worked_days = total_worked_days_lt + total_worked_days_gt
            allocated_leave, utilized_leaves = self.allocated_leave_days(join_date, exp_lv_date,total_worked_days)
            ticket_entitlement, ticket_utilized, balance = self.ticket_entitelment(years_in_service, join_date, exp_lv_date)
            # utilized_leaves = allocated_leave - leave_balance
            leave_balance = allocated_leave - utilized_leaves
            total_leave_amount = (self.employee_id.contract_id.basic/30)*leave_balance

            # total earnings
            total_earnings = round(
                total_payable_gratuity + eligible_month_salary + rec.other_bonus + total_leave_amount, 2)

            # total deduction
            total_deductions = round(loan_amount + rec.other_deduction, 2)

            # final amount
            final_amount = total_earnings - total_deductions

            data = {
                'years_in_service': round(years_in_service, 2),
                'total_worked_years': round(total_worked_years,2),
                'total_worked_days_lt': round(total_worked_days_lt,2),
                'total_worked_days_gt':round(total_worked_days_gt,2),
                'lev_in_5_tenure': lev_in_5_tenure,
                'lev_more_5_tenure': lev_more_5_tenure,
                'gratuity_id': gratuity_id,
                'gratuity_per_day': round(gratuity_per_day, 2),
                'per_day_wage': round(per_day_wage, 2),
                'gratuity_amount_5_years': round(gratuity_amount_5_years, 2),
                'gratuity_amount_more_5_years': round(gratuity_amount_more_5_years, 2),
                'final_month_days': round(final_month_days, 2) if final_month_days else 0,
                'eligible_month_salary': round(eligible_month_salary, 2),
                'allocated_leave': int(allocated_leave),
                'utilized_leaves': int(utilized_leaves),
                'leave_balance': round(leave_balance,0),
                'total_leave_amount': round(total_leave_amount,2),
                'previous_month_salary': round(eligible_month_salary, 2),
                'loan_amount': loan_amount,
                'total_payable_gratuity': round(total_payable_gratuity, 2),
                'total_earnings': total_earnings,
                'total_deduction': total_deductions,
                'final_amount': round(final_amount,2),
                'other_allowance': other_allowance,
                'living_out_allowance': living_out_allowance,
                'grt_days_in_5_tenure': round(grt_days_in_5_tenure,2),
                'grt_more_5_tenure': round(grt_more_5_tenure,2),
                'ticket_entitlement': ticket_entitlement,
                'ticket_utilized': ticket_utilized,
                'ticket_balance': balance,
            }
            return data

    @staticmethod
    def get_gratuity_amount(grt_days_in_5_tenure=None, grt_days=None, years=None,gratuity_per_day=None, rec=None):
        if rec.reason != "TERMINATION":
            if years < 1:
                result = 0
            elif 1 <= years < 3:
                result = (gratuity_per_day * grt_days) / 3
            elif 3 <= years < 5:
                result = ((gratuity_per_day * grt_days) * 2) / 3
            elif years >= 5:
                result = gratuity_per_day * grt_days
            else:
                result = 0
        else:
            if years < 365:
                result = 0
            else:
                result = (grt_days * gratuity_per_day) + (grt_days_in_5_tenure * gratuity_per_day)
        return result
    def _get_other_allowance(self,rec):
        other_allowance = 0.00
        living_out_allowance = 0.00
        if rec.employee_id.contract_id:
            contract_id = rec.employee_id.contract_id
            other_allowance = sum(contract_id.salary_rule_ids.filtered_domain([('salary_rule_id.code', '=', 'TRA')]).mapped('amount'))
            living_out_allowance = sum(contract_id.salary_rule_ids.filtered_domain([('salary_rule_id.code', '=', 'ACC')]).mapped('amount'))
        return other_allowance,living_out_allowance



    def gratuity_configuration_line(self, years_in_service):
        gratuity_config = self.env['hr.gratuity.accounting.configuration'].search(
            [('config_contract_type', '=', 'unlimited'),
             ('gratuity_start_date', '<=', fields.Datetime.now().date())
             ])
        if gratuity_config and gratuity_config.gratuity_end_date:
            gratuity_config = gratuity_config.filtered(
                lambda rec: rec.gratuity_end_date >= fields.Datetime.now().date())
        line = gratuity_config.gratuity_configuration_table.filtered(
            lambda rec: rec.from_year <= years_in_service <= rec.to_year)
        if line:
            gratuity_days = line[0].days
            return gratuity_days
        return 0

    def get_loan_amount(self, rec=None):
        for rec in self:
            loan_taken = self.env['hr.loan'].search([('employee_id', '=', rec.employee_id.id),
                                                     ('company_id', 'in', self.env.companies.ids)])
            if loan_taken:
                return sum(loan_taken.mapped('balance_amount'))
            return 0

    @staticmethod
    def get_eligible_month_salary(employee=None, resign_date=None, final_month_day=None):
        if employee.contract_id:
            contract_id = employee.contract_id[0]
            total_days = calendar.monthrange(resign_date.year, resign_date.month)[1]
            per_day_wage = contract_id.wage / total_days
            return round(contract_id.wage - (total_days - final_month_day - (total_days // 7)) * per_day_wage, 2)
        return 0

    def get_per_day_wage(self, rec=None, gratuity_id=None, per_day_wage=None):
        daily_wage = 0
        if not gratuity_id:
            return rec.employee_id.contract_id.wage / 30
        if rec.employee_id.contract_id.wage_type == 'hourly':
            if rec.employee_id.resource_calendar_id and rec.employee_id.resource_calendar_id.hours_per_day:
                daily_wage = rec.employee_id.contract_id.wage * rec.employee_id.resource_calendar_id.hours_per_day
            else:
                daily_wage = rec.employee_id.contract_id.basic * 8
        elif rec.employee_id.contract_id.wage_type == 'monthly':
            daily_wage = (rec.employee_id.contract_id.wage / gratuity_id.employee_gratuity_duration.
                          employee_daily_wage_days)
        return daily_wage


    def allocated_leave_days(self,join_date, exp_lv_date,total_worked_days):
        # allocation = sum(self.env['hr.leave.type'].search([('pay_type', '=', 'paid')]).mapped('allocation_days'))
        allocation = 0.00
        # if total_worked_days < 180:
        #     allocation = 0.00
        # elif total_worked_days < 365:
        #     allocation =total_worked_days * 0.0658
        # else:
        #     allocation = (total_worked_days/365)*30
        Allocation = self.env['hr.leave.allocation']
        allocated_leaves = Allocation.search(
            [('employee_id', '=',self.employee_id.id),
             ('holiday_status_id.is_annual_leave', '=', True), ('state', '=', 'validate')])
        allocation = sum(allocated_leaves.mapped('number_of_days_display'))
        utilized_leaves = sum(self.env['hr.leave'].search([
            ('state', '=', 'validate'), ('holiday_status_id.is_annual_leave', '=', True),
            ('employee_id', '=', self.employee_id.id)]).mapped('number_of_days'))

        return allocation, utilized_leaves
    # def non_served(self):
    #     all_attendances = self.env['hr.attendance'].search(
    #         [('checkin_date', '>=', self.from_date), ('checkout_date', '<=', self.to_date),
    #          ('employee_id', '=', self.employee.id)])

    def calculat_gratuity_days(self, total_worked_years, years_in_service,join_date,exp_lv_date,lev_in_5_tenure):
        if years_in_service < 1:
            grat_lt_days = 0.00
        elif self.employee_id.contract_type == "LIMITED":
            if years_in_service > 5:
                grat_lt_days = (105 * (1825 - lev_in_5_tenure)) / 1825
            else:
                grat_lt_days = (105 * ((exp_lv_date - join_date + timedelta(days=1)) - lev_in_5_tenure)) / 1825
        elif 1 <= total_worked_years < 3:
            grat_lt_days = total_worked_years * 7
        elif 3 <= total_worked_years < 5:
            grat_lt_days = total_worked_years * 14
        else:
            grat_lt_days = 5 * 21

        return grat_lt_days
    def grt_more_5_tenure_days(self, years_in_service,total_worked_days_gt):
        if years_in_service <1:
            grat_gt_days = 0.00
        elif years_in_service > 5:
            grat_gt_days = (total_worked_days_gt * (30 * (years_in_service - 5))) / (365 * (years_in_service - 5))
        else:
            grat_gt_days = 0.00
        return grat_gt_days



    def ticket_entitelment(self, years_in_service, join_date, exp_lv_date):

        ticket = self.env['ticket.request'].search(
            [('employee_id', '=', self.employee_id.id), ('state', '=', 'hr_approval'),
             ('create_date', '<=', exp_lv_date),
             ('create_date', '>=', join_date)])
        ticket_entitlement = 0.00
        ticket_utilized = 0.00
        ticket_accrued = 0.00
        balance = 0.00
        if ticket:
            ticket_entitlement = ticket[0].ticket_entitlement
            ticket_utilized = len(ticket)
            ticket_accrued = float(years_in_service) / int(ticket_entitlement)
            balance = ticket_accrued - ticket_utilized
        return ticket_entitlement, ticket_utilized, balance

    def _get_worked_days(self,years_in_service,lev_in_5_tenure,lev_more_5_tenure,delta):
        if years_in_service > 5:
            total_worked_days_lt = 1825 - lev_in_5_tenure
            total_worked_days_gt = (years_in_service - 5) * 365 - lev_more_5_tenure
        else:
            total_worked_days_lt = (delta.days + 1)-lev_in_5_tenure
            total_worked_days_gt = 0.00

        return total_worked_days_lt, total_worked_days_gt

    def get_leaves(self, rec=None, join_date=None, exp_lv_date=None):
        tenure = self.calculate_tenure(join_date, exp_lv_date)
        tenure = round(tenure.days / 365, 2) if tenure else 0
        if tenure < 5:
            less_t_5 = sum(self.env['hr.leave'].search([
                ('state', '=', 'validate'), ('holiday_status_id.is_unpaid_leave', '=', True),
                ('employee_id', '=', rec.employee_id.id), ('request_date_from', '>=', join_date),
                ('request_date_to', '<=', exp_lv_date)]).mapped('number_of_days'))
            return less_t_5, 0
        elif tenure > 5:
            five_yrs_comp_date = self.five_years_com_date(join_date, 5)
            five_leaves = sum(self.env['hr.leave'].search(
                [('employee_id', '=', rec.employee_id.id),
                 ('state', '=', 'validate'), ('holiday_status_id.is_unpaid_leave', '=', True),
                 ('request_date_from', '>=', join_date),
                 ('request_date_to', '<=', five_yrs_comp_date)
                 ]).mapped('number_of_days'))

            five_more_leaves = sum(self.env['hr.leave'].search(
                [('employee_id', '=', rec.employee_id.id),
                 ('state', '=', 'validate'), ('holiday_status_id.is_unpaid_leave', '=', True),
                 ('request_date_from', '>=', five_yrs_comp_date + timedelta(days=1)),
                 ('request_date_to', '<=', exp_lv_date)
                 ]).mapped('number_of_days'))
            return five_leaves, five_more_leaves

    def get_final_month_days(self, rec=None):
        payroll_period = self.env['hc.payroll.period'].search([('date_to', '>=', rec.expected_revealing_date),
                                                               ('date_from', '<=', rec.expected_revealing_date)], limit=1)
        final_month_date_list = self.get_dates_list(payroll_period.date_from, rec.expected_revealing_date)
        leave_in_f_month_list = self.get_leaves_list(rec.employee_id, payroll_period.date_from, rec.expected_revealing_date)
        worked_days = len([d for d in final_month_date_list if d not in leave_in_f_month_list])

        # if worked_days:
        #     week_norm_leaves = len(final_month_date_list) // 7
        #     worked_days -= week_norm_leaves
        return worked_days

    def get_leaves_list(self, emp=None, date_from=None, date_to=None):
        if date_to and date_from:
            leaves = self.env['hr.leave'].search([
                ('state', '=', 'validate'),
                ('request_date_from', '>=', date_from - timedelta(days=31)),
                ('request_date_to', '<=', date_to + timedelta(days=31)),
                ('employee_id', '=', emp.id)
            ])

            leaves_dates = []
            for leave in leaves:
                l_date_from = copy.deepcopy(leave.request_date_from)
                l_date_to = copy.deepcopy(leave.request_date_to)
                while l_date_from <= l_date_to:
                    leaves_dates.append(l_date_from)
                    l_date_from += timedelta(days=1)

            return leaves_dates

    def get_dates_list(self, date_from=None, date_to=None):
        payslip_dates = []
        p_date_from = copy.deepcopy(date_from)
        p_date_to = copy.deepcopy(date_to)
        if p_date_from and p_date_to:
            while p_date_from <= p_date_to:
                payslip_dates.append(p_date_from)
                p_date_from += timedelta(days=1)
        return payslip_dates

    @staticmethod
    def calculate_tenure(join_date, lve_date):
        return lve_date - join_date

    @staticmethod
    def five_years_com_date(hire_date, years):
        tenure_completion_date = hire_date + timedelta(days=years * 365)
        return tenure_completion_date

    def get_total_earnings(self, rec=None):
        return sum(self.env['hr.payslip'].search([('employee_id', '=', rec.employee_id.id)]).mapped('net_wage'))
