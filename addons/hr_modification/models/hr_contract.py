from odoo import fields, api, models
from datetime import date, timedelta


class InheritHrContract(models.Model):
    _inherit = 'hr.contract'

    extra_days_to_pay = fields.Integer("Extra Days To Pay", compute="_get_addition_days")
    extra_days_paid = fields.Boolean('Extra Days Paid')
    already_deducted = fields.Boolean("Already Deducted")
    extra_days_to_deduct = fields.Integer("Extra Days To Deduct", compute='_get_addition_days')

    date_from = fields.Date("Date From", compute="_get_the_month")

    @api.depends('date_from', 'date_start')
    def _get_addition_days(self):
        for rec in self:
            if rec.date_from:
                if rec.date_start.day > 15:
                    rec.extra_days_to_deduct = 0
                    if rec.date_from < rec.date_start:
                        rec.extra_days_to_pay = (rec.date_start - rec.date_from).days
                    else:
                        rec.extra_days_to_pay = (rec.date_from - rec.date_start).days
                else:
                    rec.extra_days_to_pay = 0
                    if rec.date_from < rec.date_start:
                        rec.extra_days_to_deduct = (rec.date_start - rec.date_from).days
                    else:
                        rec.extra_days_to_deduct = (rec.date_from - rec.date_start).days
            else:
                rec.extra_days_to_pay = 0
                rec.extra_days_to_deduct = 0

    @api.depends('date_start')
    def _get_the_month(self):
        for rec in self:
            if rec.date_start:
                if rec.date_start.day > 15:
                    next_month = rec.date_start + timedelta(days=16)
                    start_of_month = date(next_month.year, next_month.month, 1)
                    rec.date_from = start_of_month
                else:
                    current_month = rec.date_start
                    start_of_month = date(current_month.year, current_month.month, 1)
                    rec.date_from = start_of_month
            else:
                rec.date_from = None
