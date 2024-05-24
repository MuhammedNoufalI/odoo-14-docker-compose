# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, fields, exceptions,_
from odoo.http import request
from odoo.addons.website_form.controllers.main import WebsiteForm
import base64

import werkzeug
import json
# class WebsiteFormInherit(WebsiteForm):
class WebsiteFormInherit(http.Controller):
    @http.route(['/custody/requests'],type='http', auth="public", website=True)
    def portal_requests(self, **kwargs):
        print('/////////////')
        if not request.session.uid:
            return werkzeug.utils.redirect('/web/login', 303)
        my_requests = self.get_my_requests()

        my_requests = my_requests.filtered(lambda x:x.state=='draft')
        return request.render("custody_portal.custodyrequests",{'my_requests':my_requests})

    @http.route(['/custody/request/form'], type='http', method="POST", auth="public", website=True)
    def custofy_request_form(self, **kwargs):
        vals = self.get_default_vals(kwargs)
        return request.render("custody_portal.custody_portal_request_form",vals)

    @http.route(['/my/custody/requests'], type='http', method="POST", auth="public", website=True)
    def my_requests(self, **kwargs):
        if not request.session.uid:
            return werkzeug.utils.redirect('/web/login', 303)
        default_values = {}

        my_requests = self.get_my_requests()

        return request.render("custody_portal.my_custody_requests",
                              {'my_requests': my_requests})

    @http.route(['/custody/request/create'], type='http', method="POST", auth="public", website=True)
    def portal_request_insert(self, **kwargs):
        try:
            custody = request.env['hr.custody'].create({
                                                   'date_request': kwargs.get('date_request'),
                                                   'return_date': kwargs.get('return_date'),
                                                   'purpose': kwargs.get('purpose'),
                                                   'employee': int(kwargs.get('employee')),
                                                   'custody_name':int( kwargs.get('custody_name')),
                                                   # 'name': request.env['ir.sequence'].next_by_code(
                                                   #     'stock.request.order'),
                                                    })

        except Exception as e:
            warn = str(self.prepare_error_msg(e))
            vals = self.get_default_vals(kwargs)
            vals.update({'warn_message':warn})
            return request.render("custody_portal.custody_portal_request_form",vals)
        vals = self.get_default_vals(kwargs)
        vals.update({'pass_message': True,'request_id': custody})
        return request.render("custody_portal.custody_portal_request_form",vals)
        # return request.render("custody_portal.request_created", {'request_id': custody})

    @http.route([
        "/custody/request/<int:request_id>"
    ], type='http', auth="public", website=True)
    def custody_request_view(self, request_id=None, **kw):
        request_id = request.env['hr.custody'].browse(int(request_id))
        return request.render("custody_portal.requests_followup", {'request_id': request_id})


    def prepare_error_msg(self, e):
        msg = ''
        if hasattr(e, 'name'):
            msg += e.name
        elif hasattr(e, 'msg'):
            msg += e.msg
        elif hasattr(e, 'args'):
            msg += e.args[0]
        return msg

    def get_default_vals(self,kwargs):
            default_values={}
            properties = self.get_properties()
            employees = self.get_employees()
            emp = request.env['hr.employee']
            prop = request.env['hr.custody']
            print(kwargs)
            if kwargs != {}:
                default_values['date_request'] = kwargs.get('date_request')
                default_values['return_date'] = kwargs.get('return_date')
                default_values['purpose'] = kwargs.get('purpose')
                employee = employees.browse(int(kwargs.get('employee'))) if kwargs.get('employee') else emp
                property = properties.browse(int(kwargs.get('custody_name'))) if kwargs.get('custody_name') else prop
            else:
                property =  properties[0] if properties else properties
                employee =  employees[0] if employees else employees
                default_values['date_request'] = fields.date.today()
                default_values['return_date'] = ''
                default_values['purpose'] = ''

            return {
                'properties': properties.filtered(lambda x:x != property),
                'property':  property,
                'employees': employees.filtered(lambda x:x != employee),
                'employee': employee,
                'default_values': default_values}
    def get_employees(self):
        return request.env['hr.employee'].sudo().search([('user_id','=',request.env.user.id)])

    def get_my_requests(self):
        return request.env['hr.custody'].sudo().search([('create_uid', '=', request.env.user.id)])
    def get_properties(self):
        return request.env['custody.property'].sudo().search([])

    # def get_my_itrequests(self):
    #     return request.env['it.request'].search([('create_uid', '=', request.env.user.id)])
    #
    # def get_my_asset_requests(self):
    #     return request.env['asset.request'].search([('create_uid', '=', request.env.user.id)])
    #
    # def get_my_mis_requests(self):
    #     return request.env['miscellaneous.request'].search([('create_uid', '=', request.env.user.id)])
    #
    # def get_my_st_requests(self):
    #     return request.env['stationery.request'].search([('create_uid', '=', request.env.user.id)])
    #
    # def prepare_attachment(self, request, model, kwargs):
    #     if kwargs.get('attachment', False):
    #         Attachments = request.env['ir.attachment']
    #         name = kwargs.get('attachment').filename
    #         file = kwargs.get('attachment')
    #         attachment = file.read()
    #         attachment_id = Attachments.sudo().create({
    #             'name': name,
    #             'datas_fname': name,
    #             'res_name': name,
    #             'type': 'binary',
    #             'res_model': model,
    #             'res_id': request.id,
    #             'datas': base64.b64encode(attachment),
    #         })
    #
    # def get_asset_models(self):
    #     return request.env['asset.model'].sudo().search([])
    #
    # def get_product_models(self):
    #     return request.env['product.model'].sudo().search([])
