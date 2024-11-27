# -*- coding: utf-8 -*-
{
    'name': "Gestión Perecederos CIMEX",
    
    'summary': """
        Módulo para el registro y control de productos perecederos en la empresa CIMEX""",
        
    'description': """
        Este módulo permite a la empresa CIMEX gestionar el inventario de productos perecederos,
        controlando su fecha de caducidad, ubicación en almacén y alerta de vencimiento,
        rebajas y otros aspectos relevantes para la gestión eficiente de productos perecederos.
    """,
    
    'author': "CIMEX",
    'website': "https://www.yourcompany.com",
    'category': 'Inventory',
    'version': '1.0',
    'depends': ['base'],
    'images': ['static/description/icon.png'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/configuracion.xml',
        'views/templates.xml',
        'views/producto.xml',
        # 'views/solicitud.xml',
        'views/estructura.xml',
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
