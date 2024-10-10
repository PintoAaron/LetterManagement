from odoo import models, fields, api, Command
from odoo.exceptions import ValidationError


class LetterSignRequest(models.Model):
    _inherit = 'sign.request'

    sign_request_ids = fields.One2many(
        comodel_name='letter.letter', inverse_name='sign_request_id', string='Signature Request')

    # def _validate_signatories_assigned(self,vals):
    #     template_id = vals.get('template_id')
    #     if template_id:
    #         template = self.env['sign.template'].browse(template_id)
    #         if template.letter_ids and template.letter_ids[0].letter_type_id.partner_ids:
    #             if len(template.sign_item_ids) != len(template.letter_ids[0].letter_type_id.partner_ids):
    #                 raise ValidationError(
    #                     "Sign space allocated does not match with signatories")
                                   
        
        
    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         self._validate_signatories_assigned(vals)
    #     res = super().create(vals_list)
    #     return res
    
    
    
