# -*- coding:utf-8 -*-

from email.policy import default
from odoo import api, fields, models
from datetime import date
import logging
_logger = logging.getLogger(__name__)


class CertificateType(models.Model):
    _name = 'certificate.type'
    _description = 'Certificate Type'

    name = fields.Char(string='Certificate Types')
    reviewer = fields.Many2one('res.groups',string='Reviewer')
    approver = fields.Many2one('res.users',string='Approver')
    content =fields.Html('Content')




 