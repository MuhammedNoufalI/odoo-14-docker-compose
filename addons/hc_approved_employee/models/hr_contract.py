from odoo import api, fields, models, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    state = fields.Selection(selection_add=[('not_approved', 'Not Approved'), ('draft',), ], default='not_approved')

    @api.model
    def create(self, vals):
        res = super(HrContract, self).create(vals)
        res['active'] = False
        return res

    def button_approve_contract(self):
        for rec in self:
            rec.active = True
            rec.state = 'draft'
