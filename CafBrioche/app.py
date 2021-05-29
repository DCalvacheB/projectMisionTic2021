from flask import Flask, render_template, request, flash, redirect, url_for, make_response, session, debughelpers
import utils, yagmail, os
import sqlite3
from sqlite3 import Error
from forms import FormInicio, RegisterUser, ProductoForm, ContactoForm, CuentaForm
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import BadRequestKeyError
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_uploads import configure_uploads, IMAGES, UploadSet
from io import BytesIO
import base64
from PIL import Image
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///DB/CafeteriaBrioche.db'
app.config['SECRET_KEY'] = 'asdkjsakd_dsfdsfdf!secretsecret'

Bootstrap(app)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'indexF'
login_manager.login_message = 'Por favor inicia sesión'

s = URLSafeTimedSerializer('DontTellAnyOne!')

app.config.update(dict(
    MAIL_SERVER= 'smtp.gmail.com',
    MAIL_PORT = 465,
    MAIL_USE_SSL = True,
    MAIL_USE_TLS = False,
    MAIL_USERNAME = 'cafeteriabriochemanagement@gmail.com',
    MAIL_PASSWORD = 'CafeBrioche2020',
    MAIL_ASCII_ATTACHMENTS = True,
    MAIL_DEFAULT_SENDER = 'cafeteriabriochemanagement@gmail.com'
))

mail = Mail(app)
@app.route('/Cajero/NuevaCuenta', methods=['POST'])
def NuevaCuenta():
    idcajero = request.form['idcajero']
    cajero = sql_get_idtrabajo_cuenta(idcajero)
    idEncontrado = cajero[0]
    sql_create_cuenta(idEncontrado)
    flash('idEncontrao: {} \nIdtrabajo: {} \nNombre: '.format(idEncontrado, idcajero))
    return redirect(url_for('user_caja'))

@app.route('/editCuenta', methods=['POST'])
def editCuenta():
    cuentas = sql_select_cuentas()
    print(len(cuentas))
    try: 
        idVenta = len(cuentas)+1
    except:
        idVenta=1
    print(idVenta)
    prodsIds = request.form['prodsIds']
    total = request.form['total']
    prodsIds = listToString(prodsIds)
    x = prodsIds.split(",")
    idempleado = request.form['idempleado']
    h = ''
    for i in range(len(x)-1):
        idProd = x[i]
        sql_create_cuenta(idempleado)
        sql_addinto_cuenta(idProd, idempleado, idVenta)
        delete_empty_cuentas()
    create_descripcion(total, prodsIds, idVenta, idempleado)
    flash ('Cuenta creada con exito')
    return redirect(url_for('user_caja'))

def listToString(s):
    str1 = ""
    for ele in s:  
        str1 += ele
    return str1 


@app.route('/Confirmacion/confirm_email/<token>')
def confirm_email(token):
    try: 
        email = s.loads(token, salt = 'email-confirm', max_age = 86400)
    except SignatureExpired:
        flash('Ups! Ese link expiró!')
        return render_template("Error.html", titulo="Error en el proceso - Cafetería Brioche")
    user = Cajeros.query.filter_by(correo=email).first()
    user.confirmacion = 1
    db.session.commit()
    flash('{},Has confirmado tu cuenta con éxito!'.format(user.nombre))
    return render_template("ProcesoExitoso.html", titulo = "Exito! - Cafetería Brioche")


@app.route('/recuperar_cont/<token>', methods=['POST', 'GET'])
def recuperar_cont(token):
    try:
        email = s.loads(token, salt = 'recover-pswrd', max_age = 86400)
    except:
        abort(404)
    
    if request.method == "POST":
        usuario = Cajeros.query.filter_by(correo=email).first_or_404()
        contA = request.form['contA']
        contB = request.form['contB']
        hash_pswrd = generate_password_hash(contA)
        usuario.contrasena = hash_pswrd
        db.session.commit()
        flash('Tu contrasena ha sido actualizada')
        return redirect(url_for('indexF'))
    return render_template("nuevaCont.html", token=token, user = usuario.nombre, titulo="Nueva contraseña - Cafetería Brioche")


#-----------------------------------------------------------------------------------
#------------decorador de flask_login-----------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return Cajeros.query.get(int(user_id))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('indexF'))

#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
@app.route('/')
def indexF():
    form = FormInicio()
    return render_template('index.html', titulo="Inicio de sesion - Cafetería Brioche", form = form)

@app.route('/Contactanos')
def contactanos():
    form = ContactoForm()
    return render_template('contactanos.html', form = form, titulo="Contáctenos - Cafetería Brioche")

@app.route('/enviarMsg', methods=['POST'])
def enviarMsg():
    form = ContactoForm()
    correode = form.correode.data
    asunto = form.asunto.data
    mensaje = form.mensaje.data
    nuevoMsg = Mensajes(de=form.correode.data, asunto= form.asunto.data, 
        mensaje=form.mensaje.data)
    db.session.add(nuevoMsg)
    db.session.commit()
    flash('Mensaje enviado con éxito! Muchas Gracias por tu opinión')
    return render_template("Procesoexitoso.html", titulo="Proceso exitoso! - Cafetería Brioche")

@app.route('/Admin')
@login_required
def Admin():
    productos = Productos.query.all()
    usuarios = sql_select_usuarios()
    return render_template('vistaAdmin.html',usuario_nombre=current_user.nombre,
                    productos = productos, usuarios = usuarios, res= None, resProd=None, titulo ="Administrador - Cafetería Brioche")

@app.route('/Admin/ResultadoBusquedaProd', methods=['POST'])
@login_required
def ResultadoProd(resProd = None):
    productos = Productos.query.all()
    usuarios = sql_select_usuarios()
    entrada = request.form['entrada']
    resProd = sql_select_productos(entrada)
    if(len(resProd)==0):
        flash('No hay resultados para tu búsqueda de productos')
        return redirect(url_for('Admin'))
    return render_template('vistaAdmin.html',usuario_nombre=current_user.nombre,
                    productos = productos, usuarios = usuarios, res = None, resProd = resProd)

@app.route('/Admin/ResultadoBusqueda', methods=['POST'])
@login_required
def Resultado(res = None):
    productos = Productos.query.all()
    usuarios = sql_select_usuarios()
    entrada = request.form['entrada']
    res = sql_select_usuarios(entrada)
    if(len(res)==0):
        flash('No hay resultados para tu búsqueda de Empleados')
        return redirect(url_for('Admin'))
    return render_template('vistaAdmin.html',usuario_nombre=current_user.nombre,
                    productos = productos, usuarios = usuarios, res = res, reProd= None)

@app.route('/Cajero/ResultadoBusquedaProd', methods=['POST'])
@login_required
def ResultadoProdCajero(resProd = None):
    productos = Productos.query.all()
    entrada = request.form['entrada']
    resProd = sql_select_productos(entrada)
    if(len(resProd)==0):
        flash('No hay resultados para tu búsqueda de productos')
        return redirect(url_for('user_caja'))
    return render_template('vistaCajero.html',usuario_nombre=current_user.nombre,
                    productos = productos, usuarios = usuarios, res = None, resProd = resProd)

@app.route('/user')
@login_required
def user_caja():
    productos = Productos.query.all()
    cuentas = sql_select_cuentas()
    cajero = Cajeros.query.filter_by(nombre=current_user.nombre).first()
    return render_template('vistaCajero.html',usuario_nombre=current_user.nombre, idEmp=cajero.id,
    productos = productos, cuentas = cuentas, resProd = None)



@app.route('/RecuperarCont')
def recuperarCont():
    return render_template('RecuperarCont.html',titulo="Recupera tu contraseña - Cafetería Brioche")

@app.route('/VentasRegistradas')
@login_required
def VentasRegistradasCajero():
    cuentas = sql_select_cuentas()
    return render_template('VentasRegistradas.html', cuentas = cuentas,titulo="Ventas registradas - Cafetería Brioche")

@app.route('/nuevaVenta')
@login_required
def nuevaVenta():
    texts = ''
    idProductos = []
    x,y  =[],[]
    cuentas = sql_select_DC()
    return render_template('nuevaVenta.html', cuentas= cuentas, titulo="Ventas registradas - Cafetería Brioche")

@app.route('/login/UsuarioNuevo')
@app.route('/UsuarioNuevo')
@login_required
def nuevoUsu():
    form=RegisterUser()
    return render_template('NuevoUsuario.html', form = form, titulo="Nuevo usuario - Cafetería Brioche")

@app.route('/ProductoNuevo')
@app.route('/login/ProductoNuevo')
@login_required
def ProductoNuevo():
    form = ProductoForm()
    return render_template('NuevoProd.html', form = form,titulo="PRoducto nuevo - Cafetería Brioche")

@app.route('/productos/')
@login_required
def productos(): 
  productos = Productos.query.all()
  return render_template('/products.html', productos = productos,titulo="Productos existentes - Cafetería Brioche")

@app.route('/usuarios/')
@login_required
def usuarios(): 
  usuarios = sql_select_usuarios()
  return render_template('/usuarios.html', usuarios = usuarios,titulo="Usuarios registrados - Cafetería Brioche")

#--------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------

@app.route("/getimg/<prodid>")
def obtener_img(prodid):
    produc = Productos.query.filter_by(id=prodid).first()
    image_binary = produc.imagen
    response = make_response(image_binary)
    response.headers.set('Content-Type', 'image/png')
    response.headers.set('Content-Disposition', 'attachment', filename='%s.png' % prodid)
    return response

@app.route('/Confirmacion', methods=['POST'])
def envioCorreoRC(correo = None):
    if request.method == 'POST':
        #metodo post para hacer validaciones(procesar las solicitudes y redireccionar segun validacion),
        email = request.form['correo']     #obtener los campos del formulario
        if utils.isEmailValid(email):
            user = Cajeros.query.filter_by(correo=email).first()
            if user:    
                token = s.dumps(email, salt = 'recover-pswrd')
                msg = Message('Recuperar contraseña - Cafetería Brioche', recipients = [email])
                link = url_for('recuperar_cont', token = token, _external = True)
                msg.body = 'El link para recuperar tu contraseña es {}'.format(link)
                mail.send(msg)
                flash('Se ha enviado un correo a {}'.format(email))
                return redirect(url_for('indexF'))
            else: 
                flash('Ups no existe tu correo en nuestras bases de datos')
                return render_template("Error.html",titulo="Error - Cafetería Brioche")
        else:
            return 'Error email invalido'
    else:
        flash('Ups no existe tu correo en nuestras bases de datos')
        return render_template('Error.html',titulo="Error - Cafetería Brioche")


@app.route('/login', methods=['POST'])
def login():
    form = FormInicio()
    if(form.validate_on_submit()):
        user = Cajeros.query.filter_by(idtrabajo=form.idtrabajo.data).first()
        if not user:
            flash('Ups! Revisa tu correo e intenta de nuevo.')
            return render_template("index.html", form = form)

        if 'next' in session:
            next = session['next']

            if is_safe_url(next):
                return redirect(next)

        if not(check_password_hash(user.contrasena, form.contraseña.data)):
            flash('Ups! Revisa tu contraseña e intenta de nuevo.')
            return render_template("index.html", form = form)
        
        login_user(user, remember=form.recordar.data)
        next = request.args.get('next')

        if user.admin:
            flash(form.recordar.data)
            return redirect(url_for('Admin'))
        else:
            flash(form.recordar.data)
            return redirect(url_for('user_caja'))
            
    else:
        flash('Ups! Por favor intenta de nuevo.')
        return render_template("index.html", form = form)
    
@app.route('/AddUsuarioNuevo',methods=["POST"])
def AddnuevoUsu():
    form = RegisterUser()
    if form.validate_on_submit():
        email = form.email.data
        hash_pass= generate_password_hash(form.contraseña.data)
        cajero = Cajeros(idtrabajo=form.idtrabajo.data, nombre= form.nombre.data, 
        correo=form.email.data, contrasena=hash_pass, admin = form.admin.data)
        db.session.add(cajero)
        db.session.commit()
        flash('Usuario creado con éxito!')
        token = s.dumps(email, salt = 'email-confirm')
        msg = Message('Confirmar tu cuenta', recipients = [email])
        link = url_for('confirm_email', token = token, _external = True)
        msg.body = 'Tu link es {}'.format(link)
        mail.send(msg)
        db.session.commit()
        flash('Se ha enviado un correo de confirmacion a {}'.format(email))
        return redirect(url_for('nuevoUsu'))
    else:
        return render_template("Error.html")
        

@app.route('/AddProdNuevo',methods=["POST"])
def AddnuevoProd():
    form = ProductoForm()
    if request.method == "POST":
        idProd=request.form['idProd']
        
        encontrado = Productos.query.filter_by(idProd=idProd).first()
        if encontrado:
            flash('Ese id del producto ya existe, por favor escoje otro')
            return redirect(url_for('Admin'))

        nombreProd = request.form['nombre']
        cantProd = request.form['cantidad']
        precio = request.form['precio']
        file_img = request.files['inputFile']
        newfile = Productos(idProd=idProd,  nombre = nombreProd, cantidad= cantProd, precio = precio, imagen = file_img.read())
        db.session.add(newfile)
        db.session.commit()
        flash('Agregado con éxito')
        return redirect(url_for('Admin'))
    flash('Oops hubo un error!')
    return redirect(url_for('ProductoNuevo'))

@app.route('/nuevoCorreo/edit_email/<token>')
def edit_email(token):
    try: 
        email = s.loads(token, salt = 'edit-email', max_age = 86400)
    except SignatureExpired:
        flash('Ups! Ese link expiró!')
        return render_template("Error.html")
    user = Cajeros.query.filter_by(correo=email).first()
    user.confirmacion = 1
    db.session.commit()
    flash('{}, has confirmado tu el cambio de correo de tu cuenta con éxito!'.format(user.nombre))
    return render_template("ProcesoExitoso.html")
    
@app.route('/edit', methods=['POST'])
def editUser():
    try:
        try:
            borrar = request.form['borrarUser']
        except BadRequestKeyError:
            borrar = 0

        idtrabajo = request.form['idtrabajo']
        nombreU = request.form['nombreU']
        correoU = request.form['correoU']
        user = Cajeros.query.filter_by(idtrabajo=idtrabajo).first()
        
        if(user.correo!=correoU and user.nombre==nombreU):
            user.correo = correoU
            user.confirmacion = 0
            db.session.commit()
            token = s.dumps(correoU, salt = 'edit-email')
            msg = Message('Confirmar tu cuenta - Cafeteria Brioche', recipients = [correoU])
            link = url_for('edit_email', token = token, _external = True)
            msg.body = '<h1>Has cambiado el correo asociado a tu cuenta en Cafetería Brioche</h1>. <br>Utiliza este link para confirmar tu cuenta de nuevo:<br> {}'.format(link)
            mail.send(msg)
            flash('Se ha editado el correo de {}'.format(nombreU))
        elif(user.correo==correoU and user.nombre!=nombreU):
            user.nombre=nombreU
            db.session.commit()
            flash('Se ha editado el nombre de {}'.format(nombreU))
        elif user.correo==correoU and user.nombre==nombreU and borrar=='1':
            db.session.delete(user)
            db.session.commit()
            flash('El usuario fue borrado con éxito!')
        elif user.correo==correoU and user.nombre==nombreU:
            flash('No hiciste ningún cambio!')
        else:
            user.correo = correoU
            user.nombre=nombreU
            db.session.commit()
            flash('Se ha editado el correo y el nombre de {}'.format(nombreU))
        
        

    except AttributeError:
        flash('Ups, no has escogido nada para editar')
    
    return redirect(url_for('Admin'))

@app.route('/editProd', methods=['POST'])
def editProd():
    try:
        try:
            borrar = request.form['borrarProd']
        except BadRequestKeyError:
            borrar = 0
        
        idProd = request.form['idProd']
        nombreProd = request.form['nombreProd']
        cantProd = request.form['cantProd']
        cantProdV = request.form['cantProdV']
        precioProd = request.form['precioProd']
        precioProdV = request.form['precioProdV']
        producto = Productos.query.filter_by(idProd=idProd).first()
        
        if(borrar == 0):
            if(nombreProd != producto.nombre and cantProd == cantProdV and precioProd == precioProdV):
                producto.nombre = nombreProd
                db.session.commit()
                flash('Se ha actualizado el nombre del producto {}'.format(idProd))
            elif(nombreProd == producto.nombre and cantProd != cantProdV and precioProd == precioProdV):
                producto.cantidad = cantProd
                db.session.commit()
                flash('Se ha actualizado la cantidad del producto {}'.format(idProd))
            elif(nombreProd == producto.nombre and cantProd == cantProdV and precioProd != precioProdV):
                producto.precio = precioProd
                db.session.commit()
                flash('Se ha actualizado el precio del producto {}'.format(idProd))
            
            elif(nombreProd != producto.nombre and cantProd != cantProdV and precioProd == precioProdV):
                producto.nombre = nombreProd
                producto.cantidad = cantProd
                db.session.commit()
                flash('Se ha actualizado el nombre y la cantidad del producto {}'.format(idProd))
            elif(nombreProd != producto.nombre and cantProd == cantProdV and precioProd != precioProdV):
                producto.nombre = nombreProd
                producto.precio = precioProd
                db.session.commit()
                flash('Se ha actualizado el nombre y el precio del producto {}'.format(idProd))
            elif(nombreProd == producto.nombre and cantProd != cantProdV and precioProd != precioProdV):
                producto.cantidad = cantProd
                producto.precio = precioProd
                db.session.commit()
                flash('Se ha actualizado la cantidad y el precio del producto {}'.format(idProd))
            elif(nombreProd == producto.nombre and cantProd == cantProdV and precioProd == precioProdV):
                flash('No se ha hecho ningún cambio')
            else:
                producto.nombre = nombreProd
                producto.cantidad = cantProd
                db.session.commit()
                flash('Se ha actualizado el nombre, la cantidad y el precio del producto {}'.format(idProd))
        else:
            db.session.delete(producto)
            db.session.commit()
            flash('Se ha eliminado el producto con exito')

    except AttributeError:
        flash('Ups, no has escogido nada para editar')

    return  redirect(url_for('Admin'))
    

@app.route('/editImg', methods = ['POST'])
def editImg():
    idProdImg = request.form['idProdImg']
    newImgEdit = request.files['newImgEdit']
    img = newImgEdit.read()
    producto = Productos.query.filter_by(idProd=idProdImg).first()
    producto.imagen = img
    db.session.commit()
    flash('Se ha cambiado la imagen con éxito')
    return redirect(url_for('Admin'))
    

@app.route('/buscarProd', methods=['POST'])
def buscarProd():
    entrada = request.form['entrada']
    producto = Productos.query.filter_by(idProd=entrada).first()
    flash('Producto encontrado')
    return redirect(url_for('Admin'))


@app.route('/mensajes')
def listarMsjs():
    mensajes = Mensajes.query.all()
    return render_template("Mensajes.html", mensajes=mensajes)
#-----------------------------------------------------------
#---------------------Conexión a DB(deprecated)-------------------------
#-----------------------------------------------------------


def Conexion():
    try:
        con=sqlite3.connect('DB/CafeteriaBrioche.db')
        return con
    except Error:
        print(Error)

#--------- Para listar los productos-------------
def sql_select_productos(entrada = None):
    if(entrada is not None):
        strsql = "select * from productos where idProd = {};".format(entrada)
        con = Conexion()
        cursorObj = con.cursor()
        cursorObj.execute(strsql)
        productos = cursorObj.fetchall()
        return productos
    else:
        strsql = "select * from productos;"
        con = Conexion()
        cursorObj = con.cursor()
        cursorObj.execute(strsql)
        productos = cursorObj.fetchall()
        return productos

def sql_select_usuarios(entrada = None):
    if(entrada is not None):
        strsql = "select * from cajeros where idtrabajo = {};".format(entrada)
        con = Conexion()
        cursorObj = con.cursor()
        cursorObj.execute(strsql)
        usuarios = cursorObj.fetchall()
        return usuarios
    else:
        strsql = "select * from cajeros;"
        con = Conexion()
        cursorObj = con.cursor()
        cursorObj.execute(strsql)
        usuarios = cursorObj.fetchall()
        return usuarios

def sql_select_cuentas():
    strsql = "select * from cuentas;"
    con = Conexion()
    cursorObj = con.cursor()
    cursorObj.execute(strsql)
    cuentas = cursorObj.fetchall()
    return cuentas

def sql_get_idtrabajo_cuenta(entrada):
    strsql = "select id from cajeros where idtrabajo={};".format(entrada)
    con = Conexion()
    cursorObj = con.cursor()
    cursorObj.execute(strsql)
    idtrabajo_cajero = cursorObj.fetchall()
    return idtrabajo_cajero

def sql_create_cuenta(entrada):
    strsql = "INSERT INTO cuentas (idCajero) values({});".format(entrada)
    con=Conexion()
    cursorObj=con.cursor() # que es?
    cursorObj.execute(strsql)
    con.commit()
    con.close()
    return

def sql_addinto_cuenta(idProd, idCajero, idVenta):
    strsql = "insert into cuentas (idProd, idCajero, idVenta) values ({}, {}, {});".format(idProd, idCajero, idVenta)
    con=Conexion()
    cursorObj=con.cursor() # que es?
    cursorObj.execute(strsql)
    con.commit()
    con.close()
    return

def delete_empty_cuentas():
    strsql = "delete from cuentas where idProd is NULL;"
    con=Conexion()
    cursorObj=con.cursor() # que es?
    cursorObj.execute(strsql)
    con.commit()
    con.close()
    return

def create_descripcion(total, descripcion, idVenta, idempleado):
    strsql = "INSERT INTO descripciones (fecha, total, descripcion, idVenta,idempleado) values(CURRENT_TIMESTAMP,{},'{}',{},{});".format(total, descripcion, idVenta, idempleado)
    con=Conexion()
    cursorObj=con.cursor() # que es?
    cursorObj.execute(strsql)
    con.commit()
    con.close()
    return

def update_descripcion(entrada):
    strsql = "update descripciones set idCuenta = {} where id = {};".format(entrada)
    con=Conexion()
    cursorObj=con.cursor() # que es?
    cursorObj.execute(strsql)
    con.commit()
    con.close()
    return

def sql_select_DC():
    strsql="select * from descripciones;"
    con = Conexion()
    cursorObj = con.cursor()
    cursorObj.execute(strsql)
    cuentas = cursorObj.fetchall()
    return cuentas


##-----------------------------SQLAlchemy-------------------------------------
#---------(para manejar usuarios(admin o meseros/cajeros) y productos)---------

class Cajeros(UserMixin, db.Model):
    __tablename__ = 'cajeros'
    id = db.Column(db.Integer, primary_key=True)
    idtrabajo = db.Column(db.Integer, unique = True)
    nombre = db.Column(db.String)
    correo = db.Column(db.String)
    contrasena = db.Column(db.String)
    admin = db.Column(db.Boolean)
    confirmacion = db.Column(db.Boolean)
    def get_reset_token(self):
        return s.dumps(self.idtrabajo, salt = 'recover-pswrd')
        
    @staticmethod
    def verify_sent_token(token):
        try:
            email = s.loads(token, salt = 'recover-pswrd', max_age = 86400)
        except:
            return None

        User = Cajeros.query.get(email)
        return User

    def __repr__(self):
        return f"Cajeros('{self.idtrabajo}', '{self.nombre}','{self.correo}', '{self.contrasena}', '{self.admin}', '{self.confirmacion}')"
        

class Productos(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    idProd = db.Column(db.Integer, unique = True)
    nombre = db.Column(db.String)
    precio = db.Column(db.Integer)
    cantidad = db.Column(db.Integer)
    imagen = db.Column(db.LargeBinary)

    

class Mensajes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    de = db.Column(db.Integer, unique = True)
    asunto = db.Column(db.String)
    mensaje = db.Column(db.String)



    #--------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port =80)