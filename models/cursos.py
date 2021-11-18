# -*- coding: utf-8 -*-

from odoo import api, models, tools, fields

import logging
import time
import datetime
from datetime import date
import pytz
from pytz import timezone

dias_array = [('lunes', 'Lunes'),('martes', 'Martes'),('miercoles', 'Miércoles'),('jueves', 'Jueves'),('viernes', 'Viernes'),('sabado', 'Sábado')]

class sede(models.Model):

    _name = 'cursos.sede'

    name = fields.Char('Nombre')

class curso(models.Model):

    _name = 'cursos.curso'

    name = fields.Char('Nombre')
    sede_id = fields.Many2one('cursos.sede','Sede', required=True)
    fecha_inicio = fields.Date('Fecha Inicio', required=True)
    fecha_fin = fields.Date('Fecha Fin', required=True)

class horario(models.Model):

    _name = 'cursos.horario'

    curso_id = fields.Many2one('cursos.curso','Curso', required=True)
    cupo = fields.Integer('Cupo')
    dia = fields.Selection(dias_array, 'Dia', default='lunes')
    profesores = fields.Many2many('res.partner','horario_partner_rel1', 'horario_id','partner_id', 'Profesores')
    hora_inicio = fields.Float('Hora Inicio')
    hora_fin = fields.Float('Hora Fin')
    historial_curso_ids = fields.One2many('cursos.historial','horario_id', domain=[('fecha_fin','>=',date.today())],string = 'Historial', readonly= True )
    cupo_disponible = fields.Integer('Cupo disponible',compute='_get_cupo_disponible')

    def _get_cupo_disponible(self):
        for horario in self:
            cupo_disponible = horario.cupo - len(horario.historial_curso_ids)
            historiales_congelamientos = self.env['cursos.congelamiento'].search([('horario_id','=',horario.id)])

            horario.cupo_disponible = cupo_disponible + len(historiales_congelamientos)

    @api.multi
    def name_get(self):
        res = []
        for hr in self:
            segundos = hr.hora_inicio * 3600
            hora_minutos = str(datetime.timedelta(seconds=segundos))
            segundos2 = hr.hora_fin * 3600
            hora_minutos2 = str(datetime.timedelta(seconds=segundos2))
            res.append((hr.id, hr.curso_id.name + ", "+hr.dia+ ", "+hora_minutos[0:5]+ "-"+hora_minutos2[0:5]))
        return res

    def generar_eventos(self):
        dia_semana = [i for i in range(len(dias_array)) if dias_array[i][0] == self.dia][0]
        hora_i = int(self.hora_inicio)
        minuto_i = int((self.hora_inicio % 1) * 60)
        hora_f = int(self.hora_fin)
        minuto_f = int((self.hora_fin % 1) * 60)

        fecha_inicio = fields.Datetime.from_string(self.curso_id.fecha_inicio)
        fecha_fin = fields.Datetime.from_string(self.curso_id.fecha_fin)
        fecha = fecha_inicio
        dias_dif = 1
        while fecha <= fecha_fin:
            if dia_semana == fecha.weekday():
                f_i = fecha.replace(hour=hora_i+6, minute=minuto_i)
                f_f = fecha.replace(hour=hora_f+6, minute=minuto_f)
                evento =  {'fecha_inicio':fields.Datetime.to_string(f_i), 'fecha_fin':fields.Datetime.to_string(f_f), 'horario_id':self.id}
                evento_id = self.env['cursos.evento'].create(evento)
                dias_dif = 7
            fecha = fecha + datetime.timedelta(days=dias_dif)

class historial(models.Model):

    _name = 'cursos.historial'

    fecha_inicio = fields.Date('Fecha Inicio')
    fecha_fin = fields.Date('Fecha Fin')
    alumno_id = fields.Many2one('res.partner','Alumno')
    horario_id = fields.Many2one('cursos.horario','Horario')
    nombre_alumno = fields.Char(related='alumno_id.name', store=True)
    reposicion = fields.Boolean('Reposición')

class asignacion(models.TransientModel):

    _name = 'cursos.asignacion'

    curso_id = fields.Many2one('cursos.curso', 'Curso', required=True)
    alumno_id = fields.Many2one('res.partner', 'Alumno', required=True)
    fecha_inicio = fields.Date('Fecha Inicio', required=True)
    horarios_asignaciones = fields.One2many('cursos.asignacion_horario', 'asignacion_id', 'Horarios')
    fecha_fin = fields.Date('Fecha Fin')

    def buscar_cupo(self):
        for ha in self.horarios_asignaciones:
            self.write({'horarios_asignaciones': [(2,ha.id)]})

        horarios = self.env['cursos.horario'].search([('curso_id','=',self.curso_id.id)])
        horarios_array = []
        if self.fecha_inicio >= self.curso_id.fecha_inicio and self.fecha_inicio <= self.curso_id.fecha_fin:
            for horario in horarios:
                historiales = self.env['cursos.historial'].search([('horario_id','=',horario.id),('fecha_fin','=',False)])
                historiales_congelamientos = self.env['cursos.congelamiento'].search([('horario_id','=',horario.id)])
                # Buscar cupo
                alumnos_asignados = 0
                alumnos_reposicion = 0
                fecha_asignacion = datetime.datetime.strptime(self.fecha_inicio,"%Y-%m-%d")
                if len(historiales) > 0:
                    for historial in historiales:
                        if historial.reposicion:
                            fecha_c_f = datetime.datetime.strptime(historial.fecha_inicio, "%Y-%m-%d")
                            if (fecha_asignacion <= fecha_c_f <= fecha_asignacion):
                                alumnos_reposicion += 1
                        else:
                            alumnos_asignados += 1
                else:
                    historiales = self.env['cursos.horario']
                    historiales += horario
                cupo_disp = horario.cupo - alumnos_asignados
                fecha_asignacion = datetime.datetime.strptime(self.fecha_inicio,"%Y-%m-%d")
                if len(historiales):
                    # cupo_disp = horario.cupo - len(historiales)
                    congelados = 0
                    # fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d")
                    for congelamiento in historiales_congelamientos:
                        if congelamiento.fecha_congelamiento:
                            fecha_c_f = datetime.datetime.strptime(congelamiento.fecha_congelamiento, "%Y-%m-%d")
                            fecha_c_i = datetime.datetime.strptime(congelamiento.fecha_inicio_congelamiento, "%Y-%m-%d")
                            if (fecha_c_f >= fecha_asignacion) & (fecha_c_i <= fecha_asignacion):
                                congelados = congelados +1

                    cupo_disp += congelados - alumnos_reposicion
                    if cupo_disp > 0:
                        asign_horario =  {'asignacion_id':self.id, 'seleccionado': False, 'cupo_disponible':cupo_disp, 'horario_id':horario.id, 'congelados': congelados }
                        asign_horario_id = self.env['cursos.asignacion_horario'].create(asign_horario)
                        h_cupo = (4,asign_horario_id.id)
                        horarios_array.append(h_cupo)

        self.write({'horarios_asignaciones': horarios_array})
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cursos.asignacion',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def asignar(self):
        for a_horario in self.horarios_asignaciones:
            if a_horario.seleccionado:
                fecha_fin = False
                if self.fecha_fin == False:
                    self.fecha_fin = False
                else:
                    fecha_fin = self.fecha_fin
                historial =  {'fecha_inicio':self.fecha_inicio, 'fecha_fin':fecha_fin, 'alumno_id':self.alumno_id.id, 'horario_id':a_horario.horario_id.id, 'reposicion': a_horario.reposicion }
                hist_id = self.env['cursos.historial'].create(historial)
        return {'type': 'ir.actions.act_window_close'}

class asignacion_horario(models.TransientModel):

    _name = 'cursos.asignacion_horario'

    asignacion_id = fields.Many2one('cursos.asignacion','horario', required=True)
    seleccionado = fields.Boolean('Sel')
    cupo_disponible = fields.Integer('Cupo Disponible')
    horario_id = fields.Many2one('cursos.horario','horario', required=True)
    cupo = fields.Integer(related='horario_id.cupo', store=False)
    dia = fields.Selection(related='horario_id.dia', store=False)
    hora_inicio = fields.Float(related='horario_id.hora_inicio', store=False)
    hora_fin = fields.Float(related='horario_id.hora_fin', store=False)
    congelados = fields.Integer('Congelados')
    reposicion = fields.Boolean('Reposición')


class asistencia(models.Model):

    _name = 'cursos.asistencia'

    fecha = fields.Date('Fecha')
    alumno_id = fields.Many2one('res.partner','Alumno')
    horario_id = fields.Many2one('cursos.horario','Horario')
    estado_asistencia = fields.Selection([
        ('si', 'Si Llego'),
        ('no', 'No Llego'),
        ('tarde', 'Llego tarde')], 'Tipo Asistencia')
    reposicion = fields.Boolean('Reposición')

class asistencia_wizard(models.TransientModel):

    _name = 'cursos.asistencia_wizard'

    fecha = fields.Date('Fecha', required=True)
    sede_id = fields.Many2one('cursos.sede','Sede', required=True)
    hora = fields.Float('Hora', required=True)
    dia = fields.Selection(dias_array, 'Dia', required=True)
    asistencias_alumnos = fields.Many2many('cursos.asistencia_wizard_alumno','asistencia_wizard_alumnos_rel1', 'asistencia_wizard_id','asistencia_wizard_alumno_id', 'Alumnos')

    def buscar_alumnos(self):
        historiales_reposicion = self.env['cursos.historial'].search([('horario_id.curso_id.sede_id','=',self.sede_id.id),('fecha_inicio','=',self.fecha),('fecha_fin','=',self.fecha),('horario_id.dia','=',self.dia),('reposicion','=',True),('alumno_id','!=',False)])
        # historiales_reposicion = self.env['cursos.historial'].search([('horario_id.hora_inicio','=',self.hora),('horario_id.curso_id.sede_id','=',self.sede_id.id),('horario_id.dia','=',self.dia),('reposicion','=',True)])
        # historiales = self.env['cursos.historial'].search([('horario_id.hora_inicio','=',self.hora),('horario_id.curso_id.sede_id','=',self.sede_id.id),('fecha_fin','=',False),('horario_id.dia','=',self.dia)])
        historiales = self.env['cursos.historial'].search([('horario_id.curso_id.sede_id','=',self.sede_id.id),('fecha_fin','=',False),('horario_id.dia','=',self.dia),('alumno_id','!=',False)])
        historiales_fecha_incio_fin = self.env['cursos.historial'].search([('horario_id.curso_id.sede_id','=',self.sede_id.id),('fecha_inicio','>=',self.fecha),('fecha_fin','<=',self.fecha),('horario_id.dia','=',self.dia),('alumno_id','!=',False)])
        historiales_horario = []
        congelados = []
        for historial in historiales:
            if historial.horario_id.hora_inicio == self.hora:
                historiales_horario.append(historial)
        for historial in historiales_fecha_incio_fin:
            if historial.horario_id.hora_inicio == self.hora:
                historiales_horario.append(historial)                    
        historiales_reposicion_lista = []
        for historial in historiales_reposicion:
            if historial.horario_id.hora_inicio == self.hora:
                historiales_reposicion_lista.append(historial)
        historiales = historiales_horario + historiales_reposicion_lista
        historiales2 = sorted(historiales, key=lambda hist: hist.nombre_alumno)
        historiales_congelamientos = self.env['cursos.congelamiento'].search([('horario_id.dia','=',self.dia)])
        for congelado in historiales_congelamientos:
            if congelado.horario_id.hora_inicio == self.hora:
                congelados.append(congelado)
        alumnos_array = []
        # fecha_hoy = datetime.datetime.now().strftime("%Y-%m-%d")
        fecha_asistencia = datetime.datetime.strptime(self.fecha,"%Y-%m-%d")
        # Limpiar detalle de asistencias alumnos
        for aa in self.asistencias_alumnos:
            self.write({'asistencias_alumnos': [(2,aa.id)]})

        for historial in historiales2:
            agregar = True
            for congelamiento in congelados:
                if congelamiento.alumno_id.id == historial.alumno_id.id and congelamiento.horario_id.id == historial.horario_id.id:
                    fecha_c_f = datetime.datetime.strptime(congelamiento.fecha_congelamiento, "%Y-%m-%d")
                    fecha_c_i = datetime.datetime.strptime(congelamiento.fecha_inicio_congelamiento, "%Y-%m-%d")
                    if (fecha_c_f >= fecha_asistencia) & (fecha_c_i <= fecha_asistencia):
                        agregar = False
            if agregar:
                wizard_alumno =  {'alumno_id':historial.alumno_id.id, 'horario_id':historial.horario_id.id , 'reposicion': historial.reposicion}
                wizard_alumno_id = self.env['cursos.asistencia_wizard_alumno'].create(wizard_alumno)
                w_alumno = (4,wizard_alumno_id.id)
                alumnos_array.append(w_alumno)

        self.write({'asistencias_alumnos': alumnos_array})

        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cursos.asistencia_wizard',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def guardar_asistencia(self):
        for asistencia_alumno in self.asistencias_alumnos:
            asistencia =  {'fecha':self.fecha, 'alumno_id':asistencia_alumno.alumno_id.id, 'horario_id':asistencia_alumno.horario_id.id, 'estado_asistencia':asistencia_alumno.estado_asistencia, 'reposicion': asistencia_alumno.reposicion }
            asistencia_id = self.env['cursos.asistencia'].create(asistencia)

        return {'type': 'ir.actions.act_window_close'}

class asistencia_wizard_alumno(models.TransientModel):

    _name = 'cursos.asistencia_wizard_alumno'

    alumno_id = fields.Many2one('res.partner','Alumno', readonly= True)
    nombre = fields.Char(related='alumno_id.name', store=False, readonly= True)
    horario_id = fields.Many2one('cursos.horario','Horario')
    curso = fields.Char(related='horario_id.curso_id.name',store=False, readonly= True)
    estado_asistencia = fields.Selection([
        ('si', 'Si Llego'),
        ('no', 'No Llego'),
        ('tarde', 'Llego tarde')], 'Tipo Asistencia', required=True, default='si')
    reposicion = fields.Boolean('Reposición')

class evento(models.Model):

    _name = 'cursos.evento'

    fecha_inicio = fields.Datetime('Fecha Inicio', required=True)
    alumnos = fields.Char(compute='_get_alumnos')
    fecha_fin = fields.Datetime('Fecha Fin', required=True)
    horario_id = fields.Many2one('cursos.horario','Horario', required=True)
    curso_id = fields.Many2one(related='horario_id.curso_id', store=True)
    curso_name = fields.Char(related='horario_id.curso_id.name', store=True)
    profesores = fields.Many2many(related='horario_id.profesores', store=False)
    historial_curso_ids = fields.One2many(related='horario_id.historial_curso_ids', store=False)

    @api.multi
    def name_get(self):
        res = []
        for ev in self:
            res.append((ev.id, ev.curso_name + ", " + ev.fecha_inicio + " - " + ev.fecha_fin))
        return res

    def  _get_alumnos(self):
        for evento in self:
            alumnos_lista = []
            for linea in evento.historial_curso_ids:
                alumnos_lista.append(linea.alumno_id.name)
            evento.alumnos =', '.join(alumnos_lista)

class congelamiento(models.Model):
    _name = 'cursos.congelamiento'

    alumno_id = fields.Many2one('res.partner','Alumno')
    horario_id = fields.Many2one('cursos.horario','Horario')
    fecha_congelamiento = fields.Date('Fecha fin congelamiento')
    fecha_inicio_congelamiento = fields.Date('Fecha inicio congelamiento')
    razon_congelamiento = fields.Char('Razón congelamiento')
