# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class HcKeyHolder(models.Model):
    _name = 'hc.key.holder'
    _inherit = 'mail.thread'
    _description = 'Key Holder'

    employee_id = fields.Many2one('hr.employee', string="Employee")
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    kh_warning_count = fields.Float(string="Warning Count", default=0)
    branch_id = fields.Many2one('hc.branch', string="Branch Id")
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed')], string="State", default='draft')

    def action_confirm(self):
        for rec in self:
            rec.write({'state': 'confirmed'})

    def set_to_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})

    @api.constrains('date_from', 'date_to')
    def _check_overlapping_dates(self):
        for rec in self:
            # Starting date must be prior to the ending date
            date_from = rec.date_from
            date_to = rec.date_to
            if date_to and date_from:
                if date_to < date_from:
                    raise ValidationError(_('The ending date must not be prior to the starting date.'))
            domain = [
                ('id', '!=', rec.id),
                '|', '|',
                '&', ('date_from', '<=', rec.date_from), ('date_to', '>=', rec.date_from),
                '&', ('date_from', '<=', rec.date_to), ('date_to', '>=', rec.date_to),
                '&', ('date_from', '<=', rec.date_from), ('date_to', '>=', rec.date_to),
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(_("You can not have an overlap between key holder's period, "
                                        "please correct the start and/or end dates of your New Key Holder's Period."))
