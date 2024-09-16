{
    "name": "Letters",
    "summary": "Manage letter",
    "author": "QG Apps",
    "website": "https://github.com/space-bicycle/odoo-lab",
    "version": "17.0.1.0.2",
    "license": "Other proprietary",
    "category": "Uncategorized",
    "depends": [
        "base",
        "mail",
        "pipeline",
        "email_template_qweb",
        "sign",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "data/letter_type.xml",
        "reports/ir_actions_report.xml",
        "views/letter_menus.xml",
        "views/letter_type_stage.xml",
        "views/letter_type.xml",
        "views/letter_letter.xml",
        "views/letter_dashboard.xml",
        "wizard/letter_mail_wizard.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "letter/static/src/fonts/univers-lt-std-webfont/style.css",
            "letter/static/src/scss/report.scss",
        ],
        "web.report_assets_common": [
            "letter/static/src/fonts/univers-lt-std-webfont/style.css",
            "letter/static/src/scss/report.scss",
        ],
    },
    "application": True,
}
