import logging
from odoo import models,api,tools
import re


class report_certificate(models.AbstractModel):
    _name = 'report.hc_certificate.report_certificate'
    _description = 'Hc certificate'

 
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['certificate.request'].browse(docids)
        logging.info("doc=====================%s",docids)


        content=docs.certificate_type_id.content
        print("5555555555555555555",type(content))

        # fieldm = 'object.' + 'x_given_vote_'+str(no)+'_'+str(idrec)
        # dvote = eval(fieldm, {'object': data})
        logging.info("doc=====================%s",re.findall(r'\{(?:{[^{}]*}|[^{}])*}', content))
        for word in re.findall(r'\{(?:{[^{}]*}|[^{}])*}', content):
            oneword=word.replace('{','')
            finalword=oneword.replace('}','')

            fieldm =finalword
            logging.info("---------fieldm------------------%s,%s",word, fieldm)

            dvote = eval(fieldm, {'object': docs})

            content=content.replace(word,str(dvote))
            # if content.find("salary_wage"):
            #
            #     content = content.replace('salary_wage', str(docs.employee_id.company_id.currency_id.amount_to_text(docs.employee_id.contract_id.total_salary)))


        logging.info("---------------------------%s",content)
        user_post=''
        get_emp_data=self.env['hr.employee'].sudo().search([('user_id','=',self.env.user.name)])
        if len(get_emp_data):
            user_post=get_emp_data[0].job_id.name
        data={'name':content,'sign':self.env.user.sign_signature,'user_name':self.env.user.name,'user_post':user_post}
        return {
              'doc_ids': docids,
              'doc_model': 'certificate.type',
              'docs': docs,
              'data': data,
        }