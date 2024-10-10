from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError


class SignSendRequest(models.TransientModel):
    _inherit = 'sign.send.request'

    letter_id = fields.One2many(
        comodel_name='letter.letter', related='template_id.letter_ids', string='Letter')

    def sign_roles_and_signatories(self):
        template = self.template_id
        if template.letter_ids:

            signatories = template.letter_ids[0].letter_type_id.partner_ids
            sign_items = template.sign_item_ids

            if signatories:
                if len(sign_items) != len(signatories):
                    raise ValidationError(
                        "Sign space allocated does not match with signatories")

            self.signer_id = False
            self.set_sign_order = True
            self.signers_count = len(signatories)
            self.signer_ids = [(5, 0, 0)]

            signatory_names = [
                f'{a}_Signer' for a in range(1, len(signatories) + 1)]
            signer_ids = []

            for index, name in enumerate(signatory_names):
                sign_item_role = self.env['sign.item.role'].search(
                    [('name', '=', name)], limit=1)
                if not sign_item_role:
                    sign_item_role = self.env['sign.item.role'].create({
                        'name': name,
                    })

                if index < len(sign_items):
                    sign_items[index].responsible_id = sign_item_role.id

                signer_ids.append((0, 0, {
                    'role_id': sign_item_role.id,
                    'partner_id': signatories[index].id,
                    'mail_sent_order': index + 1,
                }))

            self.signer_ids = signer_ids
            signers = [{'partner_id': signer.partner_id.id, 'role_id': signer.role_id.id,
                        'mail_sent_order': signer.mail_sent_order} for signer in self.signer_ids]
            cc_partner_ids = self.cc_partner_ids.ids
            reference = self.filename
            subject = self.subject
            message = self.message
            message_cc = self.message_cc
            attachment_ids = self.attachment_ids
            sign_request = self.env['sign.request'].create({
                'template_id': self.template_id.id,
                'request_item_ids': [Command.create({
                    'partner_id': signer['partner_id'],
                    'role_id': signer['role_id'],
                    'mail_sent_order': signer['mail_sent_order'],
                }) for signer in signers],
                'reference': reference,
                'subject': subject,
                'message': message,
                'message_cc': message_cc,
                'attachment_ids': [Command.set(attachment_ids)],
                'validity': self.validity,
                'reminder': self.reminder,
            })
            sign_request.message_subscribe(partner_ids=cc_partner_ids)
            return sign_request

    def send_request(self):
        if self.letter_id:
            request = self.sign_roles_and_signatories()
            if self.activity_id:
                self._activity_done()
                return {'type': 'ir.actions.act_window_close'}
            return request.go_to_document()
        return super().send_request()
