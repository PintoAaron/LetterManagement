{
    "name": "Letter Sign",
    "summary": "Integrate e-signature in letter",
    "author": "QG Apps",
    "website": "https://github.com/space-bicycle/odoo-lab",
    "version": "17.0.1.0.2",
    "license": "Other proprietary",
    "category": "Uncategorized",
    "depends": [
        "base",
        "letter",
        "sign",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/letter_letter.xml",
        "views/letter_menus.xml",
    ],
    "application": True,
    "installable": True,
}
