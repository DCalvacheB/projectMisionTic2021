from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField,PasswordField,BooleanField, validators, FileField
from wtforms.fields.html5 import EmailField
import email_validator
from wtforms.validators import InputRequired,DataRequired, Length, Email
from flask_wtf.file import FileField, FileAllowed, FileRequired


class FormInicio(FlaskForm):
    #usuario = EmailField('Usuario', validators=[DataRequired(message = "Por favor completa este campo")])
    #email = StringField('Correo', validators=[InputRequired(message = "Por favor completa este campo"), Email(message='Ingresa un correo')])
    idtrabajo = IntegerField('ID', validators=[InputRequired(message = "Por favor completa este campo")])
    contraseña = PasswordField('Contraseña', validators=[InputRequired(message = "Por favor completa este campo"), Length(min=8,
    message='La contraseña debe tener una longitud de mínimo 8 caracteres')])
    recordar = BooleanField('Recordar Usuario')

class RegisterUser(FlaskForm):
    #usuario = EmailField('Usuario', validators=[DataRequired(message = "Por favor completa este campo")])
    idtrabajo = IntegerField('idtrabajo', validators=[InputRequired()])
    nombre = StringField('Nombre', validators=[InputRequired(), Length(min=5, message='El nombre debe tener mínimo de 5 caracteres')])
    email = StringField('Correo', validators=[InputRequired(message = "Por favor completa este campo"), Email(message='Ingresa un correo')])
    contraseña = PasswordField('Contraseña', validators=[InputRequired(message = "Por favor completa este campo"), Length(min=8,
    message='La contraseña debe tener una longitud de mínimo 8 caracteres')])
    admin = BooleanField('Administrador')
    
class ProductoForm(FlaskForm):
    idProd = IntegerField('id', validators=[DataRequired()])
    nombre = StringField('nombre', validators=[DataRequired()])
    #marca = StringField('marca', validators=[DataRequired()])
    precio = IntegerField('precio',validators=[DataRequired()])
    cantidad = IntegerField('cantidad',validators=[DataRequired()])
    imagen = FileField('image', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    
class ContactoForm(FlaskForm):
    correode = EmailField('Usuario', validators=[DataRequired(message = "Por favor completa este campo")])
    asunto = StringField('nombre', validators=[DataRequired()])
    mensaje = StringField('Nombre', validators=[InputRequired(), Length(min=5, max= 200)])


class CuentaForm(FlaskForm):
    idProd = IntegerField('idProd', validators=[DataRequired()])
    cantidad = IntegerField('cantidad', validators=[DataRequired()])
    idCajero = IntegerField('idCajero', validators=[DataRequired()])
    