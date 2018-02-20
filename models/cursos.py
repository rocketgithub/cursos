# -*- coding: utf-8 -*-

from odoo import api, models, tools, fields

import logging
import datetime

class sede(models.Model):

    _name = 'cursos.sede'

    name = fields.Char('Nombre')

class curso(models.Model):

    _name = 'cursos.curso'

    name = fields.Char('Nombre')
    sede_id = fields.Many2one('cursos.sede','Sede', required=True)

class horario(models.Model):

    _name = 'cursos.horario'

    curso_id = fields.Many2one('cursos.curso','Curso', required=True)
    cupo = fields.Integer('Cupo')
    dia = fields.Selection([
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado')], 'Dia', default='lunes')
    profesores = fields.Many2many('res.partner','horario_partner_rel1', 'horario_id','partner_id', 'Profesores')
#    alumnos = fields.Many2many('res.partner','horario_partner_rel2', 'horario_id','partner_id', 'Alumnos')
    hora_inicio = fields.Float('Hora Inicio')
    hora_fin = fields.Float('Hora Fin')
    historial_curso_ids = fields.One2many('cursos.historial','horario_id', domain=[('fecha_fin','=',False)],string = 'Historial' )

    def name_get(self):
        segundos = self.hora_inicio * 3600
        hora_minutos = str(datetime.timedelta(seconds=segundos))
        logging.warn(hora_minutos[0:5])
        segundos2 = self.hora_fin * 3600
        hora_minutos2 = str(datetime.timedelta(seconds=segundos2))
        return [(self.id, self.curso_id.name + ", "+self.dia+ ", "+hora_minutos[0:5]+ "-"+hora_minutos2[0:5])]

class historial(models.Model):

    _name = 'cursos.historial'

    fecha_inicio = fields.Date('Fecha Inicio')
    fecha_fin = fields.Date('Fecha Fin')
    alumno_id = fields.Many2one('res.partner','Alumno')
    horario_id = fields.Many2one('cursos.horario','Horario')
#    congelado = fields.Boolean('Congelado')
    fecha_congelamiento = fields.Date(related='alumno_id.fecha_congelamiento', store=True)
    nombre_alumno = fields.Char(related='alumno_id.name', store=True)
    fecha_inicio_congelamiento = fields.Date(related='alumno_id.fecha_inicio_congelamiento', store=True)

class asignacion(models.TransientModel):

    _name = 'cursos.asignacion'

    curso_id = fields.Many2one('cursos.curso','Curso', required=True)
#    horario_ids = fields.One2many('cursos.horario','curso_id', string = 'Horarios' )
#    horarios = fields.Many2many('cursos.horario','asignacion_horario_rel1', 'asignacion_id','horario_id', 'Horarios')
    alumno_id = fields.Many2one('res.partner','Alumno', required=True)
    fecha_inicio = fields.Date('Fecha Inicio', required=True)
    horarios_asignaciones = fields.Many2many('cursos.asignacion_horario','asignacion_asignacionhorario_rel1', 'asignacion_id','asignacion_horario_id', 'Horarios')

    def buscar_cupo(self):

        logging.warn("BUSCAR CUPO")
        logging.warn(self.curso_id.name)
        horarios = self.env['cursos.horario'].search([('curso_id','=',self.curso_id.id)])
        logging.warn(horarios)
        horarios_array = []
        for horario in horarios:
            logging.warn(horario)
            historiales = self.env['cursos.historial'].search([('horario_id','=',horario.id),('fecha_fin','=',False)])
            logging.warn(len(historiales))
            # Buscar cupo
            if len(historiales) < horario.cupo:
                logging.warn("ingresar horario ")
                logging.warn(horario)
                cupo_disp = horario.cupo - len(historiales)
                congelados = 0
                fecha_hoy = datetime.datetime.now()
                for historial in historiales:
                    if historial.fecha_congelamiento:
                        fecha_c_f = datetime.datetime.strptime(historial.fecha_congelamiento, "%Y-%m-%d")
                        fecha_c_i = datetime.datetime.strptime(historial.fecha_inicio_congelamiento, "%Y-%m-%d")
                        logging.warn(fecha_c_f)
                        if (fecha_c_f >= fecha_hoy) & (fecha_c_i <= fecha_hoy):
                            congelados = congelados +1
                asign_horario =  {'seleccionado': False, 'cupo_disponible':cupo_disp, 'horario_id':horario.id, 'congelados': congelados }
                asign_horario_id = self.env['cursos.asignacion_horario'].create(asign_horario)
                logging.warn(asign_horario_id.id)
                h_cupo = (4,asign_horario_id.id)
                horarios_array.append(h_cupo)

        logging.warn(horarios_array)
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
        logging.warn("ASIGNAR")
        logging.warn(self.alumno_id)
        for a_horario in self.horarios_asignaciones:
            logging.warn(a_horario.seleccionado)
            if a_horario.seleccionado:
                historial =  {'fecha_inicio':self.fecha_inicio, 'fecha_fin':False, 'alumno_id':self.alumno_id.id, 'horario_id':a_horario.horario_id.id }
                hist_id = self.env['cursos.historial'].create(historial)
                logging.warn("DESPUES DE CREATE")
                logging.warn(hist_id)
        return {'type': 'ir.actions.act_window_close'}

class asignacion_horario(models.TransientModel):

    _name = 'cursos.asignacion_horario'

    seleccionado = fields.Boolean('Sel')
    cupo_disponible = fields.Integer('Cupo Disponible')
    horario_id = fields.Many2one('cursos.horario','horario', required=True,  readonly= True)
    cupo = fields.Integer(related='horario_id.cupo', store=False, readonly= True)
    dia = fields.Selection(related='horario_id.dia', store=False, readonly= True)
    hora_inicio = fields.Float(related='horario_id.hora_inicio', store=False, readonly= True)
    hora_fin = fields.Float(related='horario_id.hora_fin', store=False, readonly= True)
    congelados = fields.Integer('Congelados', readonly= True)


class asistencia(models.Model):

    _name = 'cursos.asistencia'

    fecha = fields.Date('Fecha')
    alumno_id = fields.Many2one('res.partner','Alumno')
    horario_id = fields.Many2one('cursos.horario','Horario')
    estado_asistencia = fields.Selection([
        ('si', 'Si Llego'),
        ('no', 'No Llego'),
        ('tarde', 'Llego tarde')], 'Tipo Asistencia')

class asistencia_wizard(models.TransientModel):

    _name = 'cursos.asistencia_wizard'

#    horario_id = fields.Many2one('cursos.horario','Horario')
    fecha = fields.Date('Fecha', required=True)
    hora = fields.Float('Hora', required=True)
    dia = fields.Selection([
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado')], 'Dia', required=True)
    asistencias_alumnos = fields.Many2many('cursos.asistencia_wizard_alumno','asistencia_wizard_alumnos_rel1', 'asistencia_wizard_id','asistencia_wizard_alumno_id', 'Alumnos')

    def buscar_alumnos(self):
#        f = datetime.datetime.strptime(self.fecha, "%Y-%m-%d")
#        logging.warn(f.weekday())
#        historiales = self.env['cursos.historial'].search([('horario_id','=',self.horario_id.id),('fecha_fin','=',False),('congelado','=',False)])
        historiales = self.env['cursos.historial'].search([('horario_id.hora_inicio','=',self.hora),('fecha_fin','=',False),('horario_id.dia','=',self.dia)])
        logging.warn(historiales)
        historiales2 = sorted(historiales, key=lambda hist: hist.nombre_alumno)
        logging.warn("SORTED ")
        logging.warn(historiales2)
        historiales3 = sorted(historiales2, key=lambda hist: hist.alumno_id.name)
        logging.warn("SORTED 2")
        logging.warn(historiales3)
        alumnos_array = []
        fecha_hoy = datetime.datetime.now()
        # Limpiar detalle de asistencias alumnos
        for aa in self.asistencias_alumnos:
            self.write({'asistencias_alumnos': [(2,aa.id)]})

        for historial in historiales2:
            agregar = True
            if historial.fecha_congelamiento:
                fecha_c_f = datetime.datetime.strptime(historial.fecha_congelamiento, "%Y-%m-%d")
                fecha_c_i = datetime.datetime.strptime(historial.fecha_inicio_congelamiento, "%Y-%m-%d")
                logging.warn(fecha_c_f)
                if (fecha_c_f >= fecha_hoy) & (fecha_c_i <= fecha_hoy):
                    agregar = False

            if agregar:
                wizard_alumno =  {'alumno_id':historial.alumno_id.id, 'horario_id':historial.horario_id.id }
                wizard_alumno_id = self.env['cursos.asistencia_wizard_alumno'].create(wizard_alumno)
                logging.warn(wizard_alumno_id)
                w_alumno = (4,wizard_alumno_id.id)
                alumnos_array.append(w_alumno)

        logging.warn(alumnos_array)
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
        logging.warn("GUARDAR ASISTENCIA")
        for asistencia_alumno in self.asistencias_alumnos:
            asistencia =  {'fecha':self.fecha, 'alumno_id':asistencia_alumno.alumno_id.id, 'horario_id':asistencia_alumno.horario_id.id, 'estado_asistencia':asistencia_alumno.estado_asistencia }
            asistencia_id = self.env['cursos.asistencia'].create(asistencia)
            logging.warn("DESPUES DE CREATE")
            logging.warn(asistencia_id)

        return {'type': 'ir.actions.act_window_close'}

class asistencia_wizard_alumno(models.TransientModel):

    _name = 'cursos.asistencia_wizard_alumno'

    alumno_id = fields.Many2one('res.partner','Alumno', readonly= True)
    nombre = fields.Char(related='alumno_id.name', store=False, readonly= True)
    horario_id = fields.Many2one('cursos.horario','Horario')
    estado_asistencia = fields.Selection([
        ('si', 'Si Llego'),
        ('no', 'No Llego'),
        ('tarde', 'Llego tarde')], 'Tipo Asistencia', required=True, default='si')
