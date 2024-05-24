# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, exceptions


class PBank(models.Model):
    _inherit = 'res.partner.bank'
    acc_number = fields.Char(string='IBAN Number')
    @api.constrains('acc_number')
    def check_acc_number(self):
        for rec in self:
            if rec.acc_number and len(rec.acc_number) > 23:
                raise exceptions.ValidationError(_("IBAN Number must be less than or equal 23 char"))

class Employee(models.Model):
    _inherit = 'hr.employee'
    bank_account_id = fields.Many2one(string='IBAN')
