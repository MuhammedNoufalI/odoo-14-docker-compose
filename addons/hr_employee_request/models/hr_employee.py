# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrPayslip(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def get_employee_request_deductions(self, employee , contract, data_from, date_to):
        employee_requests = self.env['hr.employee.request'].search(
            [('employee_id', '=', employee.id), ('state', '=', 'done'), ('request_date', '>=', data_from),
             ('request_date', '<=', date_to)])
        amount = 0.0
        if employee_requests:
            for request in employee_requests:
                if request.request_type_id.code == 'DED':
                    wage = contract.wage

                    if request.display_type == 'fixed_amount':
                        amount += request.fixed_amount_display
                    elif request.display_type == 'hours':

                        amount += ((wage / 30) / 8) * request.number_of_hours_display

                    elif request.display_type == 'days':
                        amount += (wage / 30) * request.number_of_days_display

                    elif request.display_type == 'other':
                        hours = ((wage / 30) / 8) * request.no_hours
                        days = (wage / 30) * request.no_days
                        amount += (hours + days)
        return amount

    @api.model
    def get_employee_request_allowances(self, employee , contract ,data_from, date_to):

        employee_requests = self.env['hr.employee.request'].search(
            [('employee_id', '=', employee.id), ('state', '=', 'done'), ('request_date', '>=', data_from),
             ('request_date', '<=', date_to)])

        amount = 0.0
        if employee_requests:
            for request in employee_requests:
                if request.request_type_id.code == 'ALW':
                    wage = contract.wage

                    if request.display_type == 'fixed_amount':
                        amount += request.fixed_amount_display
                    elif request.display_type == 'hours':

                        amount += ((wage / 30) / 8) * request.number_of_hours_display

                    elif request.display_type == 'days':
                        amount += (wage / 30) * request.number_of_days_display

                    elif request.display_type == 'other':
                        hours = ((wage / 30) / 8) * request.no_hours
                        days = (wage / 30) * request.no_days
                        amount += (hours + days)

        return amount

