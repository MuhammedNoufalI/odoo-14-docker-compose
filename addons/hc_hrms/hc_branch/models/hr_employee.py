# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    branch_id = fields.Many2one("hc.branch", string="Branch", tracking=True)
    resource_calendar_id = fields.Many2one('resource.calendar', default=False)
    visa_registered_branch_id = fields.Many2one('hc.branch', string='Visa Registered Branch')
    visa_unified_number = fields.Char(string='Unified Visa Number')
    hc_company_id = fields.Many2one('hc.company', string='HC Company', help="Not the Default Multi Company")

    def open_change_branch_wiz(self):
        return {
            'name': _('Change Branch'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'change.branch.wiz',
            'target': 'new',
            'view_id': self.env.ref('hc_branch.change_branch_wiz_views').id,
        }
