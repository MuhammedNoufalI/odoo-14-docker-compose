# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class InheritHrContract(models.Model):
    _inherit = 'hr.contract'

    @api.model
    def create(self, vals_list):
        res = super().create(vals_list)
        if res.wage != (res.basic + res.hra + res.other_allowance):
            raise UserError(_("Total Wage is not equal to Basic+House Rent Allowance+Other Allowance"))
        else:
            return res

    def write(self, vals_list):
        res = super().write(vals_list)
        if self.wage != (self.basic + self.hra + self.other_allowance):
            raise UserError(_("Total Wage is not equal to Basic+House Rent Allowance+Other Allowance"))
        else:
            return res
