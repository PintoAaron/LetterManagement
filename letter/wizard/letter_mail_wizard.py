from odoo import api, fields, models

class LetterMailWizard(models.TransientModel):
    _name = 'letter.mail.wizard'
    _description = 'Send Letter as Attachment'

    email_to = fields.Char(string='To', required=True)
    subject = fields.Char(string='Subject', required=True)
    body = fields.Text(string='Body', required=True)
    attachment_id = fields.Many2one('ir.attachment', string='Attachment', readonly=True)
    letter_id = fields.Many2one('letter.letter', string='Letter', required=True)

    def send_email(self):
        self.ensure_one()
        mail_values = {
            'subject': self.subject,
            'body_html': self.body,
            'email_to': self.email_to,
            'attachment_ids': [(6, 0, [self.attachment_id.id])],
        }
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
        self.letter_id.is_delivered = True
        return {'type': 'ir.actions.act_window_close'}