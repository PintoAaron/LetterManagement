from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class LetterTypeStage(models.Model):
    _name = "letter.type.stage"
    _inherit = "pipeline.stage.mixin"
    _description = "Letter Type Stage"

    letter_type_id = fields.Many2one(
        comodel_name="letter.type",
        string="Letter Type",
        ondelete="cascade",
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        related="letter_type_id.company_id",
        store=True,
    )

    @api.constrains("is_closing")
    def _check_unique_closing_stage(self):
        """Ensure closing stage is unique for each letter type."""
        self.flush_recordset(["letter_type_id", "is_closing"])
        query = """\
            SELECT letter_type_id
              FROM letter_type_stage
             WHERE letter_type_id = %(letter_type_id)s
               AND is_closing = TRUE
               AND active = TRUE
             GROUP BY letter_type_id
            HAVING COUNT(*) > 1;
        """
        self.env.cr.execute(
            query,
            {
                "letter_type_id": self.letter_type_id.id,
            },
        )
        exists = self.env.cr.fetchone()
        if exists:
            raise ValidationError(
                _("A closing stage must be unique for each letter type!")
            )
