import random
import base64
from odoo import api, fields, models, tools
from odoo.tools import is_html_empty


class Letter(models.Model):
    _name = "letter.letter"
    _inherit = [
        "pipeline.record.mixin",
        "mail.tracking.duration.mixin",
        "mail.composer.mixin",
    ]
    _description = "Letter"
    _track_duration_field = "stage_id"

    def _default_stage_id(self):
        letter_type_id = (
                self.env.context.get("letter_type_id", False) or self.letter_type_id.id
        )
        return self.env["letter.type.stage"].search(
            [("letter_type_id", "=", letter_type_id)], limit=1
        )

    def _get_default_mail_template(self):
        letter_type = self.env.context.get("letter_type_id", False)
        if letter_type:
            letter_type = self.env["letter.type"].browse(letter_type)
            print('hello')
            return letter_type.mail_template_id.id

        else:
            print('hi')
            return False

    template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Mail Template",
        domain="[('id', 'in', available_mail_template_ids)]",
        default=lambda self: self._get_default_mail_template(),
    )

    available_mail_template_ids = fields.Many2many(
        comodel_name="mail.template",
        compute="_compute_available_mail_template_ids",
        store=False,
    )

    @api.depends('letter_type_id')
    def _compute_available_mail_template_ids(self):
        for record in self:
            if record.letter_type_id:
                template_ids = record.letter_type_id.mail_template_ids.ids
                if record.letter_type_id.mail_template_id:
                    template_ids.append(record.letter_type_id.mail_template_id.id)
                record.available_mail_template_ids = self.env['mail.template'].browse(template_ids)
            else:
                record.available_mail_template_ids = self.env['mail.template'].browse()

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return self.env["letter.type.stage"].search(
            [("letter_type_id", "in", stages.mapped("letter_type_id.id"))],
            order=order,
        )

    def _get_default_color(self):
        return random.randint(1, 11)

    # Request fields
    name = fields.Char(
        default="/",
        index="trigram",
        string="Reference",
    )
    date = fields.Date(default=fields.Date.today)
    user_id = fields.Many2one(
        string="Author",
        default=lambda self: self.env.user,
    )
    partner_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="letter_partner_rel",
        column1="letter_id",
        column2="partner_id",
        string="Recipients",

    )
    color = fields.Integer(default=lambda self: self._get_default_color())
    letter_type_id = fields.Many2one(
        comodel_name="letter.type",
        string="Letter Type",
        required=True,
        ondelete="restrict",
    )
    letter_type_image = fields.Binary(related="letter_type_id.image")

    # Letter fields
    active = fields.Boolean(default=True)
    stage_id = fields.Many2one(
        comodel_name="letter.type.stage",
        copy=False,
        default=lambda self: self._default_stage_id(),
        domain="[('letter_type_id', '=', letter_type_id)]",
        group_expand="_read_group_stage_ids",
        index=True,
        ondelete="restrict",
        tracking=True,
        string="Stage",
    )
    body = fields.Html(render_options={"post_process": False})

    company_id = fields.Many2one(
        string="Company",
        store=True,
        readonly=True,
        index=True,
        default=lambda self: self.env.company,
    )

    attachment_number = fields.Integer(
        "Number of Attachments", compute="_compute_attachment_number"
    )
    is_closed = fields.Boolean(compute="_compute_is_closed")

    @api.depends("subject")
    def _compute_render_model(self):
        # Because of mail.composer.mixin
        self.render_model = "letter.letter"

    @api.depends("template_id")
    def _compute_subject(self):
        for record in self:
            if record.template_id:
                record._set_value_from_template("subject")
            if not record.template_id or not record.subject:
                record.subject = record.name

    @api.depends("template_id", "partner_ids")
    def _compute_body(self):
        """Compute using from template.

        Render when template value is set otherwise unset it.
        """
        for record in self:
            if record.template_id:
                record._set_value_from_template("body_html", "body")
            if not record.template_id:
                record.body = False

    def _compute_attachment_number(self):
        domain = [("res_model", "=", "letter.letter"), ("res_id", "in", self.ids)]
        attachment_data = self.env["ir.attachment"]._read_group(
            domain, ["res_id"], ["__count"]
        )
        attachment = dict(attachment_data)
        for record in self:
            record.attachment_number = attachment.get(record.id, 0)

    def _compute_is_closed(self):
        for record in self:
            record.is_closed = record.stage_id.is_closing

    # @api.onchange("partner_ids")
    # def _onchange_set_value_from_template(self):
    #     if self.template_id:

    #         # self._set_value_from_template("body_html", "body")
    #         # change the partner ids anytime the partner_ids field is changed
    #
    #         self.partner_ids = self.env["res.partner"].search([("id", "in", self.partner_ids.ids)])
    #         print(type(self.partner_ids))
    #         self.flush_recordset([])
    # else:
    #     self.body = False

    def action_open_attachments(self):
        self.ensure_one()
        res = self.env["ir.actions.act_window"]._for_xml_id("base.action_attachment")
        res["domain"] = [
            ("res_model", "=", "letter.letter"),
            ("res_id", "in", self.ids),
        ]
        res["context"] = {
            "default_res_model": "letter.letter",
            "default_res_id": self.id,
        }
        return res

    @api.onchange("partner_ids")
    def _onchange_partner_ids(self):
        if self.template_id:
            ir_qweb = self.env["ir.qweb"]
            letter_type = self.letter_type_id
            mail_template = self.template_id
            if letter_type and mail_template.body_type == "qweb_view":
                body = ir_qweb._render(
                    mail_template.body_view_id.id,
                    {
                        "object": self,
                        "email_template": mail_template,
                        "format_datetime": lambda dt, tz=False, dt_format=False, lang_code=False: format_datetime(
                            self.env, dt, tz, dt_format, lang_code
                        ),
                    },
                )
                body_html = tools.ustr(body)
                self.body = body_html

    def _set_value_from_template(self, template_fname, composer_fname=False):
        """Set composer value from its template counterpart."""
        self.ensure_one()
        composer_fname = composer_fname or template_fname

        template_value = False
        if self.template_id:
            template_value = self.template_id[template_fname]

        if template_value and template_fname == "body_html":
            template_value = (
                template_value if not is_html_empty(template_value) else False
            )

        if (
                not template_value
                and self.template_id.body_type == "qweb_view"
                and template_fname == "body_html"
        ):
            template_value = True

        if template_value:
            rendering_res_ids = self.ids or [0]
            self[composer_fname] = self.template_id._generate_template(
                rendering_res_ids,
                {template_fname},
            )[rendering_res_ids[0]][template_fname]
        return self[composer_fname]

    #     set the default mail template for each letter when we try to create the letter
    def _set_default_template(self):
        if self.letter_type_id:
            self.template_id = self.letter_type_id.mail_template_id.id
        else:
            self.template_id = False

    def render_pdf(self):
        report_ref = 'letter.letter_report'
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(report_ref, self.id)

        # Save PDF as attachment
        attachment = self.env['ir.attachment'].create({
            'name': f'{self.name}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        return attachment

    def action_download_pdf(self):
        self.ensure_one()
        attachment = self.render_pdf()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
