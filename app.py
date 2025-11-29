from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import datetime
from datetime import timedelta  # ✅ AGREGAR ESTE IMPORT

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
    itinerarios_collection = db.itinerarios
    # Test simple de conexión
    db.command('ping')
    print("✅ ¡CONECTADO A MONGODB ATLAS! - TravelAsia")
except Exception as e:
    db = None
    destinos_collection = None
    usuarios_collection = None
    itinerarios_collection = None
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

# COORDENADAS DE PAÍSES PARA EL MAPA
COORDENADAS_PAISES = {
    "Japón": {"lat": 36.2048, "lng": 138.2529, "zoom": 5},
    "Tailandia": {"lat": 15.8700, "lng": 100.9925, "zoom": 5},
    "Vietnam": {"lat": 14.0583, "lng": 108.2772, "zoom": 5},
    "China": {"lat": 35.8617, "lng": 104.1954, "zoom": 4},
    "Corea del Sur": {"lat": 35.9078, "lng": 127.7669, "zoom": 6},
    "Indonesia": {"lat": -0.7893, "lng": 113.9213, "zoom": 5},
    "Malasia": {"lat": 4.2105, "lng": 101.9758, "zoom": 6},
    "Singapur": {"lat": 1.3521, "lng": 103.8198, "zoom": 11},
    "India": {"lat": 20.5937, "lng": 78.9629, "zoom": 4},
    "Filipinas": {"lat": 12.8797, "lng": 121.7740, "zoom": 5},
    "Sri Lanka": {"lat": 7.8731, "lng": 80.7718, "zoom": 7},
    "Camboya": {"lat": 12.5657, "lng": 104.9910, "zoom": 6}
}

# ========== FUNCIONES UTILITARIAS ==========

def calcular_duracion_dias(fecha_inicio, fecha_fin):
    """Calcula la duración en días entre dos fechas"""
    try:
        inicio = datetime.datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fin = datetime.datetime.strptime(fecha_fin, '%Y-%m-%d')
        return (fin - inicio).days + 1
    except:
        return 7

def calcular_porcentaje_completado(itinerario):
    """Calcula el porcentaje de completado del itinerario"""
    if not itinerario.get('actividades'):
        return 0
    total_actividades = len(itinerario['actividades'])
    completadas = sum(1 for act in itinerario['actividades'] if act.get('completada', False))
    return int((completadas / total_actividades) * 100) if total_actividades > 0 else 0

def calcular_porcentaje_presupuesto(itinerario):
    """Calcula el porcentaje del presupuesto usado"""
    if itinerario.get('presupuesto_total', 0) > 0:
        gastado = itinerario['presupuesto_total'] - itinerario.get('presupuesto_restante', 0)
        return int((gastado / itinerario['presupuesto_total']) * 100)
    return 0

def generar_itinerario_automatico(datos_ia, user_id):
    """Genera un itinerario automático basado en las preferencias del usuario"""
    
    # Lógica de sugerencia de países según tipo de viaje
    sugerencias_paises = {
        'cultural': ['Japón', 'Corea del Sur', 'China'],
        'aventura': ['Tailandia', 'Vietnam', 'Indonesia'],
        'relax': ['Tailandia', 'Indonesia', 'Filipinas'],
        'gastronomia': ['Japón', 'Tailandia', 'Vietnam'],
        'shopping': ['Corea del Sur', 'Japón', 'Singapur']
    }
    
    paises = sugerencias_paises.get(datos_ia['tipo_viaje'], ['Japón', 'Tailandia'])
    
    # Calcular fechas
    fecha_inicio = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    fecha_fin = (datetime.datetime.now() + datetime.timedelta(days=30 + datos_ia['duracion'])).strftime('%Y-%m-%d')
    
    return {
        'usuario_id': ObjectId(user_id),
        'nombre_viaje': f"Viaje {datos_ia['tipo_viaje'].title()} - {datos_ia['duracion']} días",
        'paises': paises[:2],  # Máximo 2 países para no complicar
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'presupuesto_total': datos_ia['presupuesto'],
        'presupuesto_restante': datos_ia['presupuesto'],
        'descripcion': f'Itinerario generado automáticamente para {datos_ia["viajeros"]}. Tipo: {datos_ia["tipo_viaje"]}',
        'estado': 'planificando',
        'actividades': [],
        'duracion_dias': datos_ia['duracion'],
        'fecha_creacion': datetime.datetime.utcnow(),
        'fecha_actualizacion': datetime.datetime.utcnow(),
        'generado_ia': True,
        'prioridad': 'media'
    }

# ========== RUTAS PÚBLICAS ==========

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

@app.route("/destinos")
def destinos():
    """Página de destinos disponibles"""
    return render_template("destinos.html", tours=TOURS_PREDEFINIDOS)

@app.route("/explora")
def explora():
    """Página de exploración y búsqueda de destinos"""
    return render_template("explora.html", tours=TOURS_PREDEFINIDOS)

@app.route("/cotizar")
def cotizar():
    """Página de cotización"""
    return render_template("cotizar.html", tours=TOURS_PREDEFINIDOS)

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

@app.route("/cotizar/<pais>")
def cotizar_tour(pais):
    """Página de cotización de tours específicos"""
    tour = TOURS_PREDEFINIDOS.get(pais)
    if not tour:
        flash("Tour no encontrado", "danger")
        return redirect(url_for("index"))
    return render_template("cotizar.html", tour=tour)

# ========== RUTA RESULTADO_COTIZACION ==========

@app.route("/resultado_cotizacion")
def resultado_cotizacion():
    """Página de resultado de cotización"""
    # Obtener datos de la sesión o parámetros
    datos = request.args
    tour_key = datos.get('tour', 'japon')
    tour = TOURS_PREDEFINIDOS.get(tour_key, TOURS_PREDEFINIDOS['japon'])
    
    # Calcular datos para mostrar
    precio_final = datos.get('precio_final', 1500)
    personas = datos.get('personas', 2)
    noches = datos.get('noches', 7)
    categoria = datos.get('categoria', 'estandar')
    
    return render_template("resultado_cotizacion.html",
                         tour=tour,
                         precio_final=precio_final,
                         personas=personas,
                         noches=noches,
                         categoria=categoria)

# ========== AUTENTICACIÓN ==========

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
                # Calcular estadísticas del usuario
                itinerarios_count = itinerarios_collection.count_documents({
                    "usuario_id": ObjectId(session["user_id"])
                })
                
                viajes_activos = itinerarios_collection.count_documents({
                    "usuario_id": ObjectId(session["user_id"]),
                    "estado": "activo"
                })
                
                # Calcular presupuesto total de todos los itinerarios
                presupuesto_total = 0
                itinerarios = itinerarios_collection.find({
                    "usuario_id": ObjectId(session["user_id"])
                })
                for itinerario in itinerarios:
                    presupuesto_total += itinerario.get('presupuesto_total', 0)
                
                # Agregar estadísticas al usuario
                usuario['itinerarios_count'] = itinerarios_count
                usuario['viajes_activos'] = viajes_activos
                usuario['presupuesto_total'] = presupuesto_total
                
                return render_template("profile.html", usuario=usuario, tours=TOURS_PREDEFINIDOS)
        except Exception as e:
            flash(f"❌ Error cargando perfil: {e}", "danger")
    
    return redirect(url_for("index"))

# ========== GESTIÓN DE DESTINOS ==========

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

# ========== PLANIFICADOR DE VIAJES ==========

@app.route("/planificador")
@login_required
def planificador():
    """Página principal del planificador con mapa interactivo"""
    itinerarios = []
    if db is not None:
        try:
            itinerarios = list(itinerarios_collection.find({
                "usuario_id": ObjectId(session["user_id"])
            }).sort("fecha_creacion", -1))
            
            # Calcular estadísticas para cada itinerario
            for itinerario in itinerarios:
                itinerario['porcentaje_completado'] = calcular_porcentaje_completado(itinerario)
                itinerario['porcentaje_presupuesto'] = calcular_porcentaje_presupuesto(itinerario)
                
        except Exception as e:
            flash(f"❌ Error cargando itinerarios: {e}", "danger")
    
    return render_template("planificador.html", 
                         itinerarios=itinerarios,
                         tours=TOURS_PREDEFINIDOS,
                         coordenadas=COORDENADAS_PAISES)

@app.route("/crear-itinerario", methods=["GET", "POST"])
@login_required
def crear_itinerario():
    """Crear nuevo itinerario multi-país"""
    if request.method == "POST":
        nombre_viaje = request.form.get("nombre_viaje", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        fecha_inicio = request.form.get("fecha_inicio")
        fecha_fin = request.form.get("fecha_fin")
        presupuesto_total = float(request.form.get("presupuesto_total", 0) or 0)
        
        if not nombre_viaje or not fecha_inicio or not fecha_fin:
            flash("❌ Nombre del viaje y fechas son obligatorios", "danger")
            return redirect(url_for("crear_itinerario"))
        
        fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, "%Y-%m-%d")
        fecha_fin_dt = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d")
        duracion_dias = (fecha_fin_dt - fecha_inicio_dt).days
        
        if duracion_dias <= 0:
            flash("❌ La fecha fin debe ser posterior a la fecha inicio", "danger")
            return redirect(url_for("crear_itinerario"))
        
        paises = request.form.getlist("paises")
        if not paises:
            flash("❌ Selecciona al menos un país", "danger")
            return redirect(url_for("crear_itinerario"))
        
        nuevo_itinerario = {
            "usuario_id": ObjectId(session["user_id"]),
            "nombre_viaje": nombre_viaje,
            "descripcion": descripcion,
            "paises": paises,
            "ciudades": [],
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "duracion_dias": duracion_dias,
            "presupuesto_total": presupuesto_total,
            "presupuesto_restante": presupuesto_total,
            "actividades": [],
            "transportes": [],
            "estado": "planificando",
            "fecha_creacion": datetime.datetime.utcnow(),
            "fecha_actualizacion": datetime.datetime.utcnow(),
            "prioridad": "media",
            "favorito": False
        }
        
        if db is not None:
            try:
                result = itinerarios_collection.insert_one(nuevo_itinerario)
                flash("✅ ¡Itinerario creado correctamente! Ahora agrega actividades.", "success")
                return redirect(url_for("ver_itinerario", id=result.inserted_id))
            except Exception as e:
                flash(f"❌ Error creando itinerario: {e}", "danger")
        else:
            flash("⚠️ Base de datos no disponible", "warning")
    
    # ✅ CORRECCIÓN: CALCULAR FECHAS POR DEFECTO
    hoy = datetime.datetime.now().strftime('%Y-%m-%d')
    fecha_fin_default = (datetime.datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
    
    paises_pre_seleccionados = request.args.get('paises', '').split(',') if request.args.get('paises') else []
    
    return render_template("crear_itinerario.html", 
                         tours=TOURS_PREDEFINIDOS, 
                         paises_pre_seleccionados=paises_pre_seleccionados,
                         hoy=hoy,
                         fecha_fin_default=fecha_fin_default)

@app.route("/itinerario/<id>")
@login_required
def ver_itinerario(id):
    """Ver detalles de un itinerario"""
    if db is None:
        flash("❌ Base de datos no disponible", "danger")
        return redirect(url_for("planificador"))
    
    try:
        itinerario = itinerarios_collection.find_one({
            "_id": ObjectId(id),
            "usuario_id": ObjectId(session["user_id"])
        })
        if not itinerario:
            flash("⚠️ Itinerario no encontrado", "warning")
            return redirect(url_for("planificador"))
        
        # Calcular porcentajes
        itinerario['porcentaje_completado'] = calcular_porcentaje_completado(itinerario)
        itinerario['porcentaje_presupuesto'] = calcular_porcentaje_presupuesto(itinerario)
        
        return render_template("ver_itinerario.html", itinerario=itinerario)
        
    except Exception as e:
        flash(f"❌ Error cargando itinerario: {e}", "danger")
        return redirect(url_for("planificador"))

@app.route("/editar-itinerario/<id>", methods=["GET", "POST"])
@login_required
def editar_itinerario(id):
    """Editar un itinerario existente"""
    try:
        user_id = session["user_id"]
        itinerario = itinerarios_collection.find_one({
            "_id": ObjectId(id),
            "usuario_id": ObjectId(user_id)
        })
        
        if not itinerario:
            flash("⚠️ Itinerario no encontrado", "warning")
            return redirect(url_for("planificador"))
        
        if request.method == "POST":
            # Recoger datos actualizados
            updates = {
                "nombre_viaje": request.form.get("nombre_viaje"),
                "paises": request.form.getlist("paises"),
                "fecha_inicio": request.form.get("fecha_inicio"),
                "fecha_fin": request.form.get("fecha_fin"),
                "presupuesto_total": float(request.form.get("presupuesto_total", 0)),
                "descripcion": request.form.get("descripcion", ""),
                "duracion_dias": calcular_duracion_dias(
                    request.form.get("fecha_inicio"), 
                    request.form.get("fecha_fin")
                ),
                "fecha_actualizacion": datetime.datetime.utcnow()
            }
            
            # Actualizar en la base de datos
            itinerarios_collection.update_one(
                {"_id": ObjectId(id)}, 
                {"$set": updates}
            )
            
            flash("✅ ¡Itinerario actualizado exitosamente!", "success")
            return redirect(url_for("ver_itinerario", id=id))
        
        # GET - Mostrar formulario de edición
        return render_template("editar_itinerario.html", itinerario=itinerario)
        
    except Exception as e:
        flash(f"❌ Error al editar el itinerario: {str(e)}", "danger")
        return redirect(url_for("planificador"))

@app.route("/duplicar-itinerario/<id>", methods=["POST"])
@login_required
def duplicar_itinerario(id):
    """Duplicar un itinerario existente"""
    try:
        user_id = session["user_id"]
        itinerario_original = itinerarios_collection.find_one({
            "_id": ObjectId(id),
            "usuario_id": ObjectId(user_id)
        })
        
        if itinerario_original:
            # Crear copia sin el _id original
            itinerario_copia = itinerario_original.copy()
            itinerario_copia.pop('_id', None)
            
            # Actualizar campos para la copia
            itinerario_copia['nombre_viaje'] += ' (Copia)'
            itinerario_copia['fecha_creacion'] = datetime.datetime.utcnow()
            itinerario_copia['presupuesto_restante'] = itinerario_copia['presupuesto_total']
            itinerario_copia['actividades'] = []  # Limpiar actividades
            
            # Insertar la copia
            itinerarios_collection.insert_one(itinerario_copia)
            flash("✅ Itinerario duplicado exitosamente!", "success")
        else:
            flash("❌ Itinerario no encontrado", "error")
            
    except Exception as e:
        flash(f"❌ Error al duplicar el itinerario: {str(e)}", "danger")
    
    return redirect(url_for("planificador"))

@app.route("/generar-itinerario-ia", methods=["POST"])
@login_required
def generar_itinerario_ia():
    """Generar itinerario automático con IA"""
    try:
        user_id = session["user_id"]
        
        # Recoger datos del formulario IA
        datos_ia = {
            'presupuesto': float(request.form.get("presupuesto", 1500)),
            'duracion': int(request.form.get("duracion", 10)),
            'tipo_viaje': request.form.get("tipo_viaje", "cultural"),
            'viajeros': request.form.get("viajeros", "pareja")
        }
        
        # Generar itinerario automático
        itinerario_ia = generar_itinerario_automatico(datos_ia, user_id)
        
        # Guardar en la base de datos
        result = itinerarios_collection.insert_one(itinerario_ia)
        flash("🤖 ¡Itinerario IA generado exitosamente!", "success")
        return redirect(url_for("ver_itinerario", id=result.inserted_id))
        
    except Exception as e:
        flash(f"❌ Error al generar itinerario IA: {str(e)}", "danger")
        return redirect(url_for("planificador"))

# ========== GESTIÓN DE ACTIVIDADES ==========

@app.route("/agregar-actividad/<itinerario_id>", methods=["POST"])
@login_required
def agregar_actividad(itinerario_id):
    """Agregar actividad a un itinerario"""
    if request.method == "POST":
        pais = request.form.get("pais", "").strip()
        ciudad = request.form.get("ciudad", "").strip()
        actividad = request.form.get("actividad", "").strip()
        tipo = request.form.get("tipo", "cultural")
        costo = float(request.form.get("costo", 0) or 0)
        fecha = request.form.get("fecha", "")
        
        if not pais or not ciudad or not actividad:
            flash("❌ País, ciudad y actividad son obligatorios", "danger")
            return redirect(url_for("ver_itinerario", id=itinerario_id))
        
        nueva_actividad = {
            "pais": pais,
            "ciudad": ciudad,
            "actividad": actividad,
            "tipo": tipo,
            "costo": costo,
            "fecha": fecha,
            "completada": False,
            "fecha_creacion": datetime.datetime.utcnow()
        }
        
        if db is not None:
            try:
                itinerarios_collection.update_one(
                    {
                        "_id": ObjectId(itinerario_id),
                        "usuario_id": ObjectId(session["user_id"])
                    },
                    {
                        "$push": {"actividades": nueva_actividad},
                        "$inc": {"presupuesto_restante": -costo},
                        "$set": {"fecha_actualizacion": datetime.datetime.utcnow()}
                    }
                )
                flash("✅ Actividad agregada correctamente", "success")
            except Exception as e:
                flash(f"❌ Error agregando actividad: {e}", "danger")
        
        return redirect(url_for("ver_itinerario", id=itinerario_id))

@app.route("/eliminar-actividad/<itinerario_id>/<int:actividad_index>", methods=["POST"])
@login_required
def eliminar_actividad(itinerario_id, actividad_index):
    """Eliminar una actividad de un itinerario"""
    try:
        user_id = session["user_id"]
        
        # Verificar que el itinerario pertenece al usuario
        itinerario = itinerarios_collection.find_one({
            "_id": ObjectId(itinerario_id),
            "usuario_id": ObjectId(user_id)
        })
        
        if not itinerario or actividad_index >= len(itinerario.get("actividades", [])):
            flash("❌ Actividad no encontrada", "danger")
            return redirect(url_for("ver_itinerario", id=itinerario_id))
        
        # Obtener costo de la actividad a eliminar
        actividad = itinerario["actividades"][actividad_index]
        costo_actividad = actividad.get("costo", 0)
        
        # Remover actividad y actualizar presupuesto
        itinerarios_collection.update_one(
            {"_id": ObjectId(itinerario_id)},
            {
                "$pull": {"actividades": actividad},
                "$inc": {"presupuesto_restante": costo_actividad},
                "$set": {"fecha_actualizacion": datetime.datetime.utcnow()}
            }
        )
        
        flash("✅ Actividad eliminada correctamente", "success")
        return redirect(url_for("ver_itinerario", id=itinerario_id))
        
    except Exception as e:
        flash(f"❌ Error al eliminar actividad: {str(e)}", "danger")
        return redirect(url_for("ver_itinerario", id=itinerario_id))

@app.route("/toggle-actividad/<itinerario_id>/<int:actividad_index>", methods=["POST"])
@login_required
def toggle_actividad(itinerario_id, actividad_index):
    """Marcar/desmarcar actividad como completada"""
    try:
        user_id = session["user_id"]
        
        itinerario = itinerarios_collection.find_one({
            "_id": ObjectId(itinerario_id),
            "usuario_id": ObjectId(user_id)
        })
        
        if not itinerario or actividad_index >= len(itinerario.get("actividades", [])):
            return jsonify({'success': False, 'error': 'Actividad no encontrada'})
        
        # Cambiar estado de completada
        nueva_estado = not itinerario['actividades'][actividad_index].get('completada', False)
        
        itinerarios_collection.update_one(
            {'_id': ObjectId(itinerario_id)},
            {
                '$set': {
                    f'actividades.{actividad_index}.completada': nueva_estado,
                    'fecha_actualizacion': datetime.datetime.utcnow()
                }
            }
        )
        
        return jsonify({'success': True, 'completada': nueva_estado})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route("/eliminar-itinerario/<id>", methods=["POST"])
@login_required
def eliminar_itinerario(id):
    """Eliminar itinerario"""
    if db is not None:
        try:
            itinerarios_collection.delete_one({
                "_id": ObjectId(id),
                "usuario_id": ObjectId(session["user_id"])
            })
            flash("🗑️ Itinerario eliminado correctamente", "secondary")
        except Exception as e:
            flash(f"❌ Error eliminando itinerario: {e}", "danger")
    else:
        flash("⚠️ Base de datos no disponible", "warning")
    
    return redirect(url_for("planificador"))

# ========== NUEVAS RUTAS PARA SISTEMA COMPLETO ==========

@app.route("/mis-itinerarios")
@login_required
def mis_itinerarios():
    """Página para ver todos los itinerarios del usuario"""
    if db is None:
        flash("❌ Base de datos no disponible", "danger")
        return redirect(url_for("index"))
    
    try:
        user_id = session["user_id"]
        itinerarios = list(itinerarios_collection.find({
            "usuario_id": ObjectId(user_id)
        }).sort("fecha_creacion", -1))
        
        # Calcular estadísticas para cada itinerario
        for itinerario in itinerarios:
            itinerario['porcentaje_completado'] = calcular_porcentaje_completado(itinerario)
            itinerario['porcentaje_presupuesto'] = calcular_porcentaje_presupuesto(itinerario)
            itinerario['dias_restantes'] = calcular_dias_restantes(itinerario)
            
        return render_template("mis_itinerarios.html", itinerarios=itinerarios)
        
    except Exception as e:
        flash(f"❌ Error cargando itinerarios: {e}", "danger")
        return redirect(url_for("planificador"))

def calcular_dias_restantes(itinerario):
    """Calcula días restantes hasta el viaje"""
    try:
        fecha_inicio = itinerario.get('fecha_inicio')
        if not fecha_inicio:
            return None
            
        fecha_inicio_dt = datetime.datetime.strptime(fecha_inicio, '%Y-%m-%d')
        hoy = datetime.datetime.now()
        dias_restantes = (fecha_inicio_dt - hoy).days
        
        return max(0, dias_restantes) if dias_restantes > 0 else None
    except:
        return None

@app.route("/actualizar-perfil", methods=["POST"])
@login_required
def actualizar_perfil():
    """Actualizar perfil del usuario"""
    if request.method == "POST":
        try:
            user_id = session["user_id"]
            updates = {
                "nombre": request.form.get("nombre", "").strip(),
                "pais_interes": request.form.get("pais_interes", ""),
                "presupuesto": float(request.form.get("presupuesto", 0) or 0),
                "fecha_actualizacion": datetime.datetime.utcnow()
            }
            
            # Actualizar en base de datos
            usuarios_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": updates}
            )
            
            # Actualizar sesión
            session["user_name"] = updates["nombre"]
            
            flash("✅ Perfil actualizado correctamente", "success")
            return redirect(url_for("profile"))
            
        except Exception as e:
            flash(f"❌ Error actualizando perfil: {str(e)}", "danger")
            return redirect(url_for("profile"))

# ========== API ENDPOINTS ==========

@app.route("/api/destinos")
def api_destinos():
    """API para obtener datos de destinos"""
    return jsonify(TOURS_PREDEFINIDOS)

@app.route("/api/itinerarios")
@login_required
def api_itinerarios():
    """API para obtener itinerarios del usuario"""
    user_id = session["user_id"]
    itinerarios = list(itinerarios_collection.find(
        {"usuario_id": ObjectId(user_id)},
        {"actividades": 0}  # Excluir actividades para optimizar
    ).sort("fecha_creacion", -1))
    
    # Convertir ObjectId a string
    for itinerario in itinerarios:
        itinerario['_id'] = str(itinerario['_id'])
        itinerario['porcentaje_completado'] = calcular_porcentaje_completado(itinerario)
        itinerario['porcentaje_presupuesto'] = calcular_porcentaje_presupuesto(itinerario)
    
    return jsonify(itinerarios)

# ========== MANEJO DE ERRORES ==========

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# ========== INICIALIZACIÓN ==========

def init_db():
    """Inicializar la base de datos con índices"""
    try:
        if db is not None:
            # Crear índices
            usuarios_collection.create_index('email', unique=True)
            itinerarios_collection.create_index('usuario_id')
            itinerarios_collection.create_index([('fecha_creacion', -1)])
            destinos_collection.create_index([('pais', 1)])
            print("✅ Base de datos inicializada correctamente")
    except Exception as e:
        print(f"❌ Error inicializando BD: {e}")

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)