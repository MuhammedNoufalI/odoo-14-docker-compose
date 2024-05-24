from odoo import models, fields, api, _
import datetime
from odoo.exceptions import ValidationError
import copy


class InheritPayslip(models.Model):
    _inherit = 'hr.payslip'

    maternity_leaves = fields.Integer("Maternity Leaves Full", compute="_get_maternity_leaves")
    maternity_leaves_half = fields.Integer("Maternity Leaves Half")

    # maternity_leaves = fields.Integer("Maternity Leaves")

    @api.depends('employee_id', 'date_from', 'date_to')
    def _get_maternity_leaves(self):
        for rec in self:
            if rec.employee_id and rec.date_from and rec.date_to:
                ml = self.env['hr.leave'].search(
                    [('employee_id', '=', rec.employee_id.id), ('state', '=', 'validate'),
                     ('holiday_status_id.is_maternity', '=', True), ('holiday_status_id.request_unit', '=', 'day'),
                     ('date_from', '>=', rec.date_from - datetime.timedelta(days=45)),
                     ('date_to', '<=', rec.date_to + datetime.timedelta(days=45))], limit=1)

                mlh = self.env['hr.leave'].search(
                    [('employee_id', '=', rec.employee_id.id), ('state', '=', 'validate'),
                     ('holiday_status_id.is_maternity', '=', True), ('holiday_status_id.request_unit', '=', 'half_day'),
                     ('date_from', '>=', rec.date_from - datetime.timedelta(days=15)),
                     ('date_to', '<=', rec.date_to + datetime.timedelta(days=15))], limit=1)
                if ml:
                    self.check_condition(ml, rec)
                else:
                    rec.maternity_leaves = 0
                if mlh:
                    self.check_condition(mlh, rec)
                else:
                    rec.maternity_leaves_half = 0
            else:
                rec.maternity_leaves_half = 0
                rec.maternity_leaves = 0

    def check_condition(self, ml=None, rec=None):
        if ml.holiday_status_id.request_unit == 'day':
            if (ml.date_from.date() <= rec.date_from <= ml.date_to.date()) and ml.date_to.date() >= rec.date_to:
                rec.maternity_leaves = self.get_days(rec, rec, "full_month")
            elif (ml.date_from.date() <= rec.date_from <= ml.date_to.date()) and ml.date_to.date() <= rec.date_to:
                rec.maternity_leaves = self.get_days(rec, ml, "ps_date_from_to_leave_date_to")
            elif ml.date_from.date() <= rec.date_from and ml.date_to.date() >= rec.date_to:
                rec.maternity_leaves = self.get_days(rec, ml, "leave_date_from_to_ps_date_to")
            elif ml.date_from.date() >= rec.date_from and rec.date_to >= ml.date_to.date():
                rec.maternity_leaves = 45
            elif ml.date_from.date() <= rec.date_from and rec.date_to >= ml.date_to:
                rec.maternity_leaves = self.get_days(rec, ml, "from_payslip_date_from_to_leave_date_to")
            elif rec.date_from <= ml.date_from.date() and rec.date_to <= ml.date_to.date():
                rec.maternity_leaves = self.get_days(rec, ml, "from_leave_date_from_to_payslip_date_to")
            else:
                rec.maternity_leaves = 0
        else:
            if (ml.date_from.date() <= rec.date_from <= ml.date_to.date()) and ml.date_to.date() >= rec.date_to:
                rec.maternity_leaves_half = self.get_days(rec, rec, "full_month")
            elif (ml.date_from.date() <= rec.date_from <= ml.date_to.date()) and ml.date_to.date() <= rec.date_to:
                rec.maternity_leaves_half = self.get_days(rec, ml, "ps_date_from_to_leave_date_to")
            elif ml.date_from.date() <= rec.date_from and ml.date_to.date() >= rec.date_to:
                rec.maternity_leaves_half = self.get_days(rec, ml, "leave_date_from_to_ps_date_to")
            elif ml.date_from.date() >= rec.date_from and rec.date_to >= ml.date_to.date():
                rec.maternity_leaves_half = 15
            elif ml.date_from.date() <= rec.date_from and rec.date_to >= ml.date_to:
                rec.maternity_leaves_half = self.get_days(rec, ml, "from_payslip_date_from_to_leave_date_to")
            elif rec.date_from <= ml.date_from.date() and rec.date_to <= ml.date_to.date():
                rec.maternity_leaves_half = self.get_days(rec, ml, "from_leave_date_from_to_payslip_date_to")
            else:
                rec.maternity_leaves_half = 0

    def get_days(self, rec, ml, get=None):
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
        elif get == 'from_leave_date_from_to_payslip_date_to':
            d1 = datetime.date(ml.date_from.year, ml.date_from.month, ml.date_from.day)
            d2 = datetime.date(rec.date_to.year, rec.date_to.month, rec.date_to.day)
            delta = d2 - d1
            return delta.days


class InheritHrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    is_maternity = fields.Boolean("Is Maternity Leave")


class MaternityLeaveRequest(models.Model):
    _name = 'maternity_leave.request'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one("hr.employee", string="Employee",
                                  domain=[('gender', '=', 'female')], required=True)
    child_name = fields.Char("Child Name")
    date_from = fields.Date("Date From", required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ("manager_approved", "Manager Approved"),
        ('approve', 'Approved'),
        ('reject', 'Reject'),
    ], default='draft')

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
                 ('holiday_status_id.is_maternity', '=', True)])
            if is_exists:
                for allocation in is_exists:
                    if allocation.date_from.year == rec.date_from.year:
                        raise ValidationError(_("This Employee has already avail the maternity Leaves"))
                rec.state = 'approve'
                if rec.state == 'approve':
                    self.create_maternity_leaves_allocation(rec)
            else:
                rec.state = 'approve'
                if rec.state == 'approve':
                    self.create_maternity_leaves_allocation(rec)

    def reject(self):
        for rec in self:
            rec.state = 'reject'

    def draft(self):
        for rec in self:
            rec.state = 'draft'

    def create_maternity_leaves_allocation(self, maternity_request=None):
        for rec in self:
            maternity_leave_full = self.env['hr.leave.type'].search(
                [('is_maternity', '=', True), ('request_unit', '=', 'day')], limit=1)
            if not maternity_leave_full:
                raise ValidationError(
                    _("Kindly First Create Leave Type Maternity Leave and check Is Maternity Leave To True"))
            common_val = {
                'maternity_request_id': maternity_request.id,
                'employee_id': maternity_request.employee_id.id,
                'holiday_type': 'employee',
                'gender': 'female',
            }
            full_paid = copy.deepcopy(common_val)
            full_paid.update(
                {
                    'holiday_status_id': maternity_leave_full.id,
                    'date_from': rec.date_from,
                    'date_to': rec.date_from + datetime.timedelta(days=45),
                    'number_of_days_display': 45,
                    'number_of_days': 45,
                    'name': f"45 Fully Paid Maternity Leaves for {maternity_request.employee_id.name}",
                }
            )
            new_allocation = self.env['hr.leave.allocation'].create(full_paid)
            # new_allocation.sudo().action_confirm()
            new_allocation.sudo().action_approve()
            # new_allocation.sudo().action_validate()
            maternity_leave_half = self.env['hr.leave.type'].search(
                [('is_maternity', '=', True), ('request_unit', '=', 'half_day')], limit=1)
            if not maternity_leave_half:
                raise ValidationError(
                    _("Kindly Create Leave Type 'Maternity Leaves Half Paid' with 'Take Time off' with 'Half day' and "
                      "check 'is maternity' to True"))
            else:
                half_paid = copy.deepcopy(common_val)
                half_paid.update(
                    {
                        'holiday_status_id': maternity_leave_half.id,
                        'date_from': rec.date_from + datetime.timedelta(days=46),
                        'date_to': rec.date_from + datetime.timedelta(days=60),
                        'number_of_days_display': 15,
                        'number_of_days': 15,
                        'name': f"15 Half Paid Maternity Leaves for {maternity_request.employee_id.name}",
                    }
                )
                new_half_allocation = self.env['hr.leave.allocation'].create(half_paid)
                # new_half_allocation.sudo().action_confirm()
                new_half_allocation.sudo().action_approve()
                # new_half_allocation.sudo().action_validate()
                self.create_maternity_leaves(maternity_request, maternity_leave_half, maternity_leave_full)

    def create_maternity_leaves(self, mr=None, mlh=None, mlf=None):
        leave_obj = self.env['hr.leave']
        common_vals = {
            'employee_id': mr.employee_id.id,
            'holiday_type': 'employee',
        }
        fully_paid_leaves = copy.deepcopy(common_vals)
        fully_paid_leaves.update({
            'number_of_days': 45,
            'date_from': mr.date_from,
            'date_to': mr.date_from + datetime.timedelta(days=45),
            'name': f"Fully Paid Maternity Leaves for {mr.employee_id.name}",
            'holiday_status_id': mlf.id
        })
        ful_pd_mt_leav_cr = leave_obj.create(fully_paid_leaves)
        ful_pd_mt_leav_cr.action_approve()
        # ful_pd_mt_leav_cr.action_validate()

        # Half paid maternity leaves
        half_paid_maternity_leaves = copy.deepcopy(common_vals)
        half_paid_maternity_leaves.update({
            'number_of_days': 15,
            'date_from': mr.date_from + datetime.timedelta(days=46),
            'date_to': mr.date_from + datetime.timedelta(days=60),
            'name': f"Half Paid Maternity Leaves for {mr.employee_id.name}",
            'holiday_status_id': mlh.id
        })
        half_pd_mt_leav_cr = leave_obj.create(half_paid_maternity_leaves)
        half_pd_mt_leav_cr.action_approve()
        # half_pd_mt_leav_cr.action_validate()


class InheritHrLeave(models.Model):
    _inherit = 'hr.leave'

    maternity_request_id = fields.Integer("Maternity Request Id")


class InheritHrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    maternity_request_id = fields.Integer("Maternity Request Id")
