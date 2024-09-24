from odoo import models, fields, api, Command


class LetterSignRequest(models.Model):
    _inherit = 'sign.request'

    sign_request_ids = fields.One2many(comodel_name='letter.letter', inverse_name='sign_request_id', string='Signature Request')
