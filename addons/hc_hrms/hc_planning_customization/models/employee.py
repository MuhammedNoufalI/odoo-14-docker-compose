# -*- coding: utf-8 -*-

import math

from datetime import datetime, timedelta, time, date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.tools import format_time
from odoo.addons.resource.models.resource import float_to_time
from odoo.exceptions import UserError, ValidationError


class Employee(models.Model):
    _inherit = "hr.employee"

    # def name_get(self):
    #     if not self.env.context.get('show_job_title'):
    #         return super().name_get()
    #     return [(employee.id, employee._get_employee_name_with_job_title()) for employee in self]

    def _get_employee_name_with_job_title(self):
        if self.job_title:
            if self.oe_emp_sequence:
                return "%s-%s (%s)" % (self.oe_emp_sequence, self.name, self.job_title)
            else:
                return "%s (%s)" % (self.name, self.job_title)
        return self.name


class ResourceResource(models.Model):
    _inherit = "resource.resource"

    employee_name = fields.Char(string='Employee Name', store=True) #compute='_compute_employee_name'

    # def _compute_employee_name(self):
    #     print("_compute_employee_name")
    #     for rec in self:
    #         if rec.employee_id:
    #             print(['aa', rec.employee_id])
            #     if len(rec.employee_id) == 1:
            #         rec.employee_name = rec.employee_id.oe_emp_sequence + rec.employee_id.name
            #     else:
            #         rec.employee_name = ''
            # else:
            #     rec.employee_name = ''

    # def _name_search(self, name, args=None, operator='like', limit=100, name_get_uid=None):
    #     print("_name_search")
    #     args = args or []
    #     domain = []
    #     if name:
    #         domain = ['|', ('name', operator, name), ('employee_name', operator, name)]
    #     return self._search(domain + args)
