from odoo import models, api


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    @api.model
    def create(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].upper()
        return super(HrDepartment, self).create(vals)

    def write(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].upper()
        return super(HrDepartment, self).write(vals)
