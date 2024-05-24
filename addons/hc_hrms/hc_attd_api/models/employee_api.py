# -*- coding: utf-8 -*-

from odoo import models, fields, tools, api, _
from odoo import tools
from odoo.exceptions import ValidationError, UserError
import requests
import json
import base64
import datetime
from PIL import Image


class HcEmployeeSaveApi(models.Model):
    _inherit = 'hr.employee'

    face_scan_image = fields.Binary(string="Image For Attendance Device", store=True,
                                    attachment=True,
                                    help="This JPG File will be Using to link the attendance Devices")
    is_registered = fields.Boolean(string="Is Registered", help="Is the Employee Registered to the Corresponding Device"
                                                                " Which is Mapped to the Branch")
    def api_key_token(self):
        ir_config = self.env['ir.config_parameter'].sudo()
        api_url = ir_config.get_param('hc_attd_api.api_url')
        api_key = ir_config.get_param('hc_attd_api.api_key')
        return {'api_url': api_url,
                'api_key': api_key}

    @api.onchange('image_1920')
    def onchange_image_256(self):
        for rec in self:
            if rec.image_256:
                rec.face_scan_image = rec.image_256

    def save_emp_to_device(self):
        api_cred = self.api_key_token()
        # token = "7ee4e345d834fea:c3abbf46c8714cb"
        token = api_cred['api_key']
        url = api_cred['api_url']
        if not self.employee_id:
            raise UserError(_('Please Update a Employee Code'))
        if not self.name:
            raise UserError(_('Please Update the Name Of the Employee'))
        if not self.face_scan_image:
            raise UserError(_('Please Update the Image to Scan for the Employee'))
        img_upload = self.face_scan_image.decode("utf-8")
        data = {
            "badgeNumber": self.employee_id,
            "Name": self.name,
            "cardNo": self.att_card_number or False,
            "template": img_upload,
        }

        request_url = url + "/api_saveemployee"
        # request_url = "http://95.216.47.175:8082/api_saveemployee"
        headers = {
            'Content-type': 'application/json',
            'token': token,
            # 'Accept': 'application/json'
        }
        req = requests.post(request_url, data=json.dumps(data), headers=headers)
        # if req.content:
        #     val = req.content.decode()
        self.is_registered = True
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': (_("Successfully Registered %s To The Attendance Portal ", self.name)),
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},  # Refresh the form to show the key
            }
        }

    def link_emp_to_device(self):
        api_cred = self.api_key_token()
        token = api_cred['api_key']
        url = api_cred['api_url']
        # token = "7ee4e345d834fea:c3abbf46c8714cb"
        if not self.employee_id:
            raise UserError(_('Please Update a Employee Code'))
        elif not self.name:
            raise UserError(_('Please Update the Name Of the Employee'))
        elif not self.face_scan_image:
            raise UserError(_('Please Update the Image to Scan for the Employee'))
        if not [device_line.device_id for device_line in self.branch_id.attendance_device_ids]:
            raise UserError(
                _('There is no Attendance Device ID Linked for this Branch, Please Add the Attendance ID On the '
                  'Selected Branch of the Employee and Try Again!'))
        linked_dev = 0
        for device_line in self.branch_id.attendance_device_ids:
            linked_dev += 1
            data = {
                "badgeNumber": self.employee_id,
                "DeviceSerialNumber": device_line.device_id
            }
            request_url = url + "/api_addemployeedevice"
            # request_url = "http://95.216.47.175:8082/api_addemployeedevice"

            headers = {
                'Content-type': 'application/json',
                'token': token,
                # 'Accept': 'application/json'
            }
            req = requests.post(request_url, data=json.dumps(data), headers=headers)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': (_("Successfully Linked %s To The Attendance Device ", self.name)),
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},  # Refresh the form to show the key
            }
        }

    def unlink_emp_from_device(self):
        api_cred = self.api_key_token()
        token = api_cred['api_key']
        url = api_cred['api_url']
        # token = "7ee4e345d834fea:c3abbf46c8714cb"
        if not self.employee_id:
            raise UserError(_('Please Update a Employee Code'))
        elif not self.name:
            raise UserError(_('Please Update the Name Of the Employee'))
        elif not self.face_scan_image:
            raise UserError(_('Please Update the Image to Scan for the Employee'))
        if not [device_line.device_id for device_line in self.branch_id.attendance_device_ids]:
            raise UserError(
                _('There is no Attendance Device ID Linked for this Branch, Please Add the Attendance ID and Try Again!'))
        for device_line in self.branch_id.attendance_device_ids:
            data = {
                "badgeNumber": self.employee_id,
                "DeviceSerialNumber": device_line.device_id
            }
            request_url = url + "/api_deleteemployeedevice"
            # request_url = "http://95.216.47.175:8082/api_deleteemployeedevice"
            headers = {
                'Content-type': 'application/json',
                'token': token,
                # 'Accept': 'application/json'
            }
            req = requests.post(request_url, data=json.dumps(data), headers=headers)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': (
                    _("Successfully UnLinked %s From The Attendance Device From the Current Branch", self.name)),
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},  # Refresh the form to show the key
            }
        }
