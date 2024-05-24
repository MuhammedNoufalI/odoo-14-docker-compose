# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _

class RefundReason(models.Model):
    _name = "refund.reason"
    _description = 'Refund Reason'

    name = fields.Char('Reason', translate=True)

    _sql_constraints = [
        ('constraint_unique','UNIQUE(name)','Reason Must Be Unique! ')
    ]

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, name=_("%s (copy)") % (self.name))
        return super(RefundReason, self).copy(default)