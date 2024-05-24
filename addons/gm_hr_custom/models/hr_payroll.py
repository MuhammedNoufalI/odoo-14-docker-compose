# -*- coding: utf-8 -*-

from __future__ import division

import time
from datetime import datetime, timedelta
from dateutil import relativedelta

from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
from odoo import SUPERUSER_ID
import pytz


class HrPayrollConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    payroll_from_day = fields.Integer(string="Day")
    payroll_from_month = fields.Selection([('0','Current Month'),('-1', 'Previous Month')])

    payroll_to_day = fields.Integer(string="Day")
    payroll_to_month = fields.Selection([('0','Current Month'),('-1', 'Previous Month')])


    @api.model
    def get_values(self):
        res = super(HrPayrollConfig, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        payroll_from_day = params.get_param('payroll_from_day', default=False)
        payroll_from_month = params.get_param('payroll_from_month', default=False)
        payroll_to_day = params.get_param('payroll_to_day', default=False)
        payroll_to_month = params.get_param('payroll_to_month', default=False)
        res.update(
            payroll_from_day=payroll_from_day,
            payroll_from_month=payroll_from_month,
            payroll_to_day=payroll_to_day,
            payroll_to_month=payroll_to_month,
        )
        return res

    def set_values(self):
        super(HrPayrollConfig, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("payroll_from_day",
                                                         self.payroll_from_day)
        self.env['ir.config_parameter'].sudo().set_param("payroll_from_month",
                                                         self.payroll_from_month)
        self.env['ir.config_parameter'].sudo().set_param("payroll_to_day",
                                                         self.payroll_to_day)
        self.env['ir.config_parameter'].sudo().set_param("payroll_to_month",
                                                         self.payroll_to_month)

class HrPayrollRule(models.Model):
    _name = 'hr.payslip.rule'
    _rec_name = 'name'

    name = fields.Char('Description')
    code = fields.Char('Code')
    num_of_days = fields.Float(string="Number Of Days", required=False, )
    num_of_hours = fields.Float(string="Number Of Hours", required=False, )
    pay_amount = fields.Float(string="Pay Amount", required=False, )
    rule_id = fields.Many2one(comodel_name="hr.payslip", string="Payslip", required=False, )


class hr_payroll(models.Model):
    _inherit = 'hr.payslip'

    attend_rule_ids = fields.One2many(comodel_name="hr.payslip.rule", string="Attendance Rules",
                                      inverse_name='rule_id', )
    deduction_amount = fields.Float(string="Deduction Amount", required=False, compute='_compute_deduction_amount')
    overtime_amount = fields.Float(string="OverTime Amount", required=False, compute='_compute_overtime_amount',store=True)
    absent_amount = fields.Float(string="Absence Amount", required=False, compute='_compute_absent_amount',store=True)

    def _get_from_date(self):
        from_day = self.env['ir.config_parameter'].sudo().get_param('payroll_from_day')
        from_month = self.env['ir.config_parameter'].sudo().get_param('payroll_from_month')
        return str(datetime.now() + relativedelta.relativedelta(months=int(from_month), day=int(from_day)))[:10]

    def _get_to_date(self):
        to_day = self.env['ir.config_parameter'].sudo().get_param('payroll_to_day')
        to_month = self.env['ir.config_parameter'].sudo().get_param('payroll_to_month')
        return str(datetime.now() + relativedelta.relativedelta(months=int(to_month), day=int(to_day)))[:10]

    attend_date_from = fields.Date(string='Date From', readonly=True, required=True,
                                   default=_get_from_date,
                                   states={'draft': [('readonly', False)]})

    attend_date_to = fields.Date(string='Date To', readonly=True, required=True,
                                 default=_get_to_date,
                                 states={'draft': [('readonly', False)]})
    is_refund = fields.Boolean(string="Refund")
    # move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=False, copy=False)



    ##################################### edit
    #@api.multi
    @api.onchange('employee_id')
    def get_contract_per_customerr(self):
        # #print("get_contract_per_customerr")
        list = []
        if self.employee_id.contracts_count == 1 :
            self.contract_id = self.env['hr.contract'].search([('employee_id', '=' , self.employee_id.id)])
        if self.employee_id.contracts_count > 1 :
            for rec in self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)]):
                list.append(rec.id)

            return {
                'domain' : {
                    'contract_id': [('id' , 'in' , list)]
                }
            }
    ##################################### edit

    #@api.multi
    def refund_sheet(self):
        for payslip in self:
            if payslip.is_refund:
                raise UserError(_('You Cannot Refund Payslip More one time.'))
            copied_payslip = payslip.copy(
                {'credit_note': True, 'is_refund': True, 'name': _('Refund: ') + payslip.name})
            payslip.update({'is_refund': True})
            copied_payslip.input_line_ids = payslip.input_line_ids
            copied_payslip.compute_sheet()
            copied_payslip.action_payslip_done()
        formview_ref = self.env.ref('hr_payroll.view_hr_payslip_form', False)
        treeview_ref = self.env.ref('hr_payroll.view_hr_payslip_tree', False)
        return {
            'name': ("Refund Payslip"),
            'view_mode': 'tree, form',
            'view_id': False,
            # 'view_type': 'form',
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % copied_payslip.ids,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'),
                      (formview_ref and formview_ref.id or False, 'form')],
            'context': {}
        }

    @api.model
    def create(self, values):
        rec_toggle = self.env.ref('hr_payroll.hr_payroll_rule_officer')
        rec_toggle.active = False
        res = super(hr_payroll, self).create(values)
        payrolls = self.search([('employee_id', '=', res.employee_id.id)]).filtered(lambda pay: not pay.is_refund)
        for payroll in payrolls:
            if payroll.id != res.id and not res.is_refund:
                if (payroll.date_to >= res.date_from >= payroll.date_from) or (
                        payroll.date_to >= res.date_to >= payroll.date_from):
                    raise UserError(_('You Cannot Create Two Payslips for one Employee In Same Period.'))
        return res

    def get_attendance_lines(self):
        pass
        # for record in self:
        #     record.attend_rule_ids.unlink()
        #     f_l_h_l = s_l_h_l = t_l_h_l = fo_l_h_l = fi_l_h_l = []
        #     f_l_h_e = s_l_h_e = t_l_h_e = fo_l_h_e = fi_l_h_e = []
        #     first_hour_late = []
        #     second_hour_late = []
        #     third_hour_late = []
        #     four_hour_late = []
        #     five_hour_late = []
        #     first_hour_early = []
        #     second_hour_early = []
        #     third_hour_early = []
        #     four_hour_early = []
        #     five_hour_early = []
        #     absent_rules = []
        #     absent_rule_take = []
        #     val_absence = 0.0
        #     overtime_hour = 0.0
        #     val_deduction = 0.0
        #     user_id = self.env['res.users']
        #     attendance_obj = self.env['hr.attendance']
        #     holidays_obj = self.env['hr.leave']
        #     DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        #     user = user_id.browse(SUPERUSER_ID)
        #     tz = pytz.timezone((self.env.user.tz or 'UTC'))
        #
        #     # tz = pytz.utc
        #     # print("tzz",tz)
        #     def daterange(start_date, end_date):
        #         for n in range(int((end_date - start_date).days) + 1):
        #             yield start_date + timedelta(n)
        #
        #     def get_time_from_float(float_time):
        #         str_time = str(float_time)
        #         str_hour = str_time.split('.')[0]
        #         str_minute = ("%2d" % int(str(float("0." + str_time.split('.')[1]) * 60).split('.')[0])).replace(' ',
        #                                                                                                          '0')
        #         minute = (float(str_hour) * 60) + float(str_minute)
        #         return minute
        #
        #     if not record.employee_id.attendance_id:
        #         raise Warning(_("You Should Choose Attendance Rules on Employee"))
        #     if record.employee_id.attendance_id.rule_deduction_ids:
        #         for line in record.employee_id.attendance_id.rule_deduction_ids:
        #             if line.type == 'late':
        #                 if line.hour_level == '1':
        #                     first_hour_late.append(line.id)
        #                 elif line.hour_level == '2':
        #                     second_hour_late.append(line.id)
        #                 elif line.hour_level == '3':
        #                     third_hour_late.append(line.id)
        #                 elif line.hour_level == '4':
        #                     four_hour_late.append(line.id)
        #                 elif line.hour_level == '5':
        #                     five_hour_late.append(line.id)
        #             elif line.type == 'early':
        #                 if line.hour_level == '1':
        #                     first_hour_early.append(line.id)
        #                 elif line.hour_level == '2':
        #                     second_hour_early.append(line.id)
        #                 elif line.hour_level == '3':
        #                     third_hour_early.append(line.id)
        #                 elif line.hour_level == '4':
        #                     four_hour_early.append(line.id)
        #                 elif line.hour_level == '5':
        #                     five_hour_early.append(line.id)
        #             else:
        #                 absent_rules.append(line.id)
        #
        #     permission = record.employee_id.attendance_id.permission or 0.0
        #     search_domain = [
        #         ('check_in', '>=', record.attend_date_from),
        #         ('check_out', '<=', record.attend_date_to),
        #         ('employee_id', '=', record.employee_id.id),
        #     ]
        #     hours = record.employee_id.resource_calendar_id.work_period
        #     attendance_ids = attendance_obj.search(search_domain)
        #     start_date = datetime.strptime(str(record.attend_date_from), "%Y-%m-%d")
        #     end_date = datetime.strptime(str(record.attend_date_to), "%Y-%m-%d")
        #     weekend_days = [day.dayofweek for day in record.employee_id.resource_calendar_id.weekend_ids]
        #
        #
        #
        #     attendances = [str(x.check_in.date()) for x in attendance_ids]
        #
        #     # print("attendances",attendances)
        #     # attendances = [x.check_in[0:10] for x in attendance_ids]
        #
        #     for single_date in daterange(start_date, end_date):
        #         perm_morning = 0.0
        #         perm_afternoon = 0.0
        #         hour_levle = []
        #         hour_levle_early = []
        #         late_rule_exist = False
        #         early_rule_exist = False
        #         if str(single_date.date()) in attendances:
        #             print (str(single_date.date()) ,'34444444333333333334444444444444')
        #             for attendance in attendance_ids:
        #                 print ('656565656565656565656565656565656565656')
        #                 attendance_datetime = pytz.utc.localize(datetime.strptime(str(attendance.check_in), DATETIME_FORMAT)).astimezone(tz)
        #                 # print("attendance_datetime",attendance_datetime)
        #                 # print(attendance_datetime.date(),single_date.date())
        #                 if attendance_datetime.date() == single_date.date():
        #                     for leave_perm in self.env['hr.leave'].search([('employee_id','=',record.employee_id.id)]):
        #                         leave_perm_date = pytz.utc.localize(datetime.strptime(str(leave_perm.request_date_from), "%Y-%m-%d")).astimezone(tz)
        #                         if leave_perm_date.date() == single_date.date():
        #                             if leave_perm.request_unit_hours:
        #                                 if leave_perm.permission_type == 'morning':
        #                                     perm_morning += (float(leave_perm.request_hour_to) - float(leave_perm.request_hour_from))
        #                                 if leave_perm.permission_type == 'afternoon':
        #                                     perm_afternoon += (float(leave_perm.request_hour_to) - float(leave_perm.request_hour_from))
        #
        #                     print (perm_morning,'oooooooooooooooooooooooiiiiiiiiiiiiiiiiii')
        #                     print (perm_afternoon,'dddddddddddddddddddddddddddddddddd')
        #                     # print("if ")
        #                     late = 0.0
        #                     early = 0.0
        #                     if attendance.late > 0.0:
        #                         print (attendance.late,'qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq')
        #                         late = get_time_from_float(attendance.late - perm_morning)
        #                         # print("if attendance.late > 0.0:",get_time_from_float(attendance.late))
        #                         if permission > 0.0:
        #                             # print("permission")
        #                             if permission >= late:
        #                                 permission -= late
        #                                 late = 0.0
        #                                 # print("permission >= late" , permission , late)
        #                             else:
        #                                 late -= permission
        #                                 permission = 0.0
        #                                 # print("else",late,permission)
        #                         if late > 0.0:
        #                             print ('33333333wwwwwwwwwwwwwwwwwwwww')
        #                             # print("if late > 0.0:",late)
        #                             if record.employee_id.attendance_id.rule_deduction_ids:
        #                                 for rule in record.employee_id.attendance_id.rule_deduction_ids.filtered(
        #                                         lambda r: r.type == 'late'):
        #                                     hour_levle.append(int(rule.hour_level))
        #                                     # print("for rule in record.employee_id.attendance_id")
        #                                     if rule.hour_level == '1':
        #                                         if attendance.repeate_late == rule.repetition:
        #
        #                                             time_from = get_time_from_float(rule.time_from)
        #                                             time_to = get_time_from_float(rule.time_to)
        #                                             print (late,'late')
        #                                             print (time_from,'time_from')
        #                                             print (time_to,'time_to')
        #                                             if late >= time_from and late <= time_to:
        #                                                 late_rule_exist = True
        #                                                 if rule.id not in f_l_h_l:
        #                                                     print ('1111111111111111')
        #                                                     f_l_h_l.append(rule.id)
        #                                                     if rule.warning:
        #                                                         print ('222222222222')
        #                                                         break
        #                                                     else:
        #                                                         print ('333333333333333')
        #                                                         val_deduction += rule.deduction
        #                                                         break
        #                                                 else:
        #                                                     print ('else 1111111111111111111')
        #                                                     if rule.id != int(first_hour_late[-1]):
        #                                                         print ('else 2222222222222222')
        #                                                         continue
        #                                                     else:
        #                                                         print ('else 333333333333333')
        #                                                         if rule.warning:
        #                                                             print ('else 444444444444444')
        #                                                             break
        #                                                         else:
        #                                                             print ('else 555555555555555')
        #                                                             val_deduction += rule.deduction
        #                                                             break
        #                                     elif rule.hour_level == '2':
        #                                         if attendance.repeate_late == rule.repetition:
        #
        #                                             print ('vvvvnnnnnnnnnnnnnnnnnnnnnnnnnnnn')
        #                                             time_from = get_time_from_float(rule.time_from)
        #                                             time_to = get_time_from_float(rule.time_to)
        #                                             if late >= time_from and late <= time_to:
        #                                                 late_rule_exist = True
        #                                                 if rule.id not in s_l_h_l:
        #                                                     s_l_h_l.append(rule.id)
        #                                                     if rule.warning:
        #                                                         break
        #                                                     else:
        #                                                         val_deduction += rule.deduction
        #                                                         break
        #                                                 else:
        #                                                     if rule.id != int(second_hour_late[-1]):
        #                                                         continue
        #                                                     else:
        #                                                         if rule.warning:
        #                                                             break
        #                                                         else:
        #                                                             val_deduction += rule.deduction
        #                                                             break
        #                                     elif rule.hour_level == '3':
        #                                         if attendance.repeate_late == rule.repetition:
        #
        #                                             time_from = get_time_from_float(rule.time_from)
        #                                             time_to = get_time_from_float(rule.time_to)
        #                                             if late >= time_from and late <= time_to:
        #                                                 late_rule_exist = True
        #                                                 if rule.id not in t_l_h_l:
        #                                                     t_l_h_l.append(rule.id)
        #                                                     if rule.warning:
        #                                                         break
        #                                                     else:
        #                                                         val_deduction += rule.deduction
        #                                                 else:
        #                                                     if rule.id != int(third_hour_late[-1]):
        #                                                         continue
        #                                                     else:
        #                                                         if rule.warning:
        #                                                             break
        #                                                         else:
        #                                                             val_deduction += rule.deduction
        #                                                             break
        #                                     elif rule.hour_level == '4':
        #                                         if attendance.repeate_late == rule.repetition:
        #
        #                                             time_from = get_time_from_float(rule.time_from)
        #                                             time_to = get_time_from_float(rule.time_to)
        #                                             if late >= time_from and late <= time_to:
        #                                                 late_rule_exist = True
        #                                                 if rule.id not in fo_l_h_l:
        #                                                     fo_l_h_l.append(rule.id)
        #                                                     if rule.warning:
        #                                                         break
        #                                                     else:
        #                                                         val_deduction += rule.deduction
        #                                                 else:
        #                                                     if rule.id != int(four_hour_late[-1]):
        #                                                         continue
        #                                                     else:
        #                                                         if rule.warning:
        #                                                             break
        #
        #                                                         else:
        #                                                             val_deduction += rule.deduction
        #                                                             break
        #                                     elif rule.hour_level == '5':
        #                                         if attendance.repeate_late == rule.repetition:
        #
        #                                             time_from = get_time_from_float(rule.time_from)
        #                                             time_to = get_time_from_float(rule.time_to)
        #                                             if late >= time_from and late <= time_to:
        #                                                 late_rule_exist = True
        #                                                 if rule.id not in fi_l_h_l:
        #                                                     fi_l_h_l.append(rule.id)
        #                                                     if rule.warning:
        #                                                         break
        #                                                     else:
        #                                                         val_deduction += rule.deduction
        #                                                 else:
        #                                                     if rule.id != int(second_hour_late[-1]):
        #                                                         continue
        #                                                     else:
        #                                                         if rule.warning:
        #                                                             break
        #
        #                                                         else:
        #                                                             val_deduction += rule.deduction
        #                                                             break
        #                                 if not late_rule_exist:
        #                                     max_repetition = []
        #                                     if hour_levle:
        #                                         print ('mokhleeeeeeeeeeeeeffffffffff',str(max(hour_levle)))
        #                                         for rule12 in record.employee_id.attendance_id.rule_deduction_ids.filtered(
        #                                                 lambda r: r.hour_level == str(max(hour_levle))):
        #                                             max_repetition.append(rule12.repetition)
        #                                         for rule2 in record.employee_id.attendance_id.rule_deduction_ids.filtered(
        #                                                 lambda r: r.hour_level == str(max(hour_levle)) and r.repetition == max(max_repetition)):
        #
        #                                             time_from = get_time_from_float(rule2.time_from)
        #                                             time_to = get_time_from_float(rule2.time_to)
        #                                             print ('time_fromooooooooooo',time_from)
        #                                             print ('time_toooooooooooooo',time_to)
        #                                             if late >= time_from and attendance.repeate_late >= rule2.repetition:
        #                                                 print ('xxxxxxxxxxxccccccccccvvvvvvvvvvvvvvvvvvvvv')
        #                                                 # if rule2.id not in fi_l_h_l:
        #                                                 #     fi_l_h_l.append(rule2.id)
        #                                                 #     if rule2.warning:
        #                                                 #         break
        #                                                 #     else:
        #                                                 #         val_deduction += rule2.deduction
        #                                                 # else:
        #                                                 #     if rule2.id != int(second_hour_late[-1]):
        #                                                 #         continue
        #                                                 #     else:
        #                                                 if rule2.warning:
        #                                                     continue
        #
        #                                                 else:
        #                                                     val_deduction += rule2.deduction
        #                                                     # break
        #
        #
        #                     if attendance.early > 0.0:
        #                         early = get_time_from_float(attendance.early - perm_afternoon)
        #                         if permission > 0.0:
        #                             if permission >= early:
        #                                 permission -= early
        #                                 early = 0.0
        #                             else:
        #                                 early -= permission
        #                                 permission = 0.0
        #
        #                         if early > 0.0:
        #                             if record.employee_id.attendance_id.rule_deduction_ids:
        #                                 for rule in record.employee_id.attendance_id.rule_deduction_ids.filtered(
        #                                         lambda r: r.type == 'early'):
        #                                     hour_levle_early.append(int(rule.hour_level))
        #                                     if rule.hour_level == '1':
        #                                         if attendance.repeate_early == rule.repetition:
        #
        #                                             time_from = get_time_from_float(rule.time_from)
        #                                             time_to = get_time_from_float(rule.time_to)
        #                                             if early >= time_from and early <= time_to:
        #                                                 early_rule_exist = True
        #                                                 if rule.id not in f_l_h_e:
        #                                                     f_l_h_e.append(rule.id)
        #                                                     if rule.warning:
        #                                                         break
        #                                                     else:
        #                                                         val_deduction += rule.deduction
        #                                                         break
        #                                                 else:
        #                                                     if rule.id != int(first_hour_early[-1]):
        #                                                         continue
        #                                                     else:
        #                                                         if rule.warning:
        #                                                             break
        #                                                         else:
        #                                                             val_deduction += rule.deduction
        #                                                             break
        #                                     elif rule.hour_level == '2':
        #                                         if attendance.repeate_early == rule.repetition:
        #
        #                                             time_from = get_time_from_float(rule.time_from)
        #                                             time_to = get_time_from_float(rule.time_to)
        #                                             if early >= time_from and early <= time_to:
        #                                                 early_rule_exist = True
        #                                                 if rule.id not in s_l_h_e:
        #                                                     s_l_h_e.append(rule.id)
        #                                                     if rule.warning:
        #                                                         break
        #                                                     else:
        #                                                         val_deduction += rule.deduction
        #                                                         break
        #                                                 elif s_l_h_e == second_hour_early:
        #                                                     if rule.id != int(second_hour_early[-1]):
        #                                                         continue
        #                                                     else:
        #                                                         if rule.warning:
        #                                                             break
        #                                                         else:
        #                                                             val_deduction += rule.deduction
        #                                                             break
        #                                     elif rule.hour_level == '3':
        #                                         if attendance.repeate_early == rule.repetition:
        #
        #                                             time_from = get_time_from_float(rule.time_from)
        #                                             time_to = get_time_from_float(rule.time_to)
        #                                             if early >= time_from and early <= time_to:
        #                                                 early_rule_exist = True
        #                                                 if rule.id not in t_l_h_e:
        #                                                     t_l_h_e.append(rule.id)
        #                                                     if rule.warning:
        #                                                         break
        #                                                     else:
        #                                                         val_deduction += rule.deduction
        #                                                         break
        #                                                 else:
        #                                                     if rule.id != int(third_hour_late[-1]):
        #                                                         continue
        #                                                     else:
        #                                                         if rule.warning:
        #                                                             break
        #                                                         else:
        #                                                             val_deduction += rule.deduction
        #                                                             break
        #                                     elif rule.hour_level == '4':
        #                                         if attendance.repeate_early == rule.repetition:
        #
        #                                             time_from = get_time_from_float(rule.time_from)
        #                                             time_to = get_time_from_float(rule.time_to)
        #                                             if early >= time_from and early <= time_to:
        #                                                 early_rule_exist = True
        #                                                 if rule.id not in fo_l_h_e:
        #                                                     fo_l_h_e.append(rule.id)
        #                                                     if rule.warning:
        #                                                         break
        #                                                     else:
        #                                                         val_deduction += rule.deduction
        #                                                         break
        #                                                 else:
        #                                                     if rule.id != int(four_hour_early[-1]):
        #                                                         continue
        #                                                     else:
        #                                                         if rule.warning:
        #                                                             break
        #                                                         else:
        #                                                             val_deduction += rule.deduction
        #                                                             break
        #                                     elif rule.hour_level == '5':
        #                                         if attendance.repeate_early == rule.repetition:
        #
        #                                             time_from = get_time_from_float(rule.time_from)
        #                                             time_to = get_time_from_float(rule.time_to)
        #                                             if early >= time_from and early <= time_to:
        #                                                 early_rule_exist = True
        #                                                 if rule.id not in fi_l_h_e:
        #                                                     fi_l_h_e.append(rule.id)
        #                                                     if rule.warning:
        #                                                         break
        #                                                     else:
        #                                                         val_deduction += rule.deduction
        #                                                         break
        #                                                 else:
        #                                                     if rule.id != five_hour_early[-1]:
        #                                                         continue
        #                                                     else:
        #                                                         if rule.warning:
        #                                                             break
        #                                                         else:
        #                                                             val_deduction += rule.deduction
        #                                                             break
        #                                 if not early_rule_exist:
        #                                     max_repetition2 = []
        #                                     if hour_levle_early:
        #                                         for rule13 in record.employee_id.attendance_id.rule_deduction_ids.filtered(
        #                                                 lambda r: r.hour_level == str(max(hour_levle_early))):
        #                                             max_repetition2.append(rule13.repetition)
        #                                         print ('ahmed_mokhleffffffffffffffffffff')
        #                                         for rule3 in record.employee_id.attendance_id.rule_deduction_ids.filtered(
        #                                                 lambda r: r.hour_level == str(max(hour_levle_early)) and r.repetition == max(max_repetition2)):
        #                                             time_from = get_time_from_float(rule3.time_from)
        #                                             time_to = get_time_from_float(rule3.time_to)
        #
        #                                             if late >= time_from and attendance.repeate_late >= rule3.repetition:
        #                                                 # if rule3.id not in fi_l_h_l:
        #                                                 #     fi_l_h_l.append(rule3.id)
        #                                                 #     if rule3.warning:
        #                                                 #         break
        #                                                 #     else:
        #                                                 #         val_deduction += rule3.deduction
        #                                                 # else:
        #                                                 #     if rule3.id != int(second_hour_late[-1]):
        #                                                 #         continue
        #                                                 #     else:
        #                                                 if rule3.warning:
        #                                                     continue
        #
        #                                                 else:
        #                                                     val_deduction += rule3.deduction
        #                                                     # break
        #
        #                     if attendance.over_time > 0.0:
        #                         over_time = get_time_from_float(attendance.over_time)
        #                         if record.employee_id.attendance_id.rule_bonus_ids:
        #                             for rule in record.employee_id.attendance_id.rule_bonus_ids:
        #                                 if attendance_datetime.strftime('%A') in weekend_days:
        #                                     if rule.rest_day:
        #                                         over_time_hour = over_time / 60
        #                                         overtime_hour += over_time_hour * rule.bonus_hours
        #                                         break
        #                                 else:
        #                                     time_from = get_time_from_float(rule.time_from)
        #                                     time_to = get_time_from_float(rule.time_to)
        #                                     if time_to >= over_time >= time_from:
        #                                         overtime_hour += rule.bonus_hours
        #                                         break
        #
        #         else:
        #             print ('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        #             if single_date.strftime('%A') not in weekend_days:
        #                 print ('rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr')
        #                 check_date = str(single_date.date())
        #                 holidays = holidays_obj.search(
        #                     [('employee_id', '=', record.employee_id.id), ('state', 'in', ['validate', 'validate1']),
        #                      ('request_date_from', '<=', check_date), ('request_date_to', '>=', check_date)])
        #                 if holidays.filtered(lambda h: not h.holiday_status_id.is_permission):
        #                     print ('zzzxxxxxxxxxxxxxxxxxx')
        #                     pass
        #                 else:
        #                     print ('3333333eeeeeeeeeeeeeeeeeeeeeeeeeeeee')
        #                     if record.employee_id.attendance_id.rule_deduction_ids:
        #                         for rule in record.employee_id.attendance_id.rule_deduction_ids.filtered(
        #                                 lambda r: r.type == 'absent'):
        #                             if rule.id not in absent_rule_take:
        #                                 if rule.absent_repeat == '1':
        #                                     print ('zxmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm')
        #                                     absent_rule_take.append(rule.id)
        #                                     if rule.warning:
        #                                         break
        #                                     else:
        #                                         val_absence += rule.deduction
        #                                         break
        #                                 elif rule.absent_repeat == '2':
        #                                     absent_rule_take.append(rule.id)
        #                                     if rule.warning:
        #                                         break
        #                                     else:
        #                                         val_absence += rule.deduction
        #                                         break
        #                                 elif rule.absent_repeat == '3':
        #                                     absent_rule_take.append(rule.id)
        #                                     if rule.warning:
        #                                         break
        #                                     else:
        #                                         val_absence += rule.deduction
        #                                         break
        #                                 elif rule.absent_repeat == '4':
        #                                     absent_rule_take.append(rule.id)
        #                                     if rule.warning:
        #                                         break
        #                                     else:
        #                                         val_absence += rule.deduction
        #                                         break
        #                                 elif rule.absent_repeat == '5':
        #                                     absent_rule_take.append(rule.id)
        #                                     if rule.warning:
        #                                         break
        #                                     else:
        #                                         val_absence += rule.deduction
        #                                         break
        #                             else:
        #                                 if rule.id != int(absent_rules[-1]):
        #                                     continue
        #                                 else:
        #                                     if rule.warning:
        #                                         break
        #                                     else:
        #                                         val_absence += rule.deduction
        #                                         break
        #
        #     print (val_deduction,'overtime_hourddddddddddddddddddd')
        #     print (hours,'hourddddddddddddddddddd')
        #     rrule = [
        #
        #         {
        #             'name': 'Overtime',
        #             'code': 'Overtime',
        #             'num_of_days': overtime_hour / hours,
        #             'num_of_hours': overtime_hour,
        #             'pay_amount': 0.0,
        #             'rule_id': record.id,
        #         },
        #
        #         {
        #             'name': 'Deduction',
        #             'code': 'Deduction',
        #             'num_of_days': val_deduction / hours,
        #             'num_of_hours': val_deduction,
        #             'pay_amount': 0.0,
        #             'rule_id': record.id,
        #         },
        #         {
        #             'name': 'Absence',
        #             'code': 'Absence',
        #             'num_of_days': val_absence / hours,
        #             'num_of_hours': val_absence,
        #             'pay_amount': 0.0,
        #             'rule_id': record.id,
        #         }
        #     ]
        #
        #     for rr in rrule:
        #         record.write({'attend_rule_ids': [(0, 0, rr)]})
    #@api.one
    @api.depends('attend_rule_ids')
    def _compute_deduction_amount(self):
        for record in self:
            amount = 0.0
            if record.attend_rule_ids:
                for line in record.attend_rule_ids.filtered(lambda r: r.code in ['Deduction']):
                    amount = line.pay_amount
            record.deduction_amount = amount

    #@api.one
    @api.depends('attend_rule_ids')
    def _compute_overtime_amount(self):
        for record in self:
            if record.attend_rule_ids:
                for line in record.attend_rule_ids.filtered(lambda r: r.code == 'Overtime'):
                    if line.num_of_days:
                        record.overtime_amount = line.pay_amount

    #@api.one
    @api.depends('attend_rule_ids')
    def _compute_absent_amount(self):
        for record in self:
            if record.attend_rule_ids:
                for line in record.attend_rule_ids.filtered(lambda r: r.code == 'Absence'):
                    if line.num_of_days:
                        record.absent_amount = line.pay_amount


class HrPayslipEmployees_inherit(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    _description = 'Generate payslips for all selected employees'


    #@api.multi
    # def compute_sheet(self):
        # payslips = self.env['hr.payslip']
        # [data] = self.read()
        # active_id = self.env.context.get('active_id')
        # if active_id:
        #     [run_data] = self.env['hr.payslip.run'].browse(active_id).read(['date_start', 'date_end', 'credit_note'])
        # from_date = run_data.get('date_start')
        # to_date = run_data.get('date_end')
        # if not data['employee_ids']:
        #     raise UserError(_("You must select employee(s) to generate payslip(s)."))
        # for employee in self.env['hr.employee'].browse(data['employee_ids']):
        #     slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
        #     ################################# edit
        #     list = []
        #     contract_id = 0
        #     if employee.contracts_count == 1:
        #         contract_id = self.env['hr.contract'].search([('employee_id', '=', employee.id)]).id
        #     if employee.contracts_count > 1:
        #         for rec in self.env['hr.contract'].search([('employee_id', '=', employee.id)]):
        #             contract_id = rec.id
        #     res = {
        #         'employee_id': employee.id,
        #         'name': slip_data['value'].get('name'),
        #         'struct_id': self.env['hr.contract'].search([('id', '=', contract_id)]).struct_id.id,
        #         # 'contract_id': slip_data['value'].get('contract_id'),
        #         'contract_id': contract_id,
        #         'payslip_run_id': active_id,
        #         'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
        #         'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
        #         'date_from': from_date,
        #         'date_to': to_date,
        #         'credit_note': run_data.get('credit_note'),
        #         'company_id': employee.company_id.id,
        #     }
        #     payslips += self.env['hr.payslip'].create(res)
        # payslips.compute_sheet()
        # payslips.get_attendance_lines()
        # return {'type': 'ir.actions.act_window_close'}
