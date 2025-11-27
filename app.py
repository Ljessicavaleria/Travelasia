from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "travelasia-secret-key-2024")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("🔒 Debes iniciar sesión para acceder a esta página", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Configuración de MongoDB Atlas 
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/travelasia_db")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.travelasia_db
    destinos_collection = db.destinos
    usuarios_collection = db.usuarios
    # Test simple de conexión
    db.command('ping')
    print("✅ ¡CONECTADO A MONGODB ATLAS! - TravelAsia")
except Exception as e:
    db = None
    destinos_collection = None
    usuarios_collection = None
    print(f"❌ Error MongoDB: {e}")

# DATOS DE TODOS LOS TOURS PREDEFINIDOS
TOURS_PREDEFINIDOS = {
    "japon": {
        "nombre": "Tour Japón Esencial",
        "pais": "Japón",
        "ciudad": "Tokio, Kioto, Osaka",
        "duracion": "10 días",
        "precio_base": 1500,
        "incluye": ["Hoteles 4*", "Vuelos internos", "Guía turístico", "Desayunos"],
        "imagen": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=600&q=80",
        "descripcion": "Descubre lo mejor de Japón: desde el moderno Tokio hasta los templos ancestrales de Kioto."
    },
    "tailandia": {
        "nombre": "Aventura Tailandia",
        "pais": "Tailandia", 
        "ciudad": "Bangkok, Phuket, Chiang Mai",
        "duracion": "12 días",
        "precio_base": 1200,
        "incluye": ["Hoteles 4*", "Tours incluidos", "Algunas comidas", "Transporte"],
        "imagen": "https://images.unsplash.com/photo-1552465011-b4e21bf6e79a?w=600",
        "descripcion": "Playas paradisíacas, templos budistas y la vibrante vida nocturna de Bangkok."
    },
    "vietnam": {
        "nombre": "Vietnam Clásico",
        "pais": "Vietnam",
        "ciudad": "Hanoi, Halong Bay, Ho Chi Minh",
        "duracion": "9 días",
        "precio_base": 900,
        "incluye": ["Hoteles 3-4*", "Crucero en Halong Bay", "Todas las comidas", "Guía local"],
        "imagen": "https://images.unsplash.com/photo-1583417319070-4a69db38a482?w=600",
        "descripcion": "Explora la rica historia y paisajes espectaculares de Vietnam."
    },
    "china": {
        "nombre": "Gran Tour de China",
        "pais": "China",
        "ciudad": "Beijing, Shanghai, Gran Muralla",
        "duracion": "14 días",
        "precio_base": 1100,
        "incluye": ["Hoteles 4*", "Entradas a atracciones", "Tren bala", "Guía español"],
        "imagen": "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=600",
        "descripcion": "Descubre la milenaria cultura china y sus maravillas modernas."
    },
    "corea": {
        "nombre": "Corea del Sur Completa",
        "pais": "Corea del Sur",
        "ciudad": "Seúl, Busan, Jeju Island",
        "duracion": "11 días",
        "precio_base": 1300,
        "incluye": ["Hoteles 4*", "Vuelo a Jeju", "Tours K-pop", "Comidas típicas"],
        "imagen": "https://images.unsplash.com/photo-1534274867514-d5b47ef89ed7?w=600",
        "descripcion": "Experimenta la mezcla única de tradición y modernidad en Corea."
    },
    "indonesia": {
        "nombre": "Paraíso de Bali",
        "pais": "Indonesia",
        "ciudad": "Bali, Ubud, Seminyak",
        "duracion": "8 días",
        "precio_base": 800,
        "incluye": ["Villas de lujo", "Spa y yoga", "Tours culturales", "Desayunos"],
        "imagen": "https://images.unsplash.com/photo-1537953773345-d172ccf13cf1?w=600",
        "descripcion": "Relájate en las playas y templos del paraíso indonesio."
    },
    "malasia": {
        "nombre": "Malasia Diversa",
        "pais": "Malasia",
        "ciudad": "Kuala Lumpur, Penang, Langkawi",
        "duracion": "10 días",
        "precio_base": 950,
        "incluye": ["Hoteles 4*", "Vuelos domésticos", "City tours", "Desayunos"],
        "imagen": "https://images.unsplash.com/photo-1596422846543-75c6fc197f07?w=600",
        "descripcion": "Descubre la diversidad cultural y natural de Malasia."
    },
    "singapur": {
        "nombre": "Singapur Moderno",
        "pais": "Singapur",
        "ciudad": "Singapur",
        "duracion": "5 días",
        "precio_base": 1400,
        "incluye": ["Hotel 5*", "Entradas a atracciones", "Tour gastronómico", "Transporte"],
        "imagen": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=600",
        "descripcion": "Vive la experiencia futurista de la ciudad jardín de Singapur."
    },
    "india": {
        "nombre": "India Mística",
        "pais": "India",
        "ciudad": "Delhi, Agra, Jaipur",
        "duracion": "12 días",
        "precio_base": 850,
        "incluye": ["Hoteles 4*", "Visita al Taj Mahal", "Guía local", "Desayunos"],
        "imagen": "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=600",
        "descripcion": "Sumérgete en la cultura y espiritualidad de la India."
    },
    "filipinas": {
        "nombre": "Islas Filipinas",
        "pais": "Filipinas",
        "ciudad": "Palawan, Cebu, Boracay",
        "duracion": "10 días",
        "precio_base": 1100,
        "incluye": ["Resorts playeros", "Tours de snorkel", "Transporte entre islas", "Desayunos"],
        "imagen": "https://images.unsplash.com/photo-1558642084-fd07fae5282e?w=600",
        "descripcion": "Descubre las playas más hermosas del mundo en Filipinas."
    },
    "sri-lanka": {
        "nombre": "Perla del Índico",
        "pais": "Sri Lanka",
        "ciudad": "Colombo, Kandy, Galle",
        "duracion": "9 días",
        "precio_base": 950,
        "incluye": ["Hoteles boutique", "Safari en Yala", "Tren montañoso", "Guía"],
        "imagen": "https://images.unsplash.com/photo-1573804633921-5c87f5d3a1c9?w=600",
        "descripcion": "Explora los tesoros naturales y culturales de Sri Lanka."
    },
    "camboya": {
        "nombre": "Reino de Angkor",
        "pais": "Camboya",
        "ciudad": "Siem Reap, Phnom Penh",
        "duracion": "7 días",
        "precio_base": 750,
        "incluye": ["Hoteles 4*", "Entrada a Angkor Wat", "Tour histórico", "Desayunos"],
        "imagen": "https://images.unsplash.com/photo-1560169897-fc0cdbdfa4d5?w=600",
        "descripcion": "Maravíllate con los templos ancestrales de Angkor Wat."
    }
}

@app.route("/")
def index():
    """Página principal con diseño TravelAsia"""
    destinos = []
    try:
        if db is not None:
            destinos = list(destinos_collection.find())
        else:
            flash("⚠️ Modo demo: Base de datos temporalmente no disponible", "info")
    except Exception as e:
        flash(f"⚠️ Error cargando destinos: {str(e)[:100]}...", "warning")
    
    return render_template("index.html", destinos=destinos, tours=TOURS_PREDEFINIDOS)

@app.route("/new", methods=["GET", "POST"])
@login_required
def create():
    """Crear nuevo destino asiático"""
    if request.method == "POST":
        # Validar campos obligatorios
        nombre = request.form.get("nombre", "").strip()
        pais = request.form.get("pais", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        
        if not nombre or not pais or not descripcion:
            flash("❌ Completa todos los campos obligatorios: Nombre, País y Descripción", "danger")
            return redirect(url_for("create"))

        # Crear nuevo destino
        nuevo_destino = {
            "nombre": nombre,
            "pais": pais,
            "ciudad": request.form.get("ciudad", "").strip(),
            "mejor_epoca": request.form.get("mejor_epoca", "Todo el año"),
            "presupuesto": float(request.form.get("presupuesto", 0) or 0),
            "actividades": request.form.get("actividades", "").strip(),
            "descripcion": descripcion,
            "imagen": request.form.get("imagen", "").strip(),
            "calificacion": int(request.form.get("calificacion", 3))
        }

        # Guardar en MongoDB
        if db is not None:
            try:
                destinos_collection.insert_one(nuevo_destino)
                flash("✅ ¡Destino asiático agregado correctamente!", "success")
            except Exception as e:
                flash(f"❌ Error guardando en base de datos: {e}", "danger")
        else:
            flash("⚠️ Modo demo: Los datos no se guardarán permanentemente", "warning")

        return redirect(url_for("index"))
    
    return render_template("create.html")

@app.route("/view/<id>")
def view(id):
    """Ver detalles de un destino"""
    if db is None:
        flash("❌ Base de datos no disponible", "danger")
        return redirect(url_for("index"))
    
    try:
        destino = destinos_collection.find_one({"_id": ObjectId(id)})
        if not destino:
            flash("⚠️ Destino no encontrado", "warning")
            return redirect(url_for("index"))
    except Exception as e:
        flash(f"❌ Error buscando destino: {e}", "danger")
        return redirect(url_for("index"))
    
    return render_template("view.html", destino=destino)

@app.route("/edit/<id>", methods=["GET", "POST"])
@login_required
def edit(id):
    """Editar destino existente"""
    if db is None:
        flash("❌ Base de datos no disponible", "danger")
        return redirect(url_for("index"))
    
    try:
        destino = destinos_collection.find_one({"_id": ObjectId(id)})
        if not destino:
            flash("⚠️ Destino no encontrado", "warning")
            return redirect(url_for("index"))
    except Exception as e:
        flash(f"❌ Error buscando destino: {e}", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        # Validar campos
        nombre = request.form.get("nombre", "").strip()
        pais = request.form.get("pais", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        
        if not nombre or not pais or not descripcion:
            flash("❌ Completa todos los campos obligatorios", "danger")
            return redirect(url_for("edit", id=id))

        # Actualizar destino
        try:
            destinos_collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": {
                    "nombre": nombre,
                    "pais": pais,
                    "ciudad": request.form.get("ciudad", "").strip(),
                    "mejor_epoca": request.form.get("mejor_epoca", "Todo el año"),
                    "presupuesto": float(request.form.get("presupuesto", 0) or 0),
                    "actividades": request.form.get("actividades", "").strip(),
                    "descripcion": descripcion,
                    "imagen": request.form.get("imagen", "").strip(),
                    "calificacion": int(request.form.get("calificacion", 3))
                }}
            )
            flash("✏️ ¡Destino actualizado correctamente!", "info")
        except Exception as e:
            flash(f"❌ Error actualizando destino: {e}", "danger")

        return redirect(url_for("index"))

    return render_template("edit.html", destino=destino)

@app.route("/delete/<id>", methods=["POST"])
@login_required
def delete(id):
    """Eliminar destino"""
    if db is not None:
        try:
            destinos_collection.delete_one({"_id": ObjectId(id)})
            flash("🗑️ Destino eliminado correctamente", "secondary")
        except Exception as e:
            flash(f"❌ Error eliminando destino: {e}", "danger")
    else:
        flash("⚠️ Modo demo: No se puede eliminar", "warning")
    
    return redirect(url_for("index"))

@app.route("/cotizar/<pais>")
def cotizar_tour(pais):
    """Página de cotización de tours"""
    tour = TOURS_PREDEFINIDOS.get(pais)
    if not tour:
        flash("Tour no encontrado", "danger")
        return redirect(url_for("index"))
    return render_template("cotizar.html", tour=tour)

@app.route("/procesar_cotizacion", methods=["POST"])
def procesar_cotizacion():
    """Procesar la cotización del tour"""
    try:
        datos = request.form
        pais = datos.get("pais")
        personas = int(datos.get("personas", 1))
        noches = int(datos.get("noches", 7))
        categoria = datos.get("categoria", "estandar")
        
        # Cálculo de precio
        tour = TOURS_PREDEFINIDOS.get(pais)
        if not tour:
            flash("Tour no disponible", "danger")
            return redirect(url_for("index"))
        
        precio_base = tour["precio_base"]
        
        # Ajustes por categoría
        multiplicadores = {
            "economico": 0.8,
            "estandar": 1.0,
            "premium": 1.5,
            "lujo": 2.0
        }
        
        precio_final = precio_base * multiplicadores.get(categoria, 1.0) * personas * (noches / 7)
        
        return render_template("resultado_cotizacion.html", 
                             datos=datos,
                             tour=tour,
                             precio_final=round(precio_final, 2))
                             
    except Exception as e:
        flash(f"Error en la cotización: {e}", "danger")
        return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register():
    """Registro de nuevos usuarios"""
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        tipo_usuario = request.form.get("tipo_usuario", "viajero")
        
        # Validaciones básicas
        if not nombre or not email or not password:
            flash("❌ Todos los campos son obligatorios", "danger")
            return redirect(url_for("register"))
        
        if len(password) < 6:
            flash("❌ La contraseña debe tener al menos 6 caracteres", "danger")
            return redirect(url_for("register"))
        
        # Verificar si el usuario ya existe
        if db is not None:
            usuario_existente = usuarios_collection.find_one({"email": email})
            if usuario_existente:
                flash("❌ Este email ya está registrado", "danger")
                return redirect(url_for("register"))
            
            # Crear nuevo usuario
            nuevo_usuario = {
                "nombre": nombre,
                "email": email,
                "password": generate_password_hash(password),
                "tipo_usuario": tipo_usuario,
                "pais_interes": request.form.get("pais_interes", ""),
                "presupuesto": float(request.form.get("presupuesto", 0) or 0),
                "fecha_registro": datetime.datetime.utcnow()
            }
            
            try:
                usuarios_collection.insert_one(nuevo_usuario)
                flash("✅ ¡Registro exitoso! Ahora puedes iniciar sesión", "success")
                return redirect(url_for("login"))
            except Exception as e:
                flash(f"❌ Error en el registro: {e}", "danger")
        else:
            flash("⚠️ Base de datos no disponible", "warning")
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Inicio de sesión de usuarios"""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        
        if not email or not password:
            flash("❌ Email y contraseña requeridos", "danger")
            return redirect(url_for("login"))
        
        if db is not None:
            try:
                usuario = usuarios_collection.find_one({"email": email})
                if usuario and check_password_hash(usuario["password"], password):
                    # Iniciar sesión
                    session["user_id"] = str(usuario["_id"])
                    session["user_name"] = usuario["nombre"]
                    session["user_type"] = usuario["tipo_usuario"]
                    session["user_email"] = usuario["email"]
                    
                    flash(f"🎉 ¡Bienvenido/a {usuario['nombre']}!", "success")
                    return redirect(url_for("index"))
                else:
                    flash("❌ Email o contraseña incorrectos", "danger")
            except Exception as e:
                flash(f"❌ Error en el login: {e}", "danger")
        else:
            flash("⚠️ Base de datos no disponible", "warning")
    
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    """Cerrar sesión"""
    session.clear()
    flash("👋 ¡Sesión cerrada correctamente!", "info")
    return redirect(url_for("index"))

@app.route("/profile")
@login_required
def profile():
    """Perfil del usuario"""
    if db is not None:
        try:
            usuario = usuarios_collection.find_one({"_id": ObjectId(session["user_id"])})
            if usuario:
                return render_template("profile.html", usuario=usuario)
        except Exception as e:
            flash(f"❌ Error cargando perfil: {e}", "danger")
    
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)