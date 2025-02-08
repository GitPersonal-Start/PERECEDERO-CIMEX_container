# -*- coding: utf-8 -*-
from xml.dom import ValidationErr
from odoo.exceptions import ValidationError
from odoo import models, fields, api
from datetime import date, datetime, timedelta

class Rebaja(models.Model):
    _name = 'mgpp.rebaja'
    _description = 'Gestión de Rebajas para Lotes'
    
    name = fields.Char(string='Código de Rebaja', required=True)
    lote_id = fields.Many2one('mgpp.lote', string='Lote', required=True, ondelete='cascade')
    producto_id = fields.Many2one(related='lote_id.producto_id', string='Producto', store=True)
    precio_inicial = fields.Float(string='Precio Inicial', required=True, readonly=True)
    precio_actual = fields.Float(string='Precio Actual', compute='_compute_precio_actual', store=True, readonly=True)
    estado = fields.Selection([
        ('sin_rebaja', 'Sin Rebaja'),
        ('rebajado', 'Rebajado')
    ], string='Estado', default='pendiente', required=True, readonly=True)
    descuento_rebaja = fields.Integer(default='0', string='Descuento', readonly=True)
    solicitudes_ids = fields.One2many('mgpp.solicitud_rebaja', 'rebaja_id', string='Solicitudes de Rebaja', readonly=True, ondelete='cascade')
    fecha_creacion = fields.Date(string='Fecha de Creación', default=fields.Date.today, readonly=True)
    fecha_finalizacion = fields.Date(string='Fecha de Finalización', required=True, readonly=True)
    dias_restantes = fields.Integer(string='Días Restantes', compute='_compute_dias_restantes', store=True, readonly=True)
    fecha_modificacion = fields.Date(string='Fecha de Modificación', readonly=True)
    observaciones = fields.Text(string='Observaciones', readonly=True)

    perdida_ganancias = fields.Float(
        string='Pérdida de Ganancias',
        compute='_compute_perdida_ganancias',
        store=True,
        help="Pérdida de ganancias debido a las rebajas aplicadas."
    )
    @api.depends('precio_inicial', 'precio_actual')
    def _compute_perdida_ganancias(self):
        for rebaja in self:
            rebaja.perdida_ganancias = rebaja.precio_inicial - rebaja.precio_actual

    @api.depends('fecha_finalizacion')
    def _compute_dias_restantes(self):
        """Calcula los días restantes hasta la fecha de finalización."""
        for record in self:
            if record.fecha_finalizacion:
                hoy = fields.Date.context_today(record)
                dias = (record.fecha_finalizacion - hoy).days
                record.dias_restantes = max(dias, 0)
            else:
                record.dias_restantes = 0

    @api.depends('solicitudes_ids', 'solicitudes_ids.estado')
    def _compute_precio_actual(self):
        """Calcula el precio actual basado en la solicitud de rebaja ejecutada."""
        for record in self:
            solicitud_ejecutada = record.solicitudes_ids.filtered(lambda s: s.estado == 'ejecutada')
            if solicitud_ejecutada:
                solicitud = solicitud_ejecutada[0]  # Tomar la primera solicitud ejecutada
                porcentaje = float(solicitud.descuento_rebaja) / 100
                record.precio_actual = record.precio_inicial * (1 - porcentaje)
                record.descuento_rebaja = solicitud.descuento_rebaja
                record.estado = 'rebajado'
                record.fecha_modificacion = fields.Date.context_today(self)
            else:
                record.precio_actual = record.precio_inicial
                
    @api.model
    def create(self, vals):
        """Crea automáticamente cuatro solicitudes de rebaja al crear la rebaja."""
        # Crear el registro de la rebaja
        rebaja = super().create(vals)
        # Obtener el nombre del producto asociado al lote
        producto_nombre = rebaja.lote_id.producto_id.name if rebaja.lote_id.producto_id else 'Producto Desconocido'
        # Lista de descuentos a aplicar
        descuentos = ['30', '50', '70', '80']
        
        for descuento in descuentos:
            # Calcular el precio aplicado
            precio_aplicado = rebaja.precio_inicial * (1 - int(descuento) / 100)
            
            # Determinar los días antes de la validación según el descuento
            dias_antes = 0
            if descuento == '30':
                dias_antes = 60
            elif descuento == '50':
                dias_antes = 30
            elif descuento == '70':
                dias_antes = 15
            elif descuento == '80':
                dias_antes = 7
            
            # Calcular la fecha de validación
            fecha_validacion = (
                rebaja.fecha_finalizacion - timedelta(days=dias_antes)
                if rebaja.fecha_finalizacion
                else None
            )
            
            # Crear la solicitud de rebaja con la lógica aplicada
            self.env['mgpp.solicitud_rebaja'].create({
                'name': f"{producto_nombre} - {descuento}%",
                'rebaja_id': rebaja.id,
                'lote_id': rebaja.lote_id.id,
                'descuento_rebaja': descuento,
                'precio_aplicado': precio_aplicado,
                'estado': 'pendiente',
                'fecha_solicitud': fields.Date.context_today(self),
                'fechas_vencimiento': rebaja.fecha_finalizacion,
                'fechas_validacion': fecha_validacion,
                'observaciones': f"Solicitud de rebaja del {descuento}% creada automáticamente.",
            })
        
        return rebaja
    def action_open_solicitudes(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Solicitudes de Rebaja',
            'view_mode': 'tree,form',
            'res_model': 'mgpp.solicitud_rebaja',
            'domain': [('rebaja_id', '=', self.id)],
        }
    def action_crear_solicitud(self):
        self.ensure_one()  # Asegúrate de que solo hay una rebaja seleccionada
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nueva Solicitud de Rebaja',
            'view_mode': 'form',
            'res_model': 'mgpp.solicitud_rebaja',
            'target': 'new',  # Abre el formulario como un modal
            'context': {
                'default_rebaja_id': self.id,  # Asocia automáticamente la solicitud con esta rebaja
                'default_fechas_vencimiento': self.fecha_finalizacion,  # Configuración inicial opcional
                'default_precio_aplicado': self.precio_inicial,  # Ejemplo de precio inicial con descuento
            },
        }
    def action_solicitar_todas(self):
        for solicitud in self.solicitudes_ids:
            if solicitud.estado == 'pendiente':
                solicitud.action_solicitar()


class SolicitudRebaja(models.Model):
    _name = 'mgpp.solicitud_rebaja'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Solicitud de Rebaja'

    fecha_validacion_id = fields.Many2one('mgpp.fecha_validacion', string="Fecha de Validación", ondelete='cascade')
    approval_log_ids = fields.One2many(
        'mgpp.approval_log', 'solicitud_id', string="Historial de Aprobaciones", ondelete='cascade'
    )
    name = fields.Char(string='Código de Solicitud', required=True)
    codigo_23 = fields.Char(string='Código 23')
    codigo_23_aplicado = fields.Boolean(string='Código 23 Aplicado', default=False)
    rebaja_id = fields.Many2one(
        'mgpp.rebaja', string='Rebaja', required=True
    )
    lote_id = fields.Many2one('mgpp.lote', string='Lote', required=True, ondelete='cascade')
    descuento_rebaja = fields.Integer(string='Descuento')
    precio_aplicado = fields.Float(string='Precio Aplicado', required=True, readonly=True)
    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('solicitado', 'Solicitado'),
        ('pendiente_aprobacion', 'Pendiente de Aprobación'),
        ('aprobado', 'Aprobado'),
        ('vencido', 'Vencido'),
        ('ejecutada', 'Ejecutada'),
        ('revisada', 'Revisada')
    ], string='Estado', default='pendiente', required=True, readonly=True)
    fecha_solicitud = fields.Date(
        string='Fecha de Solicitud', default=fields.Date.today, readonly=True
    )
    observaciones = fields.Text(string='Observaciones')
    usuarios_aprobadores = fields.Many2many('res.users', string='Aprobadores')
    total_aprobaciones = fields.Integer(
        string='Total de Aprobaciones', compute='_compute_total_aprobaciones'
    )
    fechas_validacion = fields.Date(string="Fecha de Validación")
    fechas_vencimiento= fields.Date(string="Fecha de Vencimiento")

    # Restricción SQL para garantizar unicidad
    _sql_constraints = [
        (
            'unique_rebaja_fecha_validacion',
            'unique(rebaja_id, fecha_validacion)',
            'No se pueden crear solicitudes de rebaja con la misma fecha de validación asociadas a la misma rebaja.'
        ),
    ]
    
    @api.constrains('fecha_validacion', 'fecha_vencimiento')
    def _check_fecha_validacion(self):
        """
        Valida que la fecha de validación esté entre hoy y la fecha de vencimiento.
        """
        hoy = fields.Date.today()
        for record in self:
            # Validar rango de fecha
            if record.fechas_validacion < hoy:
                raise ValidationError("La fecha de validación no puede ser anterior al día de hoy.")
            if record.fechas_validacion > record.fechas_vencimiento:
                raise ValidationError("La fecha de validación no puede ser posterior a la fecha de vencimiento.")

    def write(self, vals):
        """
        Sobreescribe el método `write` para validar lógica entre rebajas menores y mayores
        solo cuando el estado cambie a 'pendiente_aprobacion'.
        """
        for record in self:
            nuevo_estado = vals.get('estado', record.estado)
            if nuevo_estado == 'pendiente_aprobacion':
                # Buscar solicitudes conflictivas
                solicitudes_conflictivas = self.search([
                    ('id', '!=', record.id),
                    ('estado', 'in', ['pendiente_aprobacion', 'aprobada']),
                    ('fechas_validacion', '>=', record.fechas_validacion),
                    ('fechas_vencimiento', '=', record.fechas_vencimiento)
                ])
                for solicitud in solicitudes_conflictivas:
                    if solicitud.descuento_rebaja == record.descuento_rebaja:
                        raise ValidationError(
                            f"No es lógico aprobar una rebaja del {record.descuento_rebaja}% "
                            f"con fecha de validación {record.fechas_validacion} si existe una rebaja del "
                            f"{solicitud.descuento_rebaja}% con una validación posterior ({solicitud.fechas_validacion})."
                        )

        return super(SolicitudRebaja, self).write(vals)
    
    @api.depends('usuarios_aprobadores')
    def _compute_total_aprobaciones(self):
        """Cuenta el número de aprobaciones."""
        for record in self:
            record.total_aprobaciones = len(record.usuarios_aprobadores)

    def action_aprobar(self):
        """Aprobar la solicitud."""
        self.ensure_one()

        if self.estado != 'revisada':
            raise ValidationError('Solo se pueden aprobar solicitudes que estén en estado "Revisada".')

        user = self.env.user

        if user in self.usuarios_aprobadores:
            raise ValidationError('Ya has aprobado esta solicitud.')

        self.env['mgpp.approval_log'].create({
            'solicitud_id': self.id,
            'usuario_id': user.id,
            'fecha': fields.Date.today(),
            'horas': fields.Datetime.now(),
            'observaciones': 'Aprobación realizada.'
        })

        self.write({'usuarios_aprobadores': [(4, user.id)]})

        if len(self.usuarios_aprobadores) == 1:
            self.write({'estado': 'pendiente_aprobacion'})
        elif len(self.usuarios_aprobadores) >= 3:
            self.write({'estado': 'aprobado'})

    def action_cancelar_aprobacion(self):
        """Cancelar la aprobación de la solicitud."""
        self.ensure_one()

        if self.estado not in ['pendiente_aprobacion', 'revisada']:
            raise ValidationError('No se puede cancelar la aprobación en el estado actual.')

        user = self.env.user

        if user not in self.usuarios_aprobadores:
            raise ValidationError('No puedes cancelar una aprobación que no has realizado.')

        self.write({'usuarios_aprobadores': [(3, user.id)]})

        log = self.env['mgpp.approval_log'].search([
            ('solicitud_id', '=', self.id),
            ('usuario_id', '=', user.id)
        ], limit=1)
        if log:
            log.unlink()

        if len(self.usuarios_aprobadores) == 0:
            self.write({'estado': 'revisada'})
        elif len(self.usuarios_aprobadores) < 3:
            self.write({'estado': 'pendiente_aprobacion'})
        
    def action_solicitar(self, **kwargs):
        for record in self:
            if record.estado == 'pendiente':
                record.estado = 'solicitado'
    def action_cancelar_solicitud(self):
        for record in self:
            if record.estado == 'solicitado':
                record.estado = 'pendiente'

    def action_marcar_revisada(self):
        for record in self:
            if record.estado == 'solicitado':
                record.estado = 'revisada'

    def action_cancelar_revision(self):
        for record in self:
            if record.estado == 'revisada':
                record.estado = 'solicitado'
    @api.model
    def create(self, vals):
        """Valida que no existan solicitudes con el mismo porcentaje de descuento para la misma rebaja."""
        existing_solicitudes = self.env['mgpp.solicitud_rebaja'].search([
            ('rebaja_id', '=', vals.get('rebaja_id')),
            ('descuento_rebaja', '=', vals.get('descuento_rebaja'))
        ])
        if existing_solicitudes:
            raise ValueError(f"Ya existe una solicitud con el descuento del {vals.get('descuento_rebaja')}% para este lote de producto.")
        # Calcular el precio aplicado si no está definido
        if 'descuento_rebaja' in vals and 'precio_aplicado' not in vals:
            rebaja = self.env['mgpp.rebaja'].browse(vals['rebaja_id'])
            descuento = float(vals.get('descuento_rebaja', 0)) / 100
            vals['precio_aplicado'] = rebaja.precio_inicial * (1 - descuento)
            
        if 'fecha_validacion_id' not in vals and 'fechas_validacion' in vals:
            fecha = vals['fechas_validacion']
            fecha_record = self.env['mgpp.fecha_validacion'].search([('fechas_validacion', '=', fecha)], limit=1)
            if not fecha_record:
                fecha_record = self.env['mgpp.fecha_validacion'].create({'fechas_validacion': fecha})
            vals['fecha_validacion_id'] = fecha_record.id
            
        return super(SolicitudRebaja, self).create(vals)
    
class ApprovalLog(models.Model):
    _name = 'mgpp.approval_log'
    _description = 'Historial de Aprobaciones'

    solicitud_id = fields.Many2one(
        'mgpp.solicitud_rebaja', string="Solicitud Relacionada", required=True
    )
    usuario_id = fields.Many2one(
        'res.users', string="Usuario", required=True, default=lambda self: self.env.user
    )
    fecha = fields.Date(string="Fecha", default=fields.Date.context_today)
    # hora = fields.Float(string="Hora", default=lambda self: fields.Datetime.now().hour + fields.Datetime.now().minute / 60)
    observaciones = fields.Text(string="Observaciones")
    horas = fields.Char(string="Hora", default=lambda self: self._get_current_hour())

    def _get_current_hour(self):
        now = datetime.now()
        return now.strftime("%H:%M")  # Formato HH:MM
   
    

    
    

