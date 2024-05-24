from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    certificate = fields.Selection(
        selection_add=[('school', 'School'), ('secondary_school', 'Secondary School'), ('diploma', 'Diploma'),
                       ('phd', 'PHD')])
