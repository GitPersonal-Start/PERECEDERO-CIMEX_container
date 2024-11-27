from odoo import models, fields, api
from datetime import timedelta


class Rebaja(models.Model):
    _name = 'mgpp.rebaja'
    _description = 'Gestión de Rebajas para Lotes'

    name = fields.Char(
        string='Código de Rebaja', required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('mgpp.rebaja')
    )
    lote_id = fields.Many2one('mgpp.lote', string='Lote', required=True, ondelete='cascade')
    precio_inicial = fields.Float(string='Precio Inicial', required=True)
    precio_actual = fields.Float(string='Precio Actual', compute='_compute_precio_actual', store=True)
    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('rebajado', 'Rebajado')
    ], string='Estado', default='pendiente', required=True)
    solicitudes_ids = fields.One2many('mgpp.solicitud_rebaja', 'rebaja_id', string='Solicitudes de Rebaja')
    fecha_creacion = fields.Datetime(string='Fecha de Creación', default=fields.Datetime.now)
    fecha_finalizacion = fields.Datetime(string='Fecha de Finalización')
    dias_restantes = fields.Integer(string='Días Restantes', compute='_compute_dias_restantes', store=True)
    observaciones = fields.Text(string='Observaciones')

    @api.depends('solicitudes_ids', 'solicitudes_ids.estado', 'solicitudes_ids.precio_aplicado')
    def _compute_precio_actual(self):
        for record in self:
            solicitudes_validas = record.solicitudes_ids.filtered(lambda s: s.estado in ['ejecutada', 'aprobado'])
            if solicitudes_validas:
                solicitud_reciente = solicitudes_validas.sorted(key=lambda s: s.fecha_solicitud, reverse=True)[0]
                record.precio_actual = solicitud_reciente.precio_aplicado
                record.estado = 'rebajado' if solicitud_reciente.estado == 'ejecutada' else 'pendiente'
            else:
                record.precio_actual = record.precio_inicial
                record.estado = 'pendiente'

    @api.depends('lote_id', 'lote_id.use_date')
    def _compute_dias_restantes(self):
        for record in self:
            if record.lote_id.use_date:
                dias = (record.lote_id.use_date - fields.Date.context_today(self)).days
                record.dias_restantes = max(dias, 0)
            else:
                record.dias_restantes = 0

    @api.model
    def create(self, vals):
        rebaja = super(Rebaja, self).create(vals)
        rebaja._crear_solicitudes()
        return rebaja

    def _crear_solicitudes(self):
        """Crea solicitudes de rebaja según días a vencer y evita duplicados."""
        fechas_rebajas = [
            (60, 30),
            (30, 50),
            (15, 70),
            (7, 80)
        ]
        for record in self:
            for dias, porcentaje in fechas_rebajas:
                if record.dias_restantes <= dias:
                    existe_solicitud = record.solicitudes_ids.filtered(
                        lambda s: s.porcentaje_rebaja == porcentaje and s.estado in ['pendiente', 'aprobado']
                    )
                    if not existe_solicitud:
                        self.env['mgpp.solicitud_rebaja'].create({
                            'rebaja_id': record.id,
                            'porcentaje_rebaja': porcentaje,
                            'dias_restantes': dias,
                            'estado': 'pendiente',
                            'fecha_solicitud': fields.Datetime.now()
                        })


class SolicitudRebaja(models.Model):
    _name = 'mgpp.solicitud_rebaja'
    _description = 'Solicitud de rebaja para un lote de productos perecederos'

    name = fields.Char(
        string='Código de Solicitud', required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('mgpp.solicitud.rebaja')
    )
    rebaja_id = fields.Many2one('mgpp.rebaja', string='Rebaja', required=True, ondelete='cascade')
    porcentaje_rebaja = fields.Float(string='Porcentaje de Rebaja', required=True)
    precio_aplicado = fields.Float(string='Precio Aplicado', compute='_compute_precio_aplicado', store=True)
    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('solicitado', 'Solicitado'),
        ('aprobado', 'Aprobado'),
        ('vencido', 'Vencido'),
        ('ejecutada', 'Ejecutada'),
        ('revisada', 'Revisada')
    ], string='Estado', default='pendiente', required=True)
    fecha_solicitud = fields.Datetime(string='Fecha de Solicitud', default=fields.Datetime.now)
    fecha_aprobacion = fields.Datetime(string='Fecha de Aprobación')
    dias_restantes = fields.Integer(string='Días Restantes')
    aprobada_por = fields.Many2one('res.users', string='Aprobada por')
    observaciones = fields.Text(string='Observaciones')

    @api.depends('porcentaje_rebaja', 'rebaja_id.precio_inicial')
    def _compute_precio_aplicado(self):
        for record in self:
            record.precio_aplicado = record.rebaja_id.precio_inicial * (1 - record.porcentaje_rebaja / 100)

    @api.model
    def actualizar_estados(self):
        """Actualiza estados vencidos y prioriza solicitudes más recientes."""
        for record in self.search([]):
            if record.dias_restantes <= 0 and record.estado not in ['ejecutada', 'revisada']:
                record.estado = 'vencido'
