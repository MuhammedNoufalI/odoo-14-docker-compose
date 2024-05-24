# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    asset_group_id = fields.Many2one(comodel_name="asset.group", string="Asset Group", required=False, )
    location_id = fields.Many2one(comodel_name="stock.location", string="Location", required=False, )
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee", required=False, )
    assign_state = fields.Selection(string="assign Status", selection=[('assigned', 'Assigned'), ('not_assigned', 'Not Assigned'), ], required=False,compute='check_is_assigned' )

    @api.depends('employee_id')
    def check_is_assigned(self):
        if self.employee_id:
            self.assign_state = 'assigned'
        else:
            self.assign_state = 'not_assigned'




