# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, exceptions


class Employee(models.Model):
    _inherit = 'hr.employee'

    display_name = fields.Char(compute='_compute_display_name')

    @api.depends('name')
    def _compute_display_name(self):
        for record in self:
            if record.oe_emp_sequence:
                record.display_name = '[%s] %s' % (record.oe_emp_sequence, record.name)
            else:
                record.display_name = '%s' % record.name

    employee_sequence = fields.Char(string="")

    def name_get(self):
        new_format = []
        for rec in self:
            if rec.oe_emp_sequence and rec.name:
                new_format.append((rec.id, rec.display_name))
        return new_format
