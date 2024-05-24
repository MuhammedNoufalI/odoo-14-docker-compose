# -*- coding: utf-8 -*-

from odoo import fields, models


class HcOverTimeTypes(models.Model):
    _name = 'hc.over.time.type'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Over Time Types'

    def domain_over_time_fields(self):
        ot_fields = self.env['ir.model.fields'].search([('model', '=', 'hr.attendance'), ('name', 'like', 'otime%')]).ids
        domain = [('id', 'in', ot_fields)]
        return domain

    name = fields.Char(string="Name")
    description = fields.Char(string="Description")
    value = fields.Float(string="Value")
    over_time_type = fields.Selection([('event_based', 'Event Based'), ('time_based', 'Time Based')],
                                      string="Over Time Type")
    # is_checkout_next_day = fields.Boolean(string="Is Checkout Next Day")
    from_time = fields.Float(string="From Time")
    to_time = fields.Float(string="To Time")
    event_type = fields.Selection([('public_holiday', 'Public Holiday'), ('special_holiday', 'Special Holiday'),
                                   ('weekend', 'Weekend')], string="Event Types", copy=False)
    over_time_id = fields.Many2one('ir.model.fields', domain=domain_over_time_fields,
                                   string="Over Time (Attendance)", ondelete='cascade')
