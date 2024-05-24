from odoo import models, fields

class PosSession(models.Model):
    _inherit = 'pos.session'

    def get_order_report_values(self):
        return self.order_ids.get_report_values()
