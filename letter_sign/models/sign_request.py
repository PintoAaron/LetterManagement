from odoo import models, fields, api, Command
from odoo.exceptions import ValidationError


class LetterSignRequest(models.Model):
    _inherit = 'sign.request'

    sign_request_ids = fields.One2many(
        comodel_name='letter.letter', inverse_name='sign_request_id', string='Signature Request')

    def _check_sign_item_ids(self):
        for record in self:
            if record.template_id.letter_ids[0].letter_type_id.partner_ids:
                if len(record.template_id.sign_item_ids) != len(record.template_id.letter_ids[0].letter_type_id.partner_ids):
                    raise ValidationError(
                        "Number of signing space does not match with signatories")

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            record._check_sign_item_ids()
        return res
