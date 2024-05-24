 # -*- coding: utf-8 -*-


from odoo.tools import float_compare
# from odoo.exceptions import UserError
import odoo
import werkzeug
import werkzeug.exceptions
from odoo import http,exceptions,_
from odoo.http import request
class LeaveForm(http.Controller):
    #mention class name
    @http.route(['/leave/form'], type='http', auth="public", website=True)
    #mention a url for redirection.
    #define the type of controller which in this case is ‘http’.
    #mention the authentication to be either public or user.
    def leave_form(self, **post):
        #create method
        #this will load the form webpage
        # my_user = request.env['res.users'].search([('id', '=', request.env.user.id)])
        # if my_user:
        #     my_user.sel_groups_1_9_10 = '1'
        # print (my_user.sel_groups_1_9_10)
        employye_leaves = request.env['hr.leave'].search([('employee_id.user_id','=',request.env.user.id)])
        employee_recs = request.env['hr.employee'].search([('user_id','=',request.env.user.id)])
        holiday_status_recs = request.env['hr.leave.type'].search([])
        holi = holiday_status_recs[0] if holiday_status_recs else holiday_status_recs
        holiday_status_recs = holiday_status_recs.filtered(lambda x:x != holi)
        return request.render("website_test.tmp_leave_form", {'employee_recs':employee_recs,'holiday_status_recs':holiday_status_recs,
                                                              'employye_leaves':employye_leaves,
                                                              'date_from': False,
                                                              'date_to': False,
                                                              'name': False, 'holi': holi
                                                              })

    @http.route(['/leave/form/submit'], type='http', auth="public", website=True)
    #next controller with url for submitting data from the form#
    def leave_form_submit(self, **post):
        try:
            print ('data_recieved' , post)

            date_start = str(post['request_date_from'])+ str(' 06:00:00')
            date_end = str(post['request_date_to'])+ str(' 15:00:00')
            leave_request = request.env['hr.leave'].sudo().create({
                'name': post.get('name'),
                'employee_id': int(post.get('employee_id')),
                'date_from': date_start,
                'date_to': date_end,
                'holiday_status_id': int(post.get('holiday_status_id')),
                'request_date_from': post.get('request_date_from'),
                'request_date_to': post.get('request_date_to'),
                'department_id': request.env['hr.employee'].browse(int(post.get('employee_id'))).department_id.id
            })


            # leave_request.sudo()._onchange_request_parameters()
            leave_request.sudo()._onchange_leave_dates()

            # leave_request = request.env['hr.leave'].sudo().create(post)

            vals = {
                'leave_request': leave_request,
            }
            #inherited the model to pass the values to the model from the form#
            return request.render("website_test.tmp_leave_form_success", vals)
            #finally send a request to render the thank you page#
        except Exception as e:
            err = str(self.prepare_error_msg(e))
            employye_leaves = request.env['hr.leave'].search([('employee_id.user_id', '=', request.env.user.id)])
            employee_recs = request.env['hr.employee'].search([('user_id', '=', request.env.user.id)])
            holiday_status_recs = request.env['hr.leave.type'].search([])
            holi = holiday_status_recs.browse(int(post.get('holiday_status_id')))
            holiday_status_recs = holiday_status_recs.filtered(lambda x: x != holi)

            return request.render("website_test.tmp_leave_form",
                                  {'employee_recs':employee_recs,'holiday_status_recs':holiday_status_recs,'employye_leaves':employye_leaves,'date_from':post.get('request_date_from'),'date_to':post.get('request_date_to'),'name':post.get('name'),'holi':holi,'warn_message':err})


    def prepare_error_msg(self, e):
        msg = ''
        if hasattr(e, 'name'):
            msg += e.name
        elif hasattr(e, 'msg'):
            msg += e.msg
        elif hasattr(e, 'args'):
            msg += e.args[0]
        print('>>>>>',msg)
        return msg

