# -*- coding: utf-8 -*-
from odoo import models, api, fields
from odoo.osv import expression
from odoo.tools.translate import _


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'
    request_id = fields.Many2one(comodel_name='hr.employee.request', string='Request')


HrPayslipWorkedDays()


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        res = super(HrPayslip, self).get_worked_day_lines(contracts, date_from, date_to)
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            domain_or = expression.OR([[('employee_id', '=', contract.employee_id.id)],
                                       [('mode_company_id', '=', contract.employee_id.company_id.id)],
                                       [('category_id', 'in', [contract.employee_id.category_ids.id])],
                                       [('department_id', '=', contract.employee_id.department_id.id)],
                                       ])
            domain = expression.AND([domain_or, [('state', '=', 'done'),
                                                 ('request_date_from', '<=', date_to),
                                                 ('request_date_to', '>=', date_from)]])
            employee_request = self.env['hr.employee.request'].search(domain)
            requests_res = []
            for record in employee_request:
                hours = record.number_of_days_display if record.request_type_id.type == 'hours' else record.no_hours if record.request_type_id.type == 'other' else 0
                days = record.number_of_days_display if record.request_type_id.type == 'days' else record.no_hours if record.request_type_id.type == 'other' else 0
                for dict_item in requests_res:
                    if dict_item.get('code', False) == record.request_type_id.code:
                        hours_dict = dict_item.get('number_of_hours', 0) + hours
                        days_dict = dict_item.get('number_of_days', 0) + days
                        dict_item.update({'number_of_days': days_dict, 'hours_dict': hours_dict})
                request_data = {
                    'name': _("Employee Request %s") % (record.request_type_id.name),
                    'sequence': 10,
                    'code': record.request_type_id.code,
                    'number_of_days': days,
                    'number_of_hours': hours,
                    'contract_id': contract.id,
                }
                requests_res.append(request_data)
            if requests_res:
                res.extend(requests_res)
        return res


HrPayslip()
