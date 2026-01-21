import sqlite3              # Librería estándar de Python para trabajar con bases de datos SQLite
from .modelos import Tarea, Proyecto   # Importa las clases del módulo modelos.py
import os                   # Librería para manejar archivos y rutas

# Nombre del archivo físico de la base de datos
DATABASE_NAME = 'tareas.db'


def get_connection():
    # Abre una conexión con la base de datos SQLite
    conn = sqlite3.connect(DATABASE_NAME)
    # Configura la conexión para que las filas se puedan acceder como diccionarios (por nombre de columna)
    conn.row_factory = sqlite3.Row
    return conn


def crear_tablas():
    # Obtiene conexión y cursor para ejecutar sentencias SQL
    conn = get_connection()
    cursor = conn.cursor()

    # Crea la tabla de proyectos si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Identificador único autoincremental
            nombre TEXT NOT NULL,                   -- Nombre obligatorio del proyecto
            descripcion TEXT,                       -- Descripción opcional
            fecha_inicio TEXT,                      -- Fecha de inicio (guardada como texto)
            estado TEXT                             -- Estado del proyecto (ej. Activo, Inactivo)
        )
    """)

    # Crea la tabla de tareas si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Identificador único autoincremental
            titulo TEXT NOT NULL,                   -- Título obligatorio de la tarea
            descripcion TEXT,                       -- Descripción opcional
            fecha_creacion TEXT,                    -- Fecha de creación
            fecha_limite TEXT,                      -- Fecha límite
            prioridad TEXT,                         -- Prioridad (ej. Alta, Media, Baja)
            estado TEXT,                            -- Estado de la tarea
            proyecto_id INTEGER,                    -- Relación con un proyecto
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) -- Clave foránea que asegura que el proyecto exista
        )
    """)

    # Inserta un proyecto por defecto con id=0 para tareas generales
    try:
        cursor.execute(
            "INSERT INTO proyectos (id, nombre, descripcion, estado) VALUES (0, 'Tareas Generales', 'Tareas sin clasificar', 'Activo')")
    except sqlite3.IntegrityError:
        # Si ya existe el proyecto con id=0, ignora el error
        pass

    # Guarda los cambios y cierra la conexión
    conn.commit()
    conn.close()


class DBManager:
    """
    Clase que gestiona las operaciones con la base de datos.
    """

    def __init__(self):
        # Al crear un DBManager, asegura que las tablas existan
        crear_tablas()

    def crear_tarea(self, tarea: Tarea) -> Tarea:
        # Inserta una nueva tarea en la base de datos
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tareas(titulo, descripcion, fecha_creacion, fecha_limite, prioridad, estado, proyecto_id)
            VALUES(?, ?, ?, ?, ?, ?, ?)
        """, (tarea._titulo, tarea._descripcion, tarea._fecha_creacion, tarea._fecha_limite,
              tarea._prioridad, tarea._estado, tarea._proyecto_id))

        # Asigna al objeto tarea el id generado automáticamente
        tarea.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return tarea

    def obtener_proyectos(self):
        # Recupera todos los proyectos de la base de datos
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM proyectos")
        filas = cursor.fetchall()
        conn.close()

        # Convierte cada fila en un objeto Proyecto
        proyectos = [
            Proyecto(nombre=fila['nombre'], descripcion=fila['descripcion'],
                     id=fila['id'], estado=fila['estado'])
            for fila in filas
        ]
        return proyectos
    
    def obtener_tareas(self, estado=None):
        """
        Obtiene tareas de la DB. Aplica un algoritmo de ordenamiento y filtrado.
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        sql = "SELECT * FROM tareas"
        params = []
        
        # Algoritmo de Filtrado: Si se pasa un estado, filtramos
        if estado:
            sql += " WHERE estado = ?"
            params.append(estado)

        # Algoritmo de Ordenamiento: Ordenamos por fecha límite (ASCENDENTE)
        sql += " ORDER BY fecha_limite ASC" 

        cursor.execute(sql, params)
        filas = cursor.fetchall()
        conn.close()
        
        # Convertimos filas SQL (diccionarios gracias a row_factory) a objetos Tarea (POO)
        tareas = []
        for fila in filas:
            # Recreamos el objeto Tarea a partir de los datos de la DB
            t = Tarea(
                titulo=fila['titulo'], 
                fecha_limite=fila['fecha_limite'],
                prioridad=fila['prioridad'],
                proyecto_id=fila['proyecto_id'],
                descripcion=fila['descripcion'],
                id=fila['id'],
                estado=fila['estado']
            )
            tareas.append(t)
        return tareas

# Bloque de prueba: se ejecuta solo si corres este archivo directamente
if __name__ == '__main__':
    # Si existe la base de datos, la elimina para empezar de cero
    if os.path.exists(DATABASE_NAME):
        os.remove(DATABASE_NAME)
        print(f"Base de datos {DATABASE_NAME} eliminada.")

    # Crea las tablas de nuevo
    crear_tablas()
    print(f"Base de datos {DATABASE_NAME} y tablas inicializadas correctamente.")

    # Prueba de inserción de una tarea (CRUD: CREATE)
    manager = DBManager()
    tarea_prueba = Tarea(
        titulo="Completar Ejercicio de CRUD",
        fecha_limite="2025-10-30",
        prioridad="Alta",
        proyecto_id=0,   # Se asigna al proyecto por defecto "Tareas Generales"
        descripcion="Implementar el módulo database.py"
    )

    # Inserta la tarea y muestra el id asignado
    tarea_creada = manager.crear_tarea(tarea_prueba)
    print(f"Tarea creada y ID asignado: {tarea_creada.id}")
