# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
import calendar


class AllocationDates(models.Model):
    _name = "allocation.date"

    date = fields.Date()
    employee_id = fields.Many2one('hr.employee', string='Employee')
    leave_type_id = fields.Many2one('hr.leave.type', string="Leave Type", required=False, )


class Employee(models.Model):
    _inherit = 'hr.employee'
    allocation_dates = fields.One2many('allocation.date', 'employee_id')
    leave_type_ids = fields.Many2many('hr.leave.type', string="Leave Types", required=False, )
    has_assign_ben = fields.Boolean("Has Assign Leaves")

    def create_allocation(self):
        for rec in self.search([('leave_type_ids', '!=', False)]):
            for leave in rec.leave_type_ids:
                if leave.schedule_allocation:
                    date = fields.date.today()
                    if leave.period_type == 'monthly':
                        if leave.day == date.day:
                            exist = rec.allocation_dates.filtered(lambda x: x.leave_type_id == leave and x.date == date)
                            if not exist:
                                allocation_values = {
                                    'name': leave.name,
                                    'holiday_status_id': leave.id,
                                    'employee_id': rec.id,
                                    'number_of_days': leave.period,
                                    'date_from': date,
                                    'date_to': date + relativedelta(days=date.day + leave.day - 1),
                                }
                                allocations = self.env['hr.leave.allocation'].create(allocation_values)
                                self.env['allocation.date'].create({'leave_type_id': leave.id,
                                                                    'employee_id': rec.id,
                                                                    'date': fields.date.today()})
                    elif leave.period_type == 'annual':
                        if leave.day == date.day and int(leave.month) == int(date.month):
                            exist = rec.allocation_dates.filtered(lambda x: x.leave_type_id == leave and x.date == date)
                            if not exist:
                                allocation_values = {
                                    'name': leave.name,
                                    'holiday_status_id': leave.id,
                                    'employee_id': rec.id,
                                    'number_of_days': leave.period,
                                    'date_from': date,
                                    'date_to': date + relativedelta(days=date.day + leave.day - 1, years=date.year + 1),
                                }
                                allocations = self.env['hr.leave.allocation'].create(allocation_values)
                                self.env['allocation.date'].create({'leave_type_id': leave.id,
                                                                    'employee_id': rec.id,
                                                                    'date': fields.date.today()})

    # def create_monthly_allocation(self):
    #     running_contracts = self.env['hr.contract'].search([('state', '=', 'open')])
    #     type = self.env['hr.leave.type'].search([('schedule_create', '=', True)], limit=1)
    #     next_call = self.sudo().env.ref('leave_custom.ir_cron_create_monthly_allocation').nextcall.date()
    #     last_call = self.sudo().env.ref('leave_custom.ir_cron_create_monthly_allocation').env.context.get(
    #         'lastcall').date()
    #     if not type:
    #         type = self.env['hr.leave.type'].search([], limit=1)
    #     for rec in running_contracts.filtered(lambda rec: rec.employee_id):
    #         if rec.date_start:
    #             date = next_call if next_call else fields.date.today()
    #             first, last = calendar.monthrange(date.year, date.month)
    #             ist = datetime(date.year, date.month, 1).date()
    #             lst = datetime(date.year, date.month, last).date()
    #             exist = self.env['hr.leave.allocation'].search(
    #                 [('date_from', '>=', ist), ('date_from', '<=', lst), ('employee_id', '=', rec.employee_id.id),
    #                  ('schedule_create', '=', True)])
    #             if not exist:
    #                 emp_unpaid_leaves = self.env['hr.leave'].search(
    #                     [('date_from', '>=', ist), ('date_from', '<=', lst),
    #                      ('employee_id', '=', rec.employee_id.id),
    #                      ('state', '=', 'validate'),
    #                      ('holiday_status_id.is_unpaid_leave', '=', True)])
    #                 allocation_values = {
    #                     'name': type.name,
    #                     'schedule_create': True,
    #                     'holiday_status_id': type.id,
    #                     'employee_id': rec.employee_id.id,
    #                     'date_from': date,
    #                 }
    #                 yes = self.has_completed_year(rec.employee_id)
    #                 if yes:
    #                     per_day_allocation = 0.082191781
    #                     if sum(emp_unpaid_leaves.mapped('number_of_days')) >= lst.day:
    #                         days_to_allocate = 0
    #                     else:
    #                         days_to_allocate = 2.5 - (
    #                                 per_day_allocation * sum(emp_unpaid_leaves.mapped('number_of_days')))
    #                     if days_to_allocate < 0:
    #                         days_to_allocate = 0
    #                     if not rec.employee_id.has_assign_ben:
    #                         days_to_allocate += 6
    #                         rec.employee_id.has_assign_ben = True
    #                     allocation_values['number_of_days'] = days_to_allocate
    #                     if days_to_allocate < 1:
    #                         allocation_values['date_to'] = date + timedelta(days=1)
    #                     else:
    #                         allocation_values['date_to'] = date + relativedelta(days=days_to_allocate)
    #                 elif 182 <= (datetime.today() - fields.Datetime.from_string(
    #                     rec.employee_id.joining_date)).days <= 365:
    #                     per_day_allocation = 0.082191781
    #                     if sum(emp_unpaid_leaves.mapped('number_of_days')) >= lst.day:
    #                         days_to_allocate = 0
    #                     else:
    #                         days_to_allocate = 2 - (
    #                                 per_day_allocation * sum(emp_unpaid_leaves.mapped('number_of_days')))
    #                     if days_to_allocate < 0:
    #                         days_to_allocate = 0
    #                     allocation_values['number_of_days'] = days_to_allocate
    #                     if days_to_allocate < 1:
    #                         allocation_values['date_to'] = date + timedelta(days=1)
    #                     else:
    #                         allocation_values['date_to'] = date + relativedelta(days=days_to_allocate)
    #                 negative_allocation = self.env['hr.leave.allocation'].search(
    #                     [('employee_id', '=', rec.employee_id.id),
    #                      ('negative_balance', '>', 0)], limit=1)
    #                 if negative_allocation:
    #                     negative_allocation.negative_balance -= days_to_allocate
    #                 else:
    #                     allocations = self.env['hr.leave.allocation'].create(allocation_values)
    #                     allocations.sudo().action_approve()
    #                     allocations.sudo().action_validate()



    def create_monthly_allocation(self):
        running_contracts = self.env['hr.contract'].search([('state', '=', 'open')])
        next_call = self.sudo().env.ref('leave_custom.ir_cron_create_monthly_allocation').nextcall.date()
        last_call = self.sudo().env.ref('leave_custom.ir_cron_create_monthly_allocation').env.context.get(
            'lastcall').date()

        for rec in running_contracts.filtered(lambda  rec: rec.employee_id):
            type = self.env['hr.leave.type'].sudo().search([('schedule_create', '=', True),('company_id','=',rec.employee_id.company_id.id)], limit=1)
            if not type:
                type = self.env['hr.leave.type'].sudo().search([('company_id','=',rec.employee_id.company_id.id)], limit=1)
            if rec.date_start:
                date = fields.date.today()
                if rec.employee_id.joining_date:
                    previous_month = date - (relativedelta(months=1))
                    previous_month_days = calendar.monthrange(previous_month.year, previous_month .month)[1]
                    total_days = (date - rec.employee_id.joining_date).days
                    emp_unpaid_leaves = self.env['hr.leave'].search(
                                            [
                                             ('employee_id', '=', rec.employee_id.id),
                                             ('state', '=', 'validate'),
                                             ('holiday_status_id.is_unpaid_leave', '=', True)])
                    if emp_unpaid_leaves:
                        total_days -= sum(emp_unpaid_leaves.mapped('number_of_days'))
                    remaining_days = total_days - previous_month_days
                    allocation_values = {
                        'name': type.name,
                        'schedule_create': True,
                        'holiday_status_id': type.id,
                        'employee_id': rec.employee_id.id,
                        'date_from': previous_month,
                    }
                    if 365 > total_days >= 180:
                        if remaining_days < 180:
                            allocation_values['number_of_days'] = 12
                        else:
                            allocation_values['number_of_days'] = 2
                    elif total_days > 365:
                        if remaining_days < 365:
                            allocation_values['number_of_days'] = 8
                        else:
                            allocation_values['number_of_days'] = 2.5
                    else:
                        continue
                    negative_allocation = self.env['hr.leave.allocation'].search(
                        [('employee_id', '=', rec.employee_id.id),
                         ('negative_balance', '>', 0)], limit=1)
                    if negative_allocation:
                        negative_allocation.negative_balance -= allocation_values['number_of_days']
                    else:
                        allocations = self.env['hr.leave.allocation'].sudo().create(allocation_values)
                        allocations.sudo().action_approve()
                        allocations.sudo().action_validate()

    def is_above_one_year(self, employee=None, date=None):
        today = date
        hire_date = fields.Date.from_string(employee.joining_date)
        if hire_date:
            return (today - hire_date) > timedelta(days=365)
        else:
            return False

    @staticmethod
    def last_day_of_month(year=None, month=None):
        last_day = calendar.monthrange(year, month)[1]
        return last_day

    def has_completed_year(self, employee=None):
        today = datetime.today()
        hire_date = fields.Datetime.from_string(employee.joining_date)
        if hire_date:
            return (today - hire_date) >= timedelta(days=365)
        else:
            return False

    def has_completed_probation(self, employee=None):
        today = datetime.today()
        hire_date = fields.Datetime.from_string(employee.joining_date)
        if hire_date:
            return (today - hire_date) >= timedelta(days=183)
        else:
            return False
