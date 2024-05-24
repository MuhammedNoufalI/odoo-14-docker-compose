from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    compare_attendance_with_machine = fields.Boolean(
        string='Compare Attendance With Machine Data',
        config_parameter='hr_modification.compare_attendance_with_machine',
    )
