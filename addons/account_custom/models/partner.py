# -*- coding: utf-8 -*-
from odoo import models, fields,api


class Partner(models.Model):
    _inherit = 'res.partner'
    def generate_seq(self):
        for rec in self:
            if rec.customer_rank:
                rec.ref = self.env['ir.sequence'].next_by_code('customer.seq')
            elif rec.supplier_rank:
                rec.ref = self.env['ir.sequence'].next_by_code('vendor.seq')

    @api.model
    def create(self,vals):
        new_record = super(Partner, self).create(vals)
        new_record.generate_seq()
        return new_record
    # def name_get(self):
    #     new_format = []
    #     for rec in self:
    #         name = '[%s] %s' % (rec.ref, rec.name)
    #         new_format.append((rec.id, name))
    #     return new_format



