# -*- coding: utf-8 -*-

from odoo import api, fields, models, _



class hr_payroll(models.Model):
    _inherit = 'hr.payslip'

    ticket_amount = fields.Float()
