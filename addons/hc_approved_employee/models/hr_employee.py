from odoo import api, fields, models, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    state = fields.Selection([
        ("not_approved","Not Approved"),
        ("approved", "Approved")
    ], default='not_approved')

    @api.model
    def create(self, vals):
        res = super(HrEmployee, self).create(vals)
        res['active'] = False
        return res

    def button_approve_employee(self):
        for rec in self:
            rec.active = True
            rec.state = 'approved'




