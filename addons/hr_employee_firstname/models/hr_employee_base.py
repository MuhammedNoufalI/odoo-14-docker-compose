from odoo import api, fields, models, _


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    oe_emp_sequence = fields.Char(
        string='Employee Reference', copy=False,
        index=True, default=lambda self: _('New'), required=True,
    )
    firstname = fields.Char()
    lastname = fields.Char()
