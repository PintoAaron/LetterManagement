from odoo import models, fields


class LetterSignTemplate(models.Model):
    _inherit = 'sign.template'

    letter_ids = fields.One2many(
        comodel_name='letter.letter', inverse_name='sign_template_id', string='Letters')