# Part of Odoo. See LICENSE file for full copyright and licensing details.

from email.mime import application
from odoo import fields, models, api


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    field_names_computed = fields.Many2many('employee.documents', compute='_get_rec', string='Fields to use COMPUTED')


    def _get_rec(self):
        emp_doc_obj = self.env['employee.documents']
        for rec in self:
            all_emp_doc_ids = emp_doc_obj.sudo().search([('employee_id', '=', rec.id)])
            if len(all_emp_doc_ids):
                rec.field_names_computed = [(6, 0, all_emp_doc_ids.ids)]
            else:
                rec.field_names_computed = False

    def _name_search(self, name, args=None, operator='like', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('oe_emp_sequence', operator, name)]
        return self._search(domain + args)
