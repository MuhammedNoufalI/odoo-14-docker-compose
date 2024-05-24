# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HcApiLogs(models.Model):
    _name = 'hc.api.logs'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'API LOGS'

    name = fields.Text(string="Name")
    # response = fields.Text(string="Response")
    status_code = fields.Char(string="Status Code")
    status_description = fields.Selection([('failed', 'Failed'), ('success', 'Success')], string="Status Description")
    datetime = fields.Datetime(string="Datetime")
    return_message = fields.Text("Return Message")
    # error_message = fields.Text("Error Message")
    input = fields.Text("Input")
    output = fields.Text("Output")
