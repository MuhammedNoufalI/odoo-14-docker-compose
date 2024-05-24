# -*- coding: utf-8 -*-
# Part of Hashcode. See LICENSE file for full copyright and licensing details.


from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_compensatory_off = fields.Boolean(string="Is Compensatory Off",
                                      help="Compensatory Off for Over time on the weekend")
