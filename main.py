import bcrypt
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database_fluido import SessionLocal, Resultado, Usuario
from datetime import datetime

# --- Configuración base de la app ---
app = FastAPI(title="Fluidos para todos API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Puedes cambiar si usas un dominio específico
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dependencia para la sesión ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Modelos Pydantic ---
class ResultadoIn(BaseModel):
    usuario: str
    ejercicio: int
    respuesta: str

class UsuarioIn(BaseModel):
    nombre: str
    correo: str
    clave: str

# --- Datos base de los ejercicios ---
respuestas_ref = {
    1: {"exacto": 8.49, "rango": [7, 9]},
    2: {"exacto": 227.12, "rango": [200, 240]},
    3: {"exacto": 1.26, "rango": [1, 3]},
    4: {"exacto": 147.963, "rango": [120, 200]},
    5: {"exacto": 3.25, "rango": [3, 4]},
    6: {"exacto": 2.10, "rango": [1.8, 2.3]},
    7: {"exacto": 0.95, "rango": [0.8, 1.1]},
    8: {"exacto": 4.43, "rango": [0.8, 10.0]},
    9: {"exacto": 10.43, "rango": [8, 15]},
    10: {"exacto": 0.95, "rango": [0.8, 1.1]},
    11: {"exacto": 0.95, "rango": [0.8, 1.1]},
    12: {"exacto": 1.333, "rango": [0, 3.0]},
    13: {"exacto": 7111.5, "rango": [7000, 7200]},
    14: {"exacto": 5.75, "rango": [4, 7]},
    15: {"exacto": 7.668, "rango": [6.0, 9.0]},
    16: {"exacto": 5.6, "rango": [4.5, 7.0]},
}

# ============================
# 🔹 RUTAS DE USUARIOS
# ============================


class Login(BaseModel):
    correo: str
    password: str
class Registro(BaseModel):
    nombre: str
    correo: str
    password: str
@app.post("/registro")
def registrar_usuario(data: Registro, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.correo == data.correo).first()
    if user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado.")

    # Convertir a string para evitar errores
    hashed = bcrypt.hashpw(data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    nuevo_usuario = Usuario(
        nombre=data.nombre,
        correo=data.correo,
        password=hashed
    )

    db.add(nuevo_usuario)
    db.commit()

    return {"mensaje": "Usuario registrado exitosamente."}

@app.post("/login")
def login_usuario(data: Login, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.correo == data.correo).first()

    if not user:
        raise HTTPException(status_code=400, detail="Correo no encontrado.")

    if not bcrypt.checkpw(data.password.encode("utf-8"), user.password.encode("utf-8")):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta.")

    return {
        "mensaje": "Inicio de sesión exitoso",
        "usuario": {"nombre": user.nombre, "correo": user.correo}
    }

# ============================
# 🔹 RUTAS DE RESULTADOS
# ============================
@app.post("/guardar_resultado/")
async def guardar_resultado(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    print("📩 Datos recibidos:", data)

    usuario = data.get("usuario", "invitado")
    ejercicio = int(data.get("ejercicio", 0))
    respuesta = data.get("respuesta", "")

    estado = "incorrecto"
    puntaje = 0

    # Bloquear si ya lo resolvió correctamente
    previo = db.query(Resultado).filter(
        Resultado.usuario == usuario,
        Resultado.ejercicio == ejercicio,
        Resultado.estado == "correcto"
    ).first()

    if previo:
        return {"mensaje": "✅ Ya resolviste correctamente este ejercicio.", "bloqueado": True}

    # Evaluar respuesta
    if ejercicio in respuestas_ref:
        ref = respuestas_ref[ejercicio]
        try:
            valor = float(respuesta)
            if abs(valor - ref["exacto"]) < 1e-3:
                estado = "correcto"
                puntaje = 1
            elif ref["rango"][0] <= valor <= ref["rango"][1]:
                estado = "cercano"
                puntaje = 0.5
        except ValueError:
            pass

    nuevo = Resultado(
        usuario=usuario,
        ejercicio=ejercicio,
        respuesta=respuesta,
        puntaje=puntaje,
        estado=estado,
        fecha=datetime.now()
    )
    db.add(nuevo)
    db.commit()

    total = sum([r.puntaje for r in db.query(Resultado).filter(Resultado.usuario == usuario).all()])

    return {
        "mensaje": "Resultado guardado correctamente.",
        "usuario": usuario,
        "ejercicio": ejercicio,
        "estado": estado,
        "puntaje": puntaje,
        "puntaje_total": total
    }


@app.get("/resultados/")
def obtener_resultados(db: Session = Depends(get_db)):
    datos = db.query(Resultado).order_by(Resultado.fecha.desc()).all()  # Ordenar por fecha descendente
    return [
        {
            "usuario": r.usuario,
            "ejercicio": r.ejercicio,
            "respuesta": r.respuesta,
            "puntaje": r.puntaje,
            "estado": r.estado,
            "fecha": r.fecha.strftime("%d/%m/%Y, %H:%M:%S")
        }
        for r in datos
    ]

