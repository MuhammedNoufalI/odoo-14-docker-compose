# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InheritDepartWizard(models.TransientModel):
    _inherit = 'hr.departure.wizard'

    transfer_to = fields.Many2one('res.company', 'Transfer To')
    business_unit = fields.Char("Business Unit")
    departure_reason = fields.Selection(selection_add=[('transfer', 'Transfer')])

    def action_register_departure(self):
        res = super().action_register_departure()
        self.employee_id.business_unit = self.business_unit
        return res


class InheritHrEmployee(models.Model):
    _inherit = 'hr.employee'

    departure_reason = fields.Selection(selection_add=[('transfer', 'Transfer')])
