# -*- coding: utf-8 -*-
{
    'name': "Gestion Perecederos CIMEX",
    
    'summary': """
        Modulo para el registro y control de productos perecederos en la empresa CIMEX""",
        
    'description': """
        Este modulo permite a la empresa CIMEX gestionar el inventario de productos perecederos,
        controlando su fecha de caducidad, ubicacion y alerta de vencimiento,
        rebajas y otros aspectos relevantes para la gestion eficiente de productos perecederos.
    """,
    
    'author': "CIMEX",
    'website': "https://www.yourcompany.com",
    'category': 'Inventory',
    'version': '1.0',
    'depends': ['base','mail'],
    'images': ['static/description/icon.png'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/configuracion.xml',
        'views/templates.xml',
        'views/producto.xml',
        'views/rebaja.xml',
        'views/estructura.xml',
        # 'views/codigo.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',
    'application': True, 
    'installable': True,
    'auto_install': False,
}
