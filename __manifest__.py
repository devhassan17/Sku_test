# -*- coding: utf-8 -*-
{
    "name": "SKU Test (Pack Components Logger)",
    "summary": "Logs SKUs of component products when ordering pack/kit products",
    "version": "16.0.1.0.0",
    # If you're on 17, change to "17.0.1.0.0" and it will still work.
    "author": "Your Name",
    "license": "LGPL-3",
    "depends": ["sale"],  # "mrp" is optional; component detection handles absence.
    "data": [
        "security/ir.model.access.csv",
    ],
    "application": False,
    "installable": True,
}
