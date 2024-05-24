# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime, time, timedelta
from odoo.fields import Date, Datetime
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
class Employee(models.Model):
    _inherit = 'hr.employee'

    def get_dept_and_job(self):
        arr=[]
        arr.append(self.department_id.name or '')
        arr.append( self.job_id.name or '')
        return arr