# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResourceResource(models.Model):
    _inherit = "resource.resource"

    calendar_id = fields.Many2one(
        "resource.calendar", string='Working Time',
        required=False, domain="[('company_id', '=', company_id)]",
        help="Define the schedule of resource")