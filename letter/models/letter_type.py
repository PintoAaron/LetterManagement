import ast
import base64

from odoo import _, api, fields, models, tools
from odoo.fields import Command

DEFAULT_STAGES = {
    1: {"name": _("Draft"), "is_closing": False},
    2: {"name": _("Review"), "is_closing": False},
    3: {"name": _("Approve and Sign"), "is_closing": False},
    4: {"name": _("Complete"), "is_closing": True},
}


class LetterType(models.Model):
    _name = "letter.type"
    _description = "Letter Type"
    _order = "sequence, id"

    _check_company_auto = True

    def _get_default_image(self):
        default_image_path = "letter/static/src/img/Envelope.png"
        return base64.b64encode(tools.misc.file_open(default_image_path, "rb").read())

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        copy=False,
        required=True,
        index=True,
        default=lambda s: s.env.company,
        string="Company",
    )
    description = fields.Char()
    active = fields.Boolean(default=True)
    sequence = fields.Integer()
    image = fields.Binary(default=_get_default_image)
    mail_template_id = fields.Many2one(
        comodel_name="mail.template",
        domain=[("model", "=", "letter.letter")],
        string="Default Template",

    )
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        domain=[('is_company', '=', False)],
        relation="letter_type_partner_rel",
        column1="letter_type_id",
        column2="partner_id",
        string='Signatories')
    
    mail_template_ids = fields.Many2many(
        comodel_name="mail.template",
        domain=[("model", "=", "letter.letter")],
        relation="letter_type_mail_template_rel",
        column1="letter_type_id",
        column2="mail_template_id",
        string="Templates",
    )

    stage_ids = fields.One2many(
        comodel_name="letter.type.stage",
        inverse_name="letter_type_id",
        string="Pipeline",
    )

    show_configure_pipeline = fields.Boolean(compute="_compute_show_configure_pipeline")
    letter_count = fields.Integer(
        string="Number of letters I've authored",
        compute="_compute_letter_count",
    )
    letter_to_review_count = fields.Integer(
        string="Number of letters to review",
        compute="_compute_letter_to_review_count",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("stage_ids"):
                vals["stage_ids"] = [
                    Command.create(
                        {
                            "name": stage["name"],
                            "sequence": sequence,
                            "is_closing": stage["is_closing"],
                        }
                    )
                    for sequence, stage in DEFAULT_STAGES.items()
                ]
        return super().create(vals_list)

    @api.depends("stage_ids")
    def _compute_show_configure_pipeline(self):
        for record in self:
            record.show_configure_pipeline = not bool(record.stage_ids)

    def _compute_letter_count(self):
        domain = [("user_id", "=", self.env.user.id)]
        letters_data = self.env["letter.letter"]._read_group(
            domain, ["letter_type_id"], ["__count"]
        )
        letters_mapped_data = {
            letter_type.id: count for letter_type, count in letters_data
        }
        for record in self:
            record.letter_count = letters_mapped_data.get(record.id, 0)

    def _compute_letter_to_review_count(self):
        domain = [("partner_ids.user_id", "=", self.env.user.id)]
        letters_data = self.env["letter.letter"]._read_group(
            domain, ["letter_type_id"], ["__count"]
        )
        letters_mapped_data = {
            letter_type.id: count for letter_type, count in letters_data
        }
        for record in self:
            record.letter_to_review_count = letters_mapped_data.get(record.id, 0)

    def action_create_letter(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "letter.letter",
            "views": [(False, "form")],
            "context": {
                "default_letter_type_id": self.id,
                "default_user_id": self.env.user.id,
                "default_template_id": self.mail_template_id.id,
            },
        }

    def action_open_letter_type_stage(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "letter.letter_type_stage_window"
        )
        action["name"] = f"{self.name} - Pipeline"
        action["display_name"] = f"{self.name} - Pipeline"
        action["domain"] = [("letter_type_id", "=", self.id)]
        ctx = dict(ast.literal_eval(action["context"]))
        ctx.update({"default_letter_type_id": self.id})
        action["context"] = ctx
        return action

    def action_open_letter_pipeline(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "letter.letter_pipeline_window"
        )
        action["name"] = f"{self.name} - Letters"
        action["display_name"] = f"{self.name} - Letters"
        action["domain"] = [
            ("letter_type_id", "=", self.id),
            ("user_id", "=", self.env.user.id),

        ]
        ctx = dict(ast.literal_eval(action["context"]))
        ctx.update({"default_letter_type_id": self.id})
        action["context"] = ctx
        return action

    def action_open_to_review_pipeline(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "letter.letter_pipeline_window"
        )
        action["name"] = f"{self.name} - Letters"
        action["display_name"] = f"{self.name} - Letters"
        action["domain"] = [
            ("letter_type_id", "=", self.id),
            ("partner_ids.user_id", "=", self.env.user.id),
        ]
        ctx = dict(ast.literal_eval(action["context"]))
        ctx.update({"default_letter_type_id": self.id})
        action["context"] = ctx
        return action




