# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AssetTransfer(models.Model):
    _name = 'asset.transfer'
    _rec_name = 'name'
    _description = ''

    name = fields.Char(string="Name", required=True, )
    asset_id = fields.Many2one(comodel_name="account.asset", string="Asset", required=True, )
    location_from_id = fields.Many2one(comodel_name="stock.location", string="From Location", required=False, )
    location_to_id = fields.Many2one(comodel_name="stock.location", string="To Location", required=False, )
    employee_from_id = fields.Many2one(comodel_name="hr.employee", string="From Employee", required=False, )
    employee_to_id = fields.Many2one(comodel_name="hr.employee", string="To Employee", required=False, )
    state = fields.Selection(string="status", selection=[('draft', 'Draft'), ('confirmed', 'Confirmed'),('reject','Rejected') ], default="draft" )
    asset_request_id = fields.Many2one(comodel_name="asset.request", string="", required=False, )

    @api.onchange('asset_id','name')
    def get_location_and_employee(self):
        self.location_from_id = self.asset_id.location_id.id or False
        self.employee_from_id = self.asset_id.employee_id.id or False

    def button_confirm(self):
        if self.location_to_id:
            self.asset_id.location_id = self.location_to_id.id
        if self.employee_to_id:
            self.asset_id.employee_id = self.employee_to_id.id
        self.state = 'confirmed'
        self.asset_request_id.with_context(from_transfer=True).button_confirm()

    def button_reject(self):
        self.state = 'reject'
