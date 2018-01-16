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
        ('miercoles', 'Miercoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes')], 'Dia')
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

class asignacion(models.TransientModel):

    _name = 'cursos.asignacion'

    curso_id = fields.Many2one('cursos.curso','Curso')
#    horario_ids = fields.One2many('cursos.horario','curso_id', string = 'Horarios' )
    horarios = fields.Many2many('cursos.horario','asignacion_horario_rel1', 'asignacion_id','horario_id', 'Horarios')

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
                h_cupo = (4,horario.id)
                horarios_array.append(h_cupo)

        logging.warn(horarios_array)
#        self.write({'curso_id':self.curso_id.id})
        self.write({'horarios': horarios_array})
        logging.warn(self.horarios)
        logging.warn("Despues del write")
        return {
            "type": "ir.actions.do_nothing",
        }
