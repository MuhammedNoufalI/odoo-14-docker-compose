# -*- coding: utf-8 -*-

import json

from datetime import datetime, timedelta
import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class InheritHrAttendance(models.Model):
    _inherit = 'hr.attendance'

    login_device_id = fields.Char("Login Device Id")
    logout_device_id = fields.Char("Logout Device Id")
    login_location = fields.Char("Login Location")
    logout_location = fields.Char("Logout Location")


class ResCompany(models.Model):
    _inherit = "res.company"

    zk_teco_device = fields.Boolean(string='ZK_Teco Device', readonly=1)
    zk_username = fields.Char(string="Username")
    zk_password = fields.Char(string="Password")
    zk_authorization_url = fields.Char(
        string="Authorization URL", default="http://myrra.lenvica.com/AttendHRM_MIS/dll/mis.dll/login/admin"
    )
    zk_id_token = fields.Char(string="id_token", readonly=1)
    zk_token_last_modified = fields.Datetime(string="id_token Last Modified At", readonly=1)
    zk_teco_url = fields.Char(
        string="AttendHRM_MIS", default="http://myrra.lenvica.com/AttendHRM_MIS/dll/mis.dll/zk_teco/get_punch_data"
    )

    def convert_zkdate_toodoo(self, zk_date):
        odoo_datetime = datetime.strptime(zk_date, '%d-%m-%Y %H:%M:%S')
        return odoo_datetime

    def zk_headers(self, token=False):
        headers = {}
        headers['Content-Type'] = 'application/json'
        if token:
            headers['id_token'] = self.zk_id_token
        return headers

    def zk_teco_get_token(self):
        if not self.zk_username:
            raise UserError(_('"Username" is not defined.'))
        elif not self.zk_password:
            raise UserError(_('"Password" is not defined.'))
        elif not self.zk_authorization_url:
            raise UserError(_('"Authorization URL" is not defined.'))

        headers = self.zk_headers()
        token_data = requests.request(
            'GET', self.zk_authorization_url + '?uname={}&password={}'.format(self.zk_username, self.zk_password),
            headers=headers
        )
        if token_data.status_code == 200:
            token_parsed_data = json.loads(str(token_data.text))
            if 'result' in token_parsed_data and token_parsed_data['result'] != 'success':
                raise UserError(_("Error : {}, Please contact your system administrator.".format(token_parsed_data)))
            self.update({
                'zk_id_token': token_parsed_data['id_token'],
                'zk_token_last_modified': fields.Datetime.now(),
                'zk_teco_device': True
            })
        else:
            raise UserError(_("Exception : {}, Please contact your system administrator.".format(token_data)))

    def open_info_message(self, message):
        view = self.env.ref("sh_message.sh_message_wizard")
        context = dict(self._context or {})
        context['message'] = message
        return {
            'name': 'Info',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.message.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': "new",
            'context': context
        }

    def zk_teco_test(self):
        if not self.zk_id_token:
            self.zk_teco_get_token()

        if not self.zk_teco_url:
            raise UserError(_('"AttendHRM_MIS" is not defined.'))

        headers = self.zk_headers(True)
        punches_vals = requests.request('GET', self.zk_teco_url, headers=headers)
        if punches_vals.status_code == 200:
            attendance_parsed_data = json.loads(str(punches_vals.text))
            if attendance_parsed_data.get('punches'):
                return self.open_info_message("Connection successful.")
            else:
                raise UserError(
                    _("Error : {}, Please contact your system administrator.".format(punches_vals)))
        else:
            raise UserError(_("Exception : {}, Please contact your system administrator.".format(punches_vals)))

    def _get_zk_punch_line_val(self, attendance):
        return {
            'company_name': attendance['CompanyName'],
            'badge_number': attendance['BadgeNumber'],
            'punch_date_time': self.convert_zkdate_toodoo(attendance['PunchDateTime']),
            'punch_type': attendance['PunchType'],
            'device_Id': attendance['DeviceId'],
        }


    def _create_zk_attendance(self, emp, attendance):
        hr_attendance = self.env['hr.attendance']
        date_obj = self.convert_zkdate_toodoo(attendance['PunchDateTime'])
        zk_punch_line_val = self._get_zk_punch_line_val(attendance)
        vals = {
            'employee_id': emp.id,
            'zk_punch_line': [(0, 0, zk_punch_line_val)],
        }
        if attendance['PunchType'] == 0:
            vals.update({
                'check_in': date_obj
            })
            attendance_id = hr_attendance.create(vals)
            return attendance_id

    def _write_zk_attendance(self, attendance_id, attendance):
        zk_punch_line = self.env['zk.punch.line']
        date_obj = self.convert_zkdate_toodoo(attendance['PunchDateTime'])
        zk_punch_line_id = zk_punch_line.search([
            ('attendance_id', '=', attendance_id.id),
            ('punch_date_time', '=', date_obj), ('punch_type', '=', attendance['PunchType'])
        ])
        if zk_punch_line_id:
            return zk_punch_line_id
        zk_punch_line_val = self._get_zk_punch_line_val(attendance)
        zk_punch_line_val['attendance_id'] = attendance_id.id
        zk_punch_line_id = zk_punch_line.create(zk_punch_line_val)
        return zk_punch_line_id

    def _punch(self, emp, attendance):
        hr_attendance = self.env['hr.attendance']
        date_obj = self.convert_zkdate_toodoo(attendance['PunchDateTime'])
        date_from = date_obj.strftime('%Y-%m-%d 00:00:00')
        date_to = date_obj.strftime('%Y-%m-%d 23:59:59')
        if attendance['PunchType'] == 0:
            attendance_id = hr_attendance.search([('employee_id', '=', emp.id), ('check_in', '=', date_obj)], limit=1)
            if attendance_id:
                return True
            attendance_id = hr_attendance.search([
                ('employee_id', '=', emp.id),
                ('check_in', '>=', date_from),
                ('check_in', '<=', date_to)
            ], limit=1)
            if attendance_id and attendance_id.check_in <= date_obj <= attendance_id.zk_check_in_end_datetime:
                self._write_zk_attendance(attendance_id, attendance)
                return True
            elif attendance_id and attendance_id.check_in > date_obj or \
                    attendance_id and attendance_id.zk_check_in_end_datetime < date_obj:
                # Punch is not in 24 hours duration from first punch.
                return True
            self._create_zk_attendance(emp, attendance)
        elif attendance['PunchType'] == 1:
            attendance_id = hr_attendance.search([('employee_id', '=', emp.id), ('check_out', '=', date_obj)], limit=1)
            if attendance_id:
                return True

            attendance_id = hr_attendance.search([
                ('employee_id', '=', emp.id),
                ('check_in', '>=', date_from),
                ('check_in', '<=', date_to),
            ], limit=1)
            if attendance_id and attendance_id.check_in <= date_obj <= attendance_id.zk_check_in_end_datetime:
                zk_punch_line_id = self._write_zk_attendance(attendance_id, attendance)
                if not attendance_id.check_out:
                    attendance_id.update({'check_out': zk_punch_line_id.punch_date_time})
                    return True
                elif attendance_id.check_out < zk_punch_line_id.punch_date_time:
                    attendance_id.update({'check_out': zk_punch_line_id.punch_date_time})
                    return True
            elif attendance_id and attendance_id.check_in > date_obj or \
                    attendance_id and attendance_id.zk_check_in_end_datetime < date_obj:
                # Punch is not in 24 hours duration from first punch.
                return True

    def _update_attendances(self, punches_by_user, vals=None):
        hr_attendance = self.env['hr.attendance']
        # if not vals:
        #     today = fields.Date.today()
        #     all_attendance = hr_attendance.search([('check_in', '>=', today), ('check_out', '<=', today)])
        #     all_attendance.unlink()
        #     self.env.cr.commit()
        # elif vals['filter_by'] == 'single_date':
        #     all_attendance = hr_attendance.search([
        #         ('check_in', '>=', vals['from_date']), ('check_out', '<=', vals['from_date'])])
        #     all_attendance.unlink()
        #     self.env.cr.commit()
        # elif vals['filter_by'] == 'date_range':
        #     all_attendance = hr_attendance.search([
        #         ('check_in', '>=', vals['from_date']), ('check_out', '<=', vals['to_date'])])
        #     all_attendance.unlink()
        #     self.env.cr.commit
        # elif vals['filter_by'] == 'time_range':
        #     zk_from_datetime = vals['from_datetime'].strftime('%d/%m/%Y %H:%M:%S')
        #     zk_to_datetime = vals['to_datetime'].strftime('%d/%m/%Y %H:%M:%S')
        #     endpoint += '?from_date={}&to_date={}'.format(zk_from_datetime, zk_to_datetime)

        hr_employee = self.env['hr.employee']
        # get only all check in's
        all_check_in = list(filter(lambda d: d['PunchType'] == 0 and d['BadgeNumber'] in hr_employee.search(
            [('company_id', '=', self.id)]).mapped('oe_emp_sequence'), punches_by_user))

        # check that already created in odoo
        already_done_check_ins = list(filter(lambda d: self.env['hr.attendance'].search(
            [('employee_id.oe_emp_sequence', '=', d['BadgeNumber']),
             ('check_in', '=', self.convert_zkdate_toodoo(d['PunchDateTime']))]), all_check_in))

        # remove the already done from the check in's
        check_in = [dic for dic in all_check_in if dic not in already_done_check_ins]

        # get only all check out's
        all_check_out = list(filter(lambda d: d['PunchType'] == 1 and d['BadgeNumber'] in hr_employee.search(
            [('company_id', '=', self.id)]).mapped('oe_emp_sequence'), punches_by_user))

        # get already done check out's
        already_done_check_outs = list(filter(lambda d: self.env['hr.attendance'].search(
            [('employee_id.oe_emp_sequence', '=', d['BadgeNumber']),
             ('check_out', '=', self.convert_zkdate_toodoo(d['PunchDateTime']))]), all_check_out))

        # remove the already done checkout from the checkouts
        check_out = [dic for dic in all_check_out if dic not in already_done_check_outs]

        for punch_in in check_in:
            employee_id = hr_employee.search([
                ('oe_emp_sequence', '=', punch_in['BadgeNumber']), ('company_id', '=', self.id)
            ], limit=1)
            try:
                if employee_id:
                    in_date = self.convert_zkdate_toodoo(punch_in.get('PunchDateTime'))
                    add_24_hrs_to_c_in = in_date + timedelta(hours=24)
                    related_check_outs = list(filter(lambda d: d['BadgeNumber'] == employee_id.oe_emp_sequence and (
                            str(in_date.strftime('%d-%m-%Y %H:%M:%S')) < d['PunchDateTime']
                            < str(add_24_hrs_to_c_in.strftime('%d-%m-%Y %H:%M:%S'))), check_out))
                    if related_check_outs:
                        if len(related_check_outs) > 1:
                            max_checkout = max(related_check_outs,
                                               key=lambda x: datetime.strptime(x['PunchDateTime'], '%d-%m-%Y %H:%M:%S'))
                            check_out = [dic for dic in check_out if dic not in related_check_outs]
                            self.create_attendance(punch_in, max_checkout, employee_id, in_date)
                        else:
                            max_checkout = related_check_outs[0]
                            check_out = [dic for dic in check_out if dic not in related_check_outs]
                            self.create_attendance(punch_in, max_checkout, employee_id, in_date)
            except Exception as e:
                print(e)
                continue

        # for punch in punches_by_user:
        #     employee_id = hr_employee.search([
        #         ('oe_emp_sequence', '=', punch['BadgeNumber']), ('company_id', '=', self.id)
        #     ], limit=1)
        #     if employee_id:
        #         self._punch(employee_id, punch)

    def create_attendance(self, punch_in=None, max_checkout=None, employee_id=None, in_date=None):
        self.env['hr.attendance'].create({
            'employee_id': employee_id.id,
            'check_in': in_date,
            'check_out': self.convert_zkdate_toodoo(max_checkout.get('PunchDateTime')),
            'login_device_id': punch_in.get('DeviceId'),
            'logout_device_id': max_checkout.get('DeviceId'),
            'login_location': punch_in.get('CompanyName'),
            'logout_location': max_checkout.get('CompanyName'),
        })

    def update_employee_attendances(self):
        companies = self.env['res.company'].search([('zk_teco_device', '=', True)])
        for company in companies:
            if not company.zk_id_token:
                _logger.warning("'id_token' for the '{}' company is not configured.".format(company.name))
                continue
            elif not company.zk_teco_url:
                _logger.warning("'AttendHRM_MIS' for the '{}' company is not configured.".format(company.name))
                continue
            company.import_zk_teco_attendances()

    def import_zk_teco_attendances(self, vals=False):
        endpoint = self.zk_teco_url
        if not vals:
            today = fields.Date.today()
            endpoint += '?from_date={}'.format(today.strftime('%d/%m/%Y'))
        elif vals['filter_by'] == 'single_date':
            zk_from_date = vals['from_date'].strftime('%d/%m/%Y')
            endpoint += '?from_date={}'.format(zk_from_date)
        elif vals['filter_by'] == 'date_range':
            zk_from_date = vals['from_date'].strftime('%d/%m/%Y')
            zk_to_date = vals['to_date'].strftime('%d/%m/%Y')
            endpoint += '?from_date={}&to_date={}'.format(zk_from_date, zk_to_date)
        elif vals['filter_by'] == 'time_range':
            zk_from_datetime = vals['from_datetime'].strftime('%d/%m/%Y %H:%M:%S')
            zk_to_datetime = vals['to_datetime'].strftime('%d/%m/%Y %H:%M:%S')
            endpoint += '?from_date={}&to_date={}'.format(zk_from_datetime, zk_to_datetime)

        result = self._get_zk_teco_data(endpoint, vals)
        if result:
            _logger.info("ZK_Teco attendance data import successfully for the {} company.".format(self.name))
        else:
            _logger.warning("Something went wrong during the ZK_Teco "
                            "attendance data import for the {} company.".format(self.name))

    def _get_zk_teco_data(self, endpoint, vals=None):
        _logger.info("AttendHRM_MIS endpoint: {}".format(endpoint))
        headers = self.zk_headers(True)
        punches_vals = requests.request('GET', endpoint, headers=headers)
        if punches_vals.status_code == 200:
            punches_parsed_data = json.loads(str(punches_vals.text))
            if punches_parsed_data.get('punches'):
                self._update_attendances(punches_parsed_data.get('punches'), vals)
                return True
            else:
                _logger.warning("Error : {}, Please contact your system administrator.".format(punches_vals))
                return False
            return True
        else:
            _logger.warning("Exception : {}, Please contact your system administrator.".format(punches_vals))
            return False