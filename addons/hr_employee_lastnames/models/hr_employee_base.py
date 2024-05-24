from odoo import fields, models


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    firstname = fields.Char("First Name")
    lastname = fields.Char("Middle Name")
    lastname2 = fields.Char("Last Name")

    grade = fields.Char("Grade")
