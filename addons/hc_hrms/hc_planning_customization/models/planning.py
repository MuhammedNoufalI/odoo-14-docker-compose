# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import pandas as pd
from datetime import datetime, timedelta
import pytz
from pytz import timezone, UTC
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
import json


class Planning(models.Model):
    _inherit = "planning.slot"

    branch_id = fields.Many2one("hc.branch", string="Branch")
    hc_contract_id = fields.Many2one("hr.contract", string="Contract")
    resource_calendar_id = fields.Many2one('resource.calendar', string='Working Schedule')
    hc_role_id = fields.Many2one('planning.role', string="Role ", readonly=False,
                                 copy=True, group_expand='_read_group_role_id')
    job_id = fields.Many2one(related='employee_id.job_id', store=True)
    contract_start_date = fields.Datetime(string='Contract Start')
    contract_end_date = fields.Datetime(string='Contract End')
    resource_calendar_id_domain = fields.Char(
        compute="_compute_resource_calendar_id_domain",
        readonly=True,
        store=False,
    )
    date = fields.Date(string="Date Start", compute='_compute_datetime_date', tracking=True)


    def _compute_datetime_date(self):
        for rec in self:
            if rec.date_start:
                rec.date = rec.date_start.date()
    @api.depends('branch_id')
    def _compute_resource_calendar_id_domain(self):
        for rec in self:
            rec.resource_calendar_id_domain = json.dumps(
                [('id', 'in', rec.branch_id.working_schedule_ids.ids)]
            )

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            self.role_id = self.template_id.role_id
            self.branch_id = self.template_id.branch_id
            self.resource_calendar_id = self.template_id.resource_calendar_id

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.role_id = False

    # self.resource_calendar_id = False

    # @api.onchange('branch_id')
    # def _onchange_branch_id(self):
    #     if self.branch_id:
    #         # self.resource_calendar_id = False
    #         return {'domain': {'resource_calendar_id': [('id', 'in', self.branch_id.working_schedule_ids.ids)]}}

    def _inverse_template_creation(self):
        PlanningTemplate = self.env['planning.slot.template']
        for slot in self.filtered(lambda s: s.template_creation):
            values = slot._prepare_template_values()
            domain = [(x, '=', values[x]) for x in values.keys()]
            existing_templates = PlanningTemplate.search(domain, limit=1)
            if not existing_templates:
                if values['role_id']:
                    template = PlanningTemplate.create(values)
                    slot.write({'template_id': template.id, 'previous_template_id': template.id})
            else:
                slot.write({'template_id': existing_templates.id})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'hc_role_id' in vals.keys() and vals['hc_role_id']:
                shift_template = False
                role = self.env['planning.role'].browse(vals['hc_role_id'])
                work_schedule = self.env['resource.calendar'].browse(vals['resource_calendar_id'])
                if 'template_creation' in vals.keys() and vals['template_creation']:
                    shift_template = self.env['planning.slot.template'].create({
                        'role_id': vals['hc_role_id'] if vals['hc_role_id'] else False,
                        'resource_calendar_id': vals['resource_calendar_id'] if vals['resource_calendar_id'] else False,
                        'branch_id': vals['branch_id'] if vals['branch_id'] else False,
                    })
                # start_date_ini =
                old_vals = vals
                if work_schedule:
                    start = vals.get('start_datetime')
                    end = vals.get('end_datetime')
                    local_timezone = pytz.timezone('Asia/Dubai')
                    start_utc_datetime = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
                    start_local_datetime = start_utc_datetime.astimezone(local_timezone)
                    end_utc_datetime = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
                    end_local_datetime = end_utc_datetime.astimezone(local_timezone)
                    end_local_datetime = end_local_datetime.replace(tzinfo=None)
                    start_local_datetime = start_local_datetime.replace(tzinfo=None)
                    # s_date = datetime.strptime(vals.get('start_datetime'), '%Y-%m-%d %H:%M:%S')
                    # e_date = datetime.strptime(vals.get('end_datetime'), '%Y-%m-%d %H:%M:%S')
                    # print("s_date", s_date)
                    # print("e_date", e_date)
                    # start, end = self._calculate_start_end_dates(
                    #     s_date,
                    #     e_date,
                    #     self.env.user.employee_id.resource_id,
                    #     False,
                    #     False,
                    #     False)
                    # print("start22222222222222", start, type(start))
                    # print("end222222222222222", end, type(end))
                    mydates = pd.date_range(start_local_datetime.date(), end_local_datetime.date()).strftime(
                        '%Y-%m-%d').tolist()
                    if role:
                        if 'hc_role_id' in vals.keys():
                            vals.update({
                                'role_id': vals['hc_role_id'],
                            })
                            del vals['hc_role_id']
                        if 'allocated_hours' in vals.keys():
                            del vals['allocated_hours']
                        plan = False
                        for employee in role.employee_ids:
                            emp = employee
                            emp_vals = vals
                            emp_vals['contract_start_date'] = start_local_datetime
                            emp_vals['contract_end_date'] = end_local_datetime

                            # resource = self.env['resource.resource'].search([('employee_id', '=', emp.id)])
                            if employee:
                                emp_vals['employee_id'] = employee.id
                            # else:
                            #     resource = self.env['resource.resource'].create({
                            #         'name': emp.name,
                            #         'employee_id': emp.id,
                            #         'resource_type': 'user',
                            #     })
                            #     emp_vals['resource_id'] = resource.id
                            created_plans = []
                            for day in mydates:
                                flag = False
                                night_shift_flag = False
                                date_time_obj = datetime.strptime(day, '%Y-%m-%d')
                                start_day_time = start_local_datetime
                                end_day_time = end_local_datetime
                                if work_schedule:
                                    hour_from_list = []
                                    hour_to_list = []
                                    for week_day in work_schedule.attendance_ids:
                                        if int(week_day.dayofweek) == date_time_obj.weekday():
                                            if week_day.is_check_out_next_day:
                                                night_shift_flag = True
                                            hour_from_list.append(week_day.hour_from)
                                            hour_to_list.append(week_day.hour_to)
                                    if night_shift_flag:
                                        start_time = min(hour_from_list)
                                        end_time = max(hour_to_list)
                                        start_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(start_time) * 60, 60))
                                        end_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(end_time) * 60, 60))
                                        s_hour = int(start_time.split(":")[0])
                                        s_minute = int(start_time.split(":")[1])
                                        e_hour = int(end_time.split(":")[0])
                                        e_minute = int(end_time.split(":")[1])
                                        start_day_time = date_time_obj + timedelta(hours=s_hour, minutes=s_minute)
                                        end_day_time = date_time_obj + timedelta(days=1, hours=e_hour, minutes=e_minute)
                                        flag = True
                                        if shift_template:
                                            if start_time > end_time:
                                                duration = (end_time + 24.00) - start_time
                                            else:
                                                duration = end_time - start_time
                                            shift_template.update({
                                                'start_time': start_time,
                                                'duration': duration,
                                            })
                                    else:
                                        if hour_from_list and hour_to_list:
                                            start_time = min(hour_from_list)
                                            end_time = max(hour_to_list)
                                            start_time = '{0:02.0f}:{1:02.0f}'.format(
                                                *divmod(float(start_time) * 60, 60))
                                            end_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(end_time) * 60, 60))
                                            s_hour = int(start_time.split(":")[0])
                                            s_minute = int(start_time.split(":")[1])
                                            e_hour = int(end_time.split(":")[0])
                                            e_minute = int(end_time.split(":")[1])
                                            start_day_time = date_time_obj + timedelta(hours=s_hour, minutes=s_minute)
                                            end_day_time = date_time_obj + timedelta(hours=e_hour, minutes=e_minute)
                                            flag = True
                                            if shift_template:
                                                shift_template.update({
                                                    'start_time': start_time,
                                                    'duration': end_time - start_time,
                                                })
                                if flag:
                                    start_dt = start_day_time
                                    end_dt = end_day_time
                                    local = pytz.timezone("Asia/Dubai")
                                    start_dt_loc = local.localize(start_dt, is_dst=None)
                                    start_dt_utc_dt = start_dt_loc.astimezone(pytz.utc)
                                    start_date = start_dt_utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                                    end_dt_loc = local.localize(end_dt, is_dst=None)
                                    end_dt_utc_dt = end_dt_loc.astimezone(pytz.utc)
                                    end_date = end_dt_utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                                    emp_vals['start_datetime'] = start_date
                                    emp_vals['end_datetime'] = end_date
                                    previous_shift = self.env['planning.slot'].search(
                                        [('employee_id', '=', emp.id), ('start_datetime', '=', start_date),
                                         ('end_datetime', '=', end_date)])
                                    if previous_shift:
                                        # raise ValidationError(_('You are not allowed to create two shifts for an employee at same time'))
                                        continue
                                    plan = self.create(emp_vals)
                                    if plan:
                                        created_plans.append(plan)
                            # if plan:
                            #     print("plan", plan)
                            #     previous_contract = False
                            #     new_contract = False
                            #     previous_contract_between = False
                            #     future_contract = False
                            #     contracts = self.env['hr.contract'].search(
                            #         [('employee_id', '=', emp.id), ('state', '!=', 'cancel')])
                            #     print("contracts", contracts)
                            #     for contract in contracts:
                            #         if start_local_datetime.date() >= contract.date_start:
                            #             previous_contract = contract
                            #             if contract.date_end:
                            #                 if end_local_datetime.date() <= contract.date_end:
                            #                     previous_contract_between = contract
                            #         if not previous_contract_between:
                            #             if contract.date_end:
                            #                 if contract.date_end >= end_local_datetime.date():
                            #                     future_contract = contract
                            #     print("previous_contract", previous_contract)
                            #     print("future_contract", future_contract)
                            #     if previous_contract:
                            #         if previous_contract_between:
                            #             print("if previous_contract_between:")
                            #             new_contract = previous_contract_between.with_context(
                            #                 skip_contract_closing=True).copy()
                            #             print("new_contract", new_contract)
                            #             new_contract_2 = False
                            #             if end_local_datetime.date() < previous_contract_between.date_end:
                            #                 new_contract_2 = previous_contract_between.with_context(
                            #                     skip_contract_closing=True).copy()
                            #             previous_contract_between.update({
                            #                 'date_end': start_local_datetime.date() - relativedelta(days=1),
                            #             })
                            #             rule_list = []
                            #             for rule in previous_contract_between.salary_rule_ids:
                            #                 copy_rule = rule.copy()
                            #                 rule_list.append(copy_rule.id)
                            #             new_contract.update({
                            #                 'name': emp.oe_emp_sequence + '/00' + str(emp.no_of_contracts),
                            #                 'date_end': end_local_datetime.date(),
                            #                 'date_start': start_local_datetime.date(),
                            #                 'resource_calendar_id': vals['resource_calendar_id'],
                            #                 'salary_rule_ids': rule_list,
                            #                 'kanban_state': 'done'
                            #             })
                            #
                            #             # if new_contract:
                            #             #     for new_rule in  new_contract.salary_rule_ids:
                            #             #         for old_rule in new_contract.salary_rule_ids:
                            #
                            #             if new_contract_2:
                            #                 rule_list = []
                            #                 for rule in previous_contract_between.salary_rule_ids:
                            #                     copy_rule = rule.copy()
                            #                     rule_list.append(copy_rule.id)
                            #                 new_contract_2.update({
                            #                     'name': emp.oe_emp_sequence + '/00' + str(emp.no_of_contracts),
                            #                     'date_start': end_local_datetime.date() + relativedelta(days=1),
                            #                     'resource_calendar_id': previous_contract_between.resource_calendar_id.id,
                            #                     'salary_rule_ids': rule_list,
                            #                     'kanban_state': 'done'
                            #                 })
                            #         else:
                            #             print("eleeeeeeeeeeeeeeeeee")
                            #             new_contract = previous_contract.with_context(
                            #                 skip_contract_closing=True).copy()
                            #             previous_contract.update({
                            #                 'date_end': start_local_datetime.date() - relativedelta(days=1),
                            #             })
                            #             rule_list = []
                            #             for rule in previous_contract.salary_rule_ids:
                            #                 copy_rule = rule.copy()
                            #                 rule_list.append(copy_rule.id)
                            #             new_contract.update({
                            #                 'name': emp.oe_emp_sequence + '/00' + str(emp.no_of_contracts),
                            #                 'date_end': end_local_datetime.date(),
                            #                 'date_start': start_local_datetime.date(),
                            #                 'resource_calendar_id': vals['resource_calendar_id'],
                            #                 'salary_rule_ids': rule_list,
                            #                 'kanban_state': 'done'
                            #             })
                            #     if future_contract:
                            #         if future_contract.date_end == end_local_datetime.date():
                            #             future_contract.update({
                            #                 'state': 'cancel',
                            #             })
                            #         else:
                            #             future_contract.update({
                            #                 'date_start': end_local_datetime.date() + relativedelta(days=1),
                            #             })
                            #
                            #     if not new_contract:
                            #         print("if not new_contract:")
                            #         new_contract = self.env['hr.contract'].with_context(
                            #             skip_contract_closing=True).create({
                            #             'name': emp.oe_emp_sequence + '/00' + str(emp.no_of_contracts),
                            #             'employee_id': emp.id,
                            #             'date_start': start_local_datetime.date(),
                            #             'wage': 0,
                            #             'resource_calendar_id': vals['resource_calendar_id'],
                            #             'kanban_state': 'done'
                            #         })
                            #     if new_contract:
                            #         if created_plans:
                            #             for plan in created_plans:
                            #                 plan.write({
                            #                     'hc_contract_id': new_contract.id
                            #                 })

                        vals = {}
                        if plan:
                            result = plan
                        else:
                            result = True
                else:
                    result = super(Planning, self).create(vals)
            else:
                if 'role_id' in vals.keys() and vals['role_id']:
                    result = super(Planning, self).create(vals)
                else:
                    raise UserError(
                        _("You are not allowed to create slots without a role"))

        return result

    def unlink(self):
        for rec in self:
            user = self.env.user
            if not user.has_group('hc_planning_customization.high_management_user'):
                raise UserError(
                    _("You are not allowed to delete this record,Only High Management users can delete this record"))
            contract = False
            if rec.hc_contract_id:
                contract = self.env['hr.contract'].browse(rec.hc_contract_id.id)
                if contract and contract.state == 'draft':
                    contract.unlink()
        res = super(Planning, self).unlink()
        return res

    def write(self, values):
        for record in self:
            if record.is_published:
                if 'start_datetime' in values or 'end_datetime' in values or 'branch_id' in values or 'resource_calendar_id' in values or 'resource_id' in values:
                    raise ValidationError(_('You are not allowed to edit the published shifts'))
            if 'start_datetime' in values or 'end_datetime' in values:
                if 'start_datetime' in values:
                    start_dt = datetime.strptime(values['start_datetime'], '%Y-%m-%d %H:%M:%S')
                else:
                    start_dt = record.start_datetime
                if 'end_datetime' in values:
                    end_dt = datetime.strptime(values['end_datetime'], '%Y-%m-%d %H:%M:%S')
                else:
                    end_dt = record.end_datetime
                shift_start_time = start_dt.strftime("%H.%M")
                shift_end_time = end_dt.strftime("%H.%M")
                start_time = shift_start_time
                end_time = shift_end_time
                s_hour = int(start_time.split(".")[0])
                s_minute = int(start_time.split(".")[1]) / 60
                e_hour = int(end_time.split(".")[0])
                e_minute = int(end_time.split(".")[1]) / 60
                shift_start_time = str(s_hour + s_minute)
                shift_end_time = str(e_hour + e_minute)
                if record.resource_calendar_id:
                    new_work_schedule = record.resource_calendar_id.copy()
                    hour_from_list = {}
                    hour_to_list = {}
                    for week_day in new_work_schedule.attendance_ids:
                        if int(week_day.dayofweek) == start_dt.weekday():
                            # if week_day.is_check_out_next_day:
                            #     night_shift_flag = True
                            hour_from_list[week_day.id] = week_day.hour_from
                            hour_to_list[week_day.id] = week_day.hour_to
                            # hour_to_list.append(week_day.hour_to)
                    min_start_time = min(hour_from_list.values())
                    min_end_time = max(hour_to_list.values())
                    for rec in hour_from_list.keys():
                        if hour_from_list[rec] == min_start_time:
                            start_record_id = rec
                    for rec in hour_to_list.keys():
                        if hour_to_list[rec] == min_end_time:
                            end_record_id = rec
                    for week_day in new_work_schedule.attendance_ids:
                        if week_day.id == start_record_id:
                            week_day.hour_from = float(shift_start_time) + 4
                        if week_day.id == end_record_id:
                            week_day.hour_to = float(shift_end_time) + 4
                    new_work_schedule_name = new_work_schedule.name
                    sub_list = ["(copy)"]
                    for sub in sub_list:
                        new_work_schedule_name = new_work_schedule_name.replace(sub, ' ')
                    if "Modified" in new_work_schedule_name:
                        new_work_schedule_name = new_work_schedule_name[:-7]
                        # ffff
                        new_work_schedule.write({
                            'name': new_work_schedule_name + self.env['ir.sequence'].next_by_code(
                                'resource.calendar.sequence')
                        })
                    else:
                        new_work_schedule.write({
                            'name': new_work_schedule_name + '- Modified' + '-' + self.env['ir.sequence'].next_by_code(
                                'resource.calendar.sequence')
                        })
                    record.resource_calendar_id = new_work_schedule
                    # start_time = min(hour_from_list)
                    # end_time = max(hour_to_list)
                # local = pytz.timezone("Asia/Dubai")
                # start_dt_loc = local.localize(start_dt, is_dst=None)
                # start_dt_utc_dt = start_dt_loc.astimezone(pytz.utc)
                # start_date = start_dt_utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                # end_dt_loc = local.localize(end_dt, is_dst=None)
                # end_dt_utc_dt = end_dt_loc.astimezone(pytz.utc)
                # end_date = end_dt_utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                # print("............start_date", start_date, type(start_date))
                # print("............end_date", end_date, type(end_date))
        result = super(Planning, self).write(values)
        return result

    def action_send(self):
        res = super(Planning, self).action_send()
        # self.action_update_contract()

        return res

    def action_publish(self):
        res = super(Planning, self).action_publish()
        # self.action_update_contract()
        return res

    def action_update_contract(self):
        slot_list = []
        for rec in self:
            slot_list.append(rec)
        for rec in slot_list:
            if not rec.employee_id:
                raise ValidationError(_('You are not allowed to publish the open shifts'))
            if rec.employee_id:
                contracts = self.env['hr.contract'].search(
                    [('employee_id', '=', rec.employee_id.id)])
                current_contract = False
                for contract in contracts:
                    if contract.date_end:
                        condition = contract.date_start <= rec.start_datetime.date() <= contract.date_end
                    else:
                        condition = ((contract.date_start <= rec.start_datetime.date()) and not contract.date_end)
                    if condition:
                        current_contract = contract
                if current_contract:
                    if rec.resource_calendar_id:
                        if rec.resource_calendar_id.id != current_contract.resource_calendar_id.id:
                            new_contract = current_contract.with_context(skip_contract_closing=True).copy()
                            if current_contract.date_start == rec.start_datetime.date():
                                current_contract.update({
                                    'date_start': rec.start_datetime + relativedelta(days=1),
                                })
                                rule_list = []
                                for rule in current_contract.salary_rule_ids:
                                    copy_rule = rule.copy()
                                    rule_list.append(copy_rule.id)
                                new_contract.update({
                                    'name': rec.employee_id.oe_emp_sequence + '/00' + str(
                                        rec.employee_id.no_of_contracts),
                                    'date_start': rec.start_datetime.date(),
                                    'date_end': rec.end_datetime.date(),
                                    'resource_calendar_id': rec.resource_calendar_id.id,
                                    'salary_rule_ids': rule_list,
                                    'kanban_state': 'done'
                                })
                            else:
                                current_contract.update({
                                    'date_end': rec.start_datetime - relativedelta(days=1),
                                })
                                rule_list = []
                                for rule in current_contract.salary_rule_ids:
                                    copy_rule = rule.copy()
                                    rule_list.append(copy_rule.id)
                                new_contract.update({
                                    'name': rec.employee_id.oe_emp_sequence + '/00' + str(
                                        rec.employee_id.no_of_contracts),
                                    'date_start': rec.start_datetime.date(),
                                    'date_end': rec.contract_end_date.date(),
                                    'resource_calendar_id': rec.resource_calendar_id.id,
                                    'salary_rule_ids': rule_list,
                                    'kanban_state': 'done'
                                })
                            if new_contract:
                                rec.write({
                                    'hc_contract_id': new_contract.id
                                })
        return True


class PlanningPlanning(models.Model):
    _inherit = "planning.planning"


    def _send_planning(self, message=None, employees=False):
        email_from = self.env.user.email or self.env.user.company_id.email or ''
        sent_slots = self.env['planning.slot']
        for planning in self:
            # prepare planning urls, recipient employees, ...
            slots = planning.slot_ids
            slots_open = slots.filtered(lambda slot: not slot.employee_id) if planning.include_unassigned else 0

            # extract planning URLs
            employees = employees or slots.mapped('employee_id')
            employee_url_map = employees.sudo()._planning_get_url(planning)

            # send planning email template with custom domain per employee
            template = self.env.ref('planning.email_template_planning_planning', raise_if_not_found=False)
            template_context = {
                'slot_unassigned_count': slots_open and len(slots_open),
                'slot_total_count': slots and len(slots),
                'message': message,
            }
            if template:
                # /!\ For security reason, we only given the public employee to render mail template
                for employee in self.env['hr.employee.public'].browse(employees.ids):
                    if employee.work_email:
                        template_context['employee'] = employee
                        destination_tz = pytz.timezone(self.env.user.tz or 'UTC')
                        template_context['start_datetime'] = pytz.utc.localize(planning.start_datetime).astimezone(destination_tz).replace(tzinfo=None)
                        template_context['end_datetime'] = pytz.utc.localize(planning.end_datetime).astimezone(destination_tz).replace(tzinfo=None)
                        template_context['planning_url'] = employee_url_map[employee.id]
                        template_context['assigned_new_shift'] = bool(slots.filtered(lambda slot: slot.employee_id.id == employee.id))
                        template.with_context(**template_context).send_mail(planning.id, email_values={'email_to': employee.work_email, 'email_from': email_from}, notif_layout='mail.mail_notification_light')
            sent_slots |= slots
        # mark as sent
        sent_slots.write({
            'is_published': True,
            'publication_warning': False
        })
        # if sent_slots:
        #     for slot in sent_slots:
        #         slot.action_update_contract()
        return True
