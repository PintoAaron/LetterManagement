from odoo import models, fields, api, Command

from odoo.exceptions import UserError
import base64


class LetterSign(models.Model):
    _inherit = 'letter.letter'

    def _compute_signature_status(self):
        for record in self:
            sign_request = self.env['sign.request'].search(
                [('template_id', '=', record.sign_template_id.id)],
                limit=1
            )
            record.signature_status = sign_request.state if sign_request else ''

    def _compute_is_sign(self):
        for record in self:
            record.is_sign = True if record.stage_id.name == "Approve and Sign" else False

    sign_request_id = fields.Many2one(
        'sign.request', string="Signature Request", readonly=True)
    sign_template_id = fields.Many2one(
        'sign.template', string="Signature Template", readonly=True)
    is_sign = fields.Boolean(compute="_compute_is_sign")
    signature_status = fields.Char(compute="_compute_signature_status")
    is_delivered = fields.Boolean(default=False)

    def action_create_sign_template(self):
        self.ensure_one()
        if self.sign_template_id:
            return self.sign_template_id.go_to_custom_template()
        report_ref = 'letter.letter_report'
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
            report_ref, self.id)
        attachment = self.env['ir.attachment'].create({
            'name': self.name,
            'datas': base64.b64encode(pdf_content),
            'res_model': 'sign.template',
            'type': 'binary',
        })
        sign_template = self.env['sign.template'].create({
            'name': f"{self.name} - {self.subject}",
            'attachment_id': attachment.id,
        })
        self.sign_template_id = sign_template.id
        return sign_template.go_to_custom_template()

    def action_open_signature_kanban(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Signature Templates',
            'res_model': 'sign.template',
            'view_mode': 'kanban',
            'view_id': self.env.ref('sign.sign_template_view_kanban').id,
            'target': 'current',
            "domain": [('letter_ids', '!=', False)],

        }

    def _get_fully_signed_letter_pdf(self):
        sign_request = self.env['sign.request'].search(
            [('state', '=', 'signed'), ('template_id', '=', self.sign_template_id.id)],
            limit=1
        )
        if not sign_request:
            raise UserError("This letter has not been signed yet.")

        if not sign_request.completed_document_attachment_ids:
            sign_request._generate_completed_document()
        attachment = sign_request.completed_document_attachment_ids[1]
        pdf_content = attachment.datas
        existing_attachment = self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('name', 'like', f'{self.name}.pdf')
        ])
        if existing_attachment:
            existing_attachment.unlink()
        new_attachment = self.env['ir.attachment'].create({
            'name': f'{self.name}.pdf',
            'type': 'binary',
            'datas': pdf_content,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        return new_attachment

    def action_download_pdf(self):
        self.ensure_one()
        attachment = self._get_fully_signed_letter_pdf()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def action_send_as_attachment(self):
        self.ensure_one()
        attachment = self._get_fully_signed_letter_pdf()

        subject = f"Letter:  {self.name} - {self.subject}".upper()
        return {
            'name': 'Send Letter as Attachment',
            'type': 'ir.actions.act_window',
            'res_model': 'letter.mail.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_subject': subject,
                'default_email_to': self.partner_ids[0].email or "receipient@gmail.com",
                'default_body': f"Please find attached the letter:  {self.name}",
                'default_attachment_id': attachment.id,
                'default_letter_id': self.id,
            },
        }

    def action_open_letter_requests(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Sign Requests",
            "res_model": "sign.request",
            "res_id": self.id,
            "domain": [["template_id", "in", self.sign_template_id.ids]],
            "views": [[False, 'kanban'], [False, "form"]]
        }
