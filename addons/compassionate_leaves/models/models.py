from odoo import models, fields, api, _
import datetime
from odoo.exceptions import ValidationError
import copy


class InheritPayslip(models.Model):
    _inherit = 'hr.payslip'

    compassionate_leaves = fields.Integer("Bereavement Leaves Full")

    # @api.depends('employee_id', 'date_from', 'date_to')
    # def _get_compassionate_leaves(self):
    #     for rec in self:
    #         if rec.employee_id and rec.date_from and rec.date_to:
    #             ml = self.env['hr.leave'].search(
    #                 [('employee_id', '=', rec.employee_id.id), ('state', '=', 'validate'),
    #                  ('holiday_status_id.is_compassionate', '=', True), ('holiday_status_id.request_unit', '=', 'day'),
    #                  ('date_from', '>=', rec.date_from - datetime.timedelta(days=5)),
    #                  ('date_to', '<=', rec.date_to + datetime.timedelta(days=5))], limit=1)
    #             if ml:
    #                 self.compassionate_check_condition(ml, rec)
    #             else:
    #                 rec.compassionate_leaves = 0
    #         else:
    #             rec.compassionate_leaves = 0

    def compassionate_check_condition(self, ml=None, rec=None):
        if ml.holiday_status_id.request_unit == 'day':
            if (ml.date_from.date() <= rec.date_from <= ml.date_to.date()) and ml.date_to.date() >= rec.date_to:
                rec.compassionate_leaves = self.com_get_days(rec, rec, "full_month")
            elif (ml.date_from.date() <= rec.date_from <= ml.date_to.date()) and ml.date_to.date() <= rec.date_to:
                rec.compassionate_leaves = self.com_get_days(rec, ml, "ps_date_from_to_leave_date_to")
            elif ml.date_from.date() <= rec.date_from and ml.date_to.date() >= rec.date_to:
                rec.compassionate_leaves = self.com_get_days(rec, ml, "leave_date_from_to_ps_date_to")
            elif ml.date_from.date() >= rec.date_from and rec.date_to >= ml.date_to.date():
                rec.compassionate_leaves = self.com_get_days(rec, ml, "from_leave_date_from_to_leave_date_to")
            elif ml.date_from.date() <= rec.date_from and rec.date_to >= ml.date_to:
                rec.compassionate_leaves = self.com_get_days(rec, ml, "from_payslip_date_from_to_leave_date_to")
            elif rec.date_from <= ml.date_from.date() and rec.date_to <= ml.date_to.date():
                rec.compassionate_leaves = self.com_get_days(rec, ml, "from_leave_date_from_to_payslip_date_to")
            else:
                rec.compassionate_leaves = 0
        else:
            rec.compassionate_leaves = 0

    def com_get_days(self, rec, ml, get=None):
        if get == "full_month":
            d1 = datetime.date(rec.date_to.year, rec.date_to.month, rec.date_to.day)
            d2 = datetime.date(ml.date_from.year, ml.date_from.month, ml.date_from.day)
            delta = d1 - d2
            return delta.days
        elif get == "ps_date_from_to_leave_date_to":
            d1 = datetime.date(rec.date_from.year, rec.date_from.month, rec.date_from.day)
            d2 = datetime.date(ml.date_to.year, ml.date_to.month, ml.date_to.day)
            delta = d2 - d1
            return delta.days
        elif get == "leave_date_from_to_ps_date_to":
            d1 = datetime.date(ml.date_from.year, ml.date_from.month, ml.date_from.day)
            d2 = datetime.date(rec.date_to.year, rec.date_to.month, rec.date_to.day)
            delta = d1 - d2
            return delta.days
        # it's same as the second elif but for safety purpose not removed
        elif get == 'from_payslip_date_from_to_leave_date_to':
            d1 = datetime.date(rec.date_from.year, rec.date_from.month, rec.date_from.day)
            d2 = datetime.date(ml.date_to.year, ml.date_to.month, ml.date_to.day)
            delta = d2 - d1
            return delta
        elif get == 'from_leave_date_from_to_payslip_date_to':
            d1 = datetime.date(ml.date_from.year, ml.date_from.month, ml.date_from.day)
            d2 = datetime.date(rec.date_to.year, rec.date_to.month, rec.date_to.day)
            delta = d2 - d1
            return delta.days
        elif get == 'from_leave_date_from_to_leave_date_to':
            d1 = datetime.date(ml.date_from.year, ml.date_from.month, ml.date_from.day)
            d2 = datetime.date(ml.date_to.year, ml.date_to.month, ml.date_to.day)
            delta = d2 + datetime.timedelta(days=1) - d1
            if delta.days > ml.number_of_days:
                return ml.number_of_days
            return delta.days


class InheritHrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    is_compassionate = fields.Boolean("Is Bereavement Leave")


class CompassionateLeaveRequest(models.Model):
    _name = 'compassionate_leave.request'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    date_from = fields.Date("Date From", required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ("manager_approved", "Manager Approved"),
        ('approve', 'Approved'),
        ('reject', 'Reject'),
    ], default='draft')
    in_bereavement_of = fields.Selection([
        ('spouse', 'Spouse'),
        ('relative', 'Relative'),
    ], required=True)

    def manager_reject(self):
        for rec in self:
            rec.state = 'reject'

    def manager_approve(self):
        for rec in self:
            rec.state = 'manager_approved'

    def approve(self):
        for rec in self:
            is_exists = self.env['hr.leave.allocation'].search(
                [('employee_id', '=', rec.employee_id.id),
                 ('holiday_status_id.is_compassionate', '=', True), ('date_from', '>=', rec.date_from),
                 ('date_to', '<=', rec.date_from + datetime.timedelta(days=5))])
            if is_exists:
                for allocation in is_exists:
                    if allocation.date_from.year == rec.date_from.year:
                        raise ValidationError(_("This Employee has already avail the Bereavement Leaves In This Dates"))
                rec.state = 'approve'
                if rec.state == 'approve':
                    self.create_compassionate_leaves_allocation(rec)
            else:
                rec.state = 'approve'
                if rec.state == 'approve':
                    self.create_compassionate_leaves_allocation(rec)

    def reject(self):
        for rec in self:
            rec.state = 'reject'

    def draft(self):
        for rec in self:
            rec.state = 'draft'

    def create_compassionate_leaves_allocation(self, compassionate_request=None):
        for rec in self:
            compassionate_leave_full = self.env['hr.leave.type'].search(
                [('is_compassionate', '=', True), ('request_unit', '=', 'day')], limit=1)
            if not compassionate_leave_full:
                raise ValidationError(
                    _("Kindly First Create Leave Type Bereavement Leave and check Is Bereavement Leave To True"))
            full_paid = {
                'compassionate_request_id': compassionate_request.id,
                'employee_id': compassionate_request.employee_id.id,
                'holiday_type': 'employee',
                'holiday_status_id': compassionate_leave_full.id,
                'date_from': rec.date_from,
                'date_to': rec.date_from + datetime.timedelta(
                    days=5) if compassionate_request.in_bereavement_of == 'spouse' else rec.date_from + datetime.timedelta(
                    days=3),
                'number_of_days_display': 5 if compassionate_request.in_bereavement_of == 'spouse' else 3,
                'number_of_days': 5 if compassionate_request.in_bereavement_of == 'spouse' else 3,
                'name': f"{5 if compassionate_request.in_bereavement_of == 'spouse' else 3} Fully Paid Bereavement Leaves for {compassionate_request.employee_id.name}",

            }
            new_allocation = self.env['hr.leave.allocation'].create(full_paid)
            # new_allocation.sudo().action_confirm()
            new_allocation.sudo().action_approve()
            # new_allocation.sudo().action_validate()
            self.create_compassionate_leaves(compassionate_request, compassionate_leave_full)

    def create_compassionate_leaves(self, mr=None, mlf=None):
        leave_obj = self.env['hr.leave']
        common_vals = {
            'employee_id': mr.employee_id.id,
            'holiday_type': 'employee',
        }
        fully_paid_leaves = copy.deepcopy(common_vals)
        fully_paid_leaves.update({
            'number_of_days': 5 if mr.in_bereavement_of == 'spouse' else 3,
            'date_from': mr.date_from,
            'date_to': mr.date_from + datetime.timedelta(
                days=5) if mr.in_bereavement_of == 'spouse' else mr.date_from + datetime.timedelta(days=5),
            'name': f"Fully Paid Bereavement Leaves for {mr.employee_id.name}",
            'holiday_status_id': mlf.id
        })
        ful_pd_mt_leav_cr = leave_obj.create(fully_paid_leaves)
        ful_pd_mt_leav_cr.action_approve()
        # ful_pd_mt_leav_cr.action_validate()


class InheritHrLeave(models.Model):
    _inherit = 'hr.leave'

    compassionate_request_id = fields.Integer("Bereavement Request Id")


class InheritHrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    compassionate_request_id = fields.Integer("Bereavement Request Id")
