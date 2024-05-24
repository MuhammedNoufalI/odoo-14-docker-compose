# -*- coding: utf-8 -*-

from odoo import fields, models


class HcCompany(models.Model):
    _name = 'hc.company'
    _description = 'HC Company'

    name = fields.Char(string="Name")
