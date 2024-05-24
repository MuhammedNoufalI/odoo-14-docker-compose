# -*- coding: utf-8 -*-

from odoo import fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    firstname = fields.Char(related='employee_id.firstname')
    lastname = fields.Char(related='employee_id.lastname')
    lastname2 = fields.Char(related='employee_id.lastname2')

    grade = fields.Char(related='employee_id.grade')
