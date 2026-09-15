from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import pandas as pd
import re
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LibrosFavoritos(BaseModel):
    ids_libros: list[int]

datos = np.load("modelo_svd.npz")
U = datos["U"]
sigma = datos["sigma"]
Vt = datos["Vt"]

books = pd.read_csv("data/books.csv")
ratings = pd.read_csv("data/ratings.csv")


def extraer_saga(titulo):
    """Detecta patrones tipo 'Titulo (Nombre de Saga, #2)' en el título.
    Si no encuentra ese formato, devuelve None (libro sin saga detectada)."""
    match = re.search(r"\((.+?),?\s*#\d+", titulo)
    if match:
        return match.group(1).strip()
    return None


@app.get("/recomendar/{usuario_id}")
def recomendar(usuario_id: int):
    fila_usuario = np.dot(np.dot(U[usuario_id - 1], np.diag(sigma)), Vt)

    libros_ya_calificados = ratings[ratings["user_id"] == usuario_id]["book_id"]

    puntajes = fila_usuario.copy()
    for libro_id in libros_ya_calificados:
        puntajes[libro_id - 1] = -np.inf

    ids_finales = _armar_top_sin_sagas_repetidas(puntajes)

    resultado = books[books["book_id"].isin(ids_finales)][
        ["book_id", "title", "authors", "image_url", "average_rating"]
    ]
    return resultado.to_dict(orient="records")


@app.get("/buscar_libros")
def buscar_libros(texto: str):
    resultado = books[books["title"].str.contains(texto, case=False, na=False)]
    return resultado[["book_id", "title", "authors", "image_url"]].head(10).to_dict(orient="records")


def similitud_coseno(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


@app.post("/recomendar_por_libros")
def recomendar_por_libros(favoritos: LibrosFavoritos):
    indices = [libro_id - 1 for libro_id in favoritos.ids_libros]

    vectores_libros = Vt[:, indices]
    perfil = vectores_libros.mean(axis=1)

    puntajes = np.dot(perfil, Vt)

    # Sagas de los libros que el usuario ya eligió como favoritos: se
    # excluyen también, no solo las que se repiten entre recomendaciones.
    sagas_de_favoritos = set()
    for libro_id in favoritos.ids_libros:
        puntajes[libro_id - 1] = -np.inf
        fila = books.loc[books["book_id"] == libro_id, "title"]
        if not fila.empty:
            saga = extraer_saga(fila.values[0])
            if saga is not None:
                sagas_de_favoritos.add(saga)

    ids_finales = _armar_top_sin_sagas_repetidas(puntajes, sagas_iniciales=sagas_de_favoritos)

    # Para cada libro recomendado, buscamos cuál de los favoritos elegidos
    # es el más "parecido" en el espacio latente, para poder explicar
    # la recomendación ("te lo sugerimos porque te gustó X").
    titulos_por_id = books.set_index("book_id")["title"]
    razon_por_libro = {}
    for libro_id in ids_finales:
        vector_libro = Vt[:, libro_id - 1]
        mejor_favorito = None
        mejor_similitud = -1
        for fav_id in favoritos.ids_libros:
            sim = similitud_coseno(vector_libro, Vt[:, fav_id - 1])
            if sim > mejor_similitud:
                mejor_similitud = sim
                mejor_favorito = fav_id
        razon_por_libro[libro_id] = titulos_por_id.get(mejor_favorito, "tus gustos")

    resultado = books[books["book_id"].isin(ids_finales)][
        ["book_id", "title", "authors", "image_url", "average_rating"]
    ].copy()
    resultado["porque"] = resultado["book_id"].map(razon_por_libro)
    return resultado.to_dict(orient="records")


def _armar_top_sin_sagas_repetidas(puntajes, top_n=10, sagas_iniciales=None):
    """Recorre los libros ordenados por puntaje de mayor a menor, y va
    armando la lista final saltando cualquier libro cuya saga ya haya
    sido incluida antes (así evitamos recomendar 5 tomos de lo mismo),
    o cuya saga esté en sagas_iniciales (libros que el usuario ya eligió)."""
    todos_ordenados = np.argsort(puntajes)[::-1]

    sagas_ya_usadas = set(sagas_iniciales) if sagas_iniciales else set()
    ids_finales = []

    for indice in todos_ordenados:
        libro_id = int(indice) + 1
        fila = books.loc[books["book_id"] == libro_id, "title"]
        if fila.empty:
            continue
        titulo = fila.values[0]
        saga = extraer_saga(titulo)

        if saga is not None and saga in sagas_ya_usadas:
            continue

        if saga is not None:
            sagas_ya_usadas.add(saga)

        ids_finales.append(libro_id)

        if len(ids_finales) == top_n:
            break

    return ids_finales