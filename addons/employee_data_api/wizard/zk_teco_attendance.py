# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ZkTecoAttendance(models.TransientModel):
    _name = "zk.teco.attendance"
    _description = "ZK_Teco Attendance"

    company_id = fields.Many2one(
        'res.company', string='Company', required=True, default=lambda self: self.env.company
    )
    filter_by = fields.Selection([
        ('single_date', 'Single Date'),
        ('date_range', 'Date Range'),
        ('time_range', 'Time Range')
    ], default='single_date', required=True, string='Filter By')
    from_date = fields.Date(string='From', default=fields.Date.context_today)
    to_date = fields.Date(string='To', default=fields.Date.context_today)
    from_datetime = fields.Datetime('From', default=lambda self: fields.Datetime.now())
    to_datetime = fields.Datetime('To', default=lambda self: fields.Datetime.now())

    def import_zk_teco_attendance(self):
        company = self.company_id
        if not company.zk_id_token:
            raise UserError(_("'id_token' for the '{}' company is not configured.".format(company.name)))
        elif not company.zk_teco_url:
            raise UserError(_("'AttendHRM_MIS' for the '{}' company is not configured.".format(company.name)))

        vals = {
            'filter_by': self.filter_by,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'from_datetime': self.from_datetime,
            'to_datetime': self.to_datetime,
        }
        company.import_zk_teco_attendances(vals)
