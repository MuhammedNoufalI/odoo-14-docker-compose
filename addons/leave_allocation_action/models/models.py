# -*- coding: utf-8 -*-

from odoo import models


class InheritHrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    def first_approval(self):
        for rec in self:
            if rec.state == 'confirm':
                rec.action_approve()

    def second_approval(self):
        for rec in self:
            if rec.state == 'validate1':
                rec.action_validate()
