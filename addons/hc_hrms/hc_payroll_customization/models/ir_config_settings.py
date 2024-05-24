# -*- coding: utf-8 -*-

##############################################################################
#
#    Author: Al Kidhma
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################


#
# class IrConfigInherit(models.TransientModel):
#     _inherit = 'res.config.settings'
#
#     salary_journal_id = fields.Many2one('account.journal', string='Salary Journal')
#
#     def set_values(self):
#         res = super(IrConfigInherit, self).set_values()
#         self.env['ir.config_parameter'].set_param("hc_payroll_customization.salary_journal_id",
#                                                   self.salary_journal_id.id)
#         return res
#
#     def get_values(self):
#         res = super(IrConfigInherit, self).get_values()
#         res.update(
#             salary_journal_id=int(
#                 self.env['ir.config_parameter'].sudo().get_param('hc_payroll_customization.salary_journal_id')),
#         )
#         return res

