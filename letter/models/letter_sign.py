from odoo import api, fields, models, tools


class LetterSign(models.Model):
    _inherit = "sign.template",
    letter_ids = fields.One2many('letter.letter', 'sign_template_id', string='Letters Sign')
