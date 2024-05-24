# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class HrContractInherit(models.Model):
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    resource_calendar_id = fields.Many2one('resource.calendar', required=True, default=False)

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        self.resource_calendar_id = False
        working_schedules = self.employee_id.branch_id.working_schedule_ids
        if working_schedules:
            domain = {'resource_calendar_id': [('id', 'in', working_schedules.ids)]}
            return {'domain': domain}

    @api.onchange('structure_type_id')
    def _onchange_structure_type_id(self):
        self.resource_calendar_id = self.company_id.resource_calendar_id.id


