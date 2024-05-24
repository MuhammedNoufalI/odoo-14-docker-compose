# -*- coding: utf-8 -*-

from __future__ import division

import time
from datetime import datetime, timedelta
from dateutil import relativedelta

from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
from odoo import SUPERUSER_ID
import pytz


class hr_payroll(models.Model):
    _inherit = 'hr.payslip'

    def get_attendance_lines(self):
        for record in self:
            record.attend_rule_ids = None
            att = self.env['employee.attendance'].search([('employee_id', '=', record.employee_id.id),
                                                          ('date_from', '>=', record.attend_date_from),
                                                          ('date_to', '<=', record.attend_date_to)], limit=1)
            hours = record.employee_id.resource_calendar_id.work_period
            wage = record.contract_id.wage / 30 / hours

            rrule = [
                {
                    'name': 'Overtime',
                    'code': 'Overtime',
                    'num_of_days': att.bonus / hours,
                    'num_of_hours': att.bonus,
                    'pay_amount': wage * att.bonus,
                    'rule_id': record.id,
                },
                {
                    'name': 'Deduction',
                    'code': 'Deduction',
                    'num_of_days': (att.late_deduction + att.early_deduction) / hours,
                    'num_of_hours': att.late_deduction + att.early_deduction,
                    'pay_amount': -1 * wage * att.late_deduction + att.early_deduction,
                    'rule_id': record.id,
                },
                {
                    'name': 'Absence',
                    'code': 'Absence',
                    'num_of_days': att.total_absent,
                    'num_of_hours': att.total_absent * hours,
                    'pay_amount': -1 * wage * att.total_absent * hours,
                    'rule_id': record.id,
                }
            ]

            for rr in rrule:
                record.write({'attend_rule_ids': [(0, 0, rr)]})
