
from odoo import api, models, _
from odoo.exceptions import UserError


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    @api.constrains('acc_number')
    def _oe_check_acc_number(self):
        for rec in self:
            if rec.acc_number and len(rec.acc_number) > 23:
                raise UserError(_("Invalid IBAN Number!"))
