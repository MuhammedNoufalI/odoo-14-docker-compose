from odoo import models, fields

class MedicalInsuranceCategory(models.Model):
    _name='medical.insurance.category'

    name = fields.Char('Name')