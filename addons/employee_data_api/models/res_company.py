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
    device_serial_number = fields.Char(string="Device Serial Number")
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
        val = {
            'company_name': attendance['CompanyName'],
            'badge_number': attendance['BadgeNumber'],
            'punch_date_time': self.convert_zkdate_toodoo(attendance['PunchDateTime']),
            'punch_type': attendance['PunchType'],
            'device_Id': attendance['DeviceId'],
        }
        return val

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
                self._create_raw_attendance(punches_parsed_data.get('punches'), vals)
                return True
            else:
                _logger.warning("Error : {}, Please contact your system administrator.".format(punches_vals))
                return False
            return True
        else:
            _logger.warning("Exception : {}, Please contact your system administrator.".format(punches_vals))
            return False

    def _create_raw_attendance(self, punches_by_user, vals):
        RawAttendance = self.env['hc.raw.attendance']
        hr_employee = self.env['hr.employee']
        res_company = self.env['res.company']
        # all_punches = list(filter(lambda x: x['BadgeNumber'] in hr_employee.search(
        #     [('company_id', '=', self.id)]).mapped('oe_emp_sequence'), punches_by_user))
        for punch in punches_by_user:
            punched_time = self.convert_zkdate_toodoo(punch['PunchDateTime'])
            employee_id = hr_employee.sudo().search([('oe_emp_sequence', '=', punch['BadgeNumber'])], limit=1)
            company_id = res_company.search([('device_serial_number', '=', punch['DeviceId'])], limit=1)
            duplicate_punch = RawAttendance.search(
                [('badge_number', '=', punch['BadgeNumber']), ('punched_time', '=', punched_time - timedelta(hours=4),)])
            if duplicate_punch:
                continue
            RawAttendance.create({
                'employee_id': employee_id.id if employee_id else False,
                'company_name': company_id.name if company_id.device_serial_number else 'NA',
                'badge_number': punch['BadgeNumber'],
                'punched_time': punched_time - timedelta(hours=4),
                'punch_type': punch['PunchType'],
                'device_Id': punch['DeviceId'],
            })