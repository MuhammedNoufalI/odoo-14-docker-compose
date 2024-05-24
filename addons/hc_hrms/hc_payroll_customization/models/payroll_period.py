from datetime import datetime

from odoo.exceptions import ValidationError
from odoo import _, api, fields, models
import dateutil.relativedelta


class PayrollPeriod(models.Model):
    _name = "hc.payroll.period"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Payroll Period"
    _rec_name = "code"

    code = fields.Char(string="Code", required=True, tracking=True, default=lambda self: _('New'))
    # name = fields.Char(required=True, translate=True, tracking=True)
    date_from = fields.Date(string="From Date", required=True, tracking=True)
    date_to = fields.Date(string="To Date", required=True, tracking=True)
    year = fields.Integer(string="Year", default=lambda self: fields.datetime.now().year)
    interval = fields.Integer(string="Days", readonly=1)
    payroll_type = fields.Selection([('regular', 'Regular'), ('special', 'Special')], string="Payroll Type",
                                    default='regular')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed')], default='draft')
    _sql_constraints = [
        ('name_uniq', 'unique (code)', "Code already exists, It Must Be Unique !"),
    ]

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def set_to_draft(self):
        self.write({'state': 'draft'})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                date = datetime.strptime(vals['date_to'], '%Y-%m-%d')
                month = date.strftime("%B")
                prefix = self.env['ir.sequence'].next_by_code('hc.payroll.period.sequence') or ''
                vals['code'] = '%s%s' % (month and '%s: ' % prefix or '', month)
    
            if vals.get('date_from') and vals.get('date_from'):
                if vals.get('date_from') < vals.get('date_from'):
                    raise ValidationError("End date must be greater than start date")
        records = super(PayrollPeriod, self).create(vals_list)
        return records

    def write(self, vals):
        if self.date_from and self.date_to:
            if str(self.date_to) < str(self.date_from):
                raise ValidationError("End date must be greater than start date")
        return super(PayrollPeriod, self).write(vals)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.payroll_type != 'special':
                # Starting date must be prior to the ending date
                date_from = rec.date_from
                date_to = rec.date_to
                if date_to and date_from:
                    if date_to < date_from:
                        raise ValidationError(_('The ending date must not be prior to the starting date.'))
                domain = [
                    ('id', '!=', rec.id),
                    '|', '|',
                    '&', ('date_from', '<=', rec.date_from), ('date_to', '>=', rec.date_from),
                    '&', ('date_from', '<=', rec.date_to), ('date_to', '>=', rec.date_to),
                    '&', ('date_from', '<=', rec.date_from), ('date_to', '>=', rec.date_to),
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(_('You can not have an overlap between two payroll period, '
                                            'please correct the start and/or end dates of your payroll Period.'))

    @api.onchange('date_from', 'date_to')
    def _onchange_date_interval(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                if rec.date_to > rec.date_from:
                    rec.interval = int((rec.date_to - rec.date_from).days) + 1
