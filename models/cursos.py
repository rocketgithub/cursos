# -*- coding: utf-8 -*-

from odoo import api, models, tools, fields

import logging

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
        ('sabado', 'Sábado')], 'Dia')
    profesores = fields.Many2many('res.partner','horario_partner_rel1', 'horario_id','partner_id', 'Profesores')
#    alumnos = fields.Many2many('res.partner','horario_partner_rel2', 'horario_id','partner_id', 'Alumnos')
    hora_inicio = fields.Float('Hora Inicio')
    hora_fin = fields.Float('Hora Fin')
    historial_curso_ids = fields.One2many('cursos.historial','horario_id', domain=[('fecha_fin','=',False)],string = 'Historial' )

class historial(models.Model):

    _name = 'cursos.historial'

    fecha_inicio = fields.Date('Fecha Inicio')
    fecha_fin = fields.Date('Fecha Fin')
    alumno_id = fields.Many2one('res.partner','Alumno')
    horario_id = fields.Many2one('cursos.horario','Horario')
    congelado = fields.Boolean('Congelado')

class asignacion(models.TransientModel):

    _name = 'cursos.asignacion'

    curso_id = fields.Many2one('cursos.curso','Curso')
#    horario_ids = fields.One2many('cursos.horario','curso_id', string = 'Horarios' )
#    horarios = fields.Many2many('cursos.horario','asignacion_horario_rel1', 'asignacion_id','horario_id', 'Horarios')
    alumno_id = fields.Many2one('res.partner','Alumno')
    fecha_inicio = fields.Date('Fecha Inicio')
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
                for historial in historiales:
                    if historial.congelado:
                        congelados = congelados +1
                asign_horario =  {'seleccionado': False, 'cupo_disponible':cupo_disp, 'horario_id':horario.id, 'congelados': congelados }
                asign_horario_id = self.env['cursos.asignacion_horario'].create(asign_horario)
                logging.warn(asign_horario_id.id)
                h_cupo = (4,asign_horario_id.id)
                horarios_array.append(h_cupo)

        logging.warn(horarios_array)
        self.write({'horarios_asignaciones': horarios_array})
 #       logging.warn(self.horarios)
#        logging.warn("Despues del write")
#        return {
#            "type": "ir.actions.do_nothing",
#        }
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
#        logging.warn(self.horarios[0].id)
        for a_horario in self.horarios_asignaciones:
            logging.warn(a_horario.seleccionado)
            if a_horario.seleccionado:
                historial =  {'fecha_inicio':self.fecha_inicio, 'fecha_fin':False, 'alumno_id':self.alumno_id.id, 'horario_id':a_horario.horario_id.id }
                hist_id = self.env['cursos.historial'].create(historial)
                logging.warn("DESPUES DE CREATE")
                logging.warn(hist_id)
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

class asignacion_horario(models.TransientModel):

    _name = 'cursos.asignacion_horario'

    seleccionado = fields.Boolean('Sel')
    cupo_disponible = fields.Integer('Cupo Disponible')
    horario_id = fields.Many2one('cursos.horario','horario', required=True)
    cupo = fields.Integer(related='horario_id.cupo', store=False)
    dia = fields.Selection(related='horario_id.dia', store=False)
    hora_inicio = fields.Float(related='horario_id.hora_inicio', store=False)
    hora_fin = fields.Float(related='horario_id.hora_fin', store=False)
    congelados = fields.Integer('Congelados')


class asistencia(models.Model):

    _name = 'cursos.asistencia'

    fecha = fields.Date('Fecha')
    alumno_id = fields.Many2one('res.partner','Alumno')
    horario_id = fields.Many2one('cursos.horario','Horario')

class asistencia_wizard(models.TransientModel):

    _name = 'cursos.asistencia_wizard'

    horario_id = fields.Many2one('cursos.horario','Horario')
    fecha = fields.Date('Fecha')
    asistencias_alumnos = fields.Many2many('cursos.asistencia_wizard_alumno','asistencia_wizard_alumnos_rel1', 'asistencia_wizard_id','asistencia_wizard_alumno_id', 'Alumnos')

    def buscar_alumnos(self):
        logging.warn("BUSCAR ALUMNOS ASIGNADOS EN HORARIO")

class asistencia_wizard_alumno(models.TransientModel):

    _name = 'cursos.asistencia_wizard_alumno'

    alumno_id = fields.Many2one('res.partner','Alumno')
    nombre = fields.Char(related='alumno_id.name', store=False)
