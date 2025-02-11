import base64
from random import randint
from odoo import fields, models


class LetterInbound(models.Model):
    _name = 'letter.inbound'
    _description = 'Letter Inbound'

    _check_company_auto = True

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(required=True, string='Reference')
    date = fields.Date(default=fields.Date.today,
                       help="When the letter is to be sent")
    description = fields.Text()
    attachment = fields.Binary(string='Letter')
    user_id = fields.Many2one(
        string="Sender",
        default=lambda self: self.env.user,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Recipient",
    )
    color = fields.Integer(default=lambda self: self._get_default_color())
    status = fields.Selection(
        default='pending',
        readonly=True,
        selection=[
            ('sent', 'Sent'),
            ('pending', 'Pending'),
            ('failed', 'Failed'),
        ])
    active = fields.Boolean(default=True)
    is_delivered = fields.Boolean(default=False)

    def send_inbound_letter(self):
        try:
            mail_values = {
                'subject': f"Inbound Letter: {self.name}",
                'body_html': f"Dear {self.partner_id.name}, Kindly find the attached letter.",
                'email_to': self.partner_id.email,
                'attachment_ids': [(0, 0, {
                    'name': self.name,
                    'datas': base64.b64encode(self.attachment),
                    'res_model': 'letter.inbound',
                    'type': 'binary',
                })],
            }
            mail = self.env['mail.mail'].create(mail_values)
            mail.send()
            self.is_delivered = True
            self.status = 'sent'
        except Exception:
            self.is_delivered = False
            self.status = 'failed'
        return True

    def send_inbound_letter_cron(self):
        inbound_letters = self.search([])
        for record in inbound_letters:
            if not record.is_delivered and record.date == fields.Date.today():
                record.send_inbound_letter()
        return True

    def action_send_inbound_letter(self):
        self.ensure_one()
        self.send_inbound_letter()
        return True
