# Book Recommender SVD

Sistema de recomendación de libros con SVD, entrenado sobre el dataset [goodbooks-10k](https://github.com/zygmuntz/goodbooks-10k) (10.000 libros, 53.424 usuarios, 6 millones de ratings). Incluye frontend en React.

```
.
├── app/
│   └── main.py
├── data/                        # CSVs del dataset (no incluidos, ver abajo)
├── entrenar.py                  # entrena el modelo y lo guarda
├── book-recommender-frontend/
├── modelo_svd.npz                # modelo entrenado (no incluido, se genera)
└── requirements.txt
```

## Cómo funciona

Se arma una matriz usuario x libro con los ratings (la mayoría de las celdas están vacías). Aplicando SVD y quedándose con las 50 dimensiones más importantes, se obtiene una representación de cada usuario y cada libro. Multiplicando esas matrices reducidas se llenan las celdas vacías con una predicción de qué rating le pondría un usuario a un libro que nunca calificó.

## Dos formas de recomendar

- **Por usuario existente** (`GET /recomendar/{usuario_id}`): usa el historial real de ese usuario en el dataset.
- **Por libros favoritos** (`POST /recomendar_por_libros`): para usuarios que no están en el dataset (yo, por ejemplo). Se promedian los vectores de los libros elegidos y se compara ese perfil contra el resto.

## Extras

- **No repite sagas**: si el ranking sugiere varios tomos de la misma saga, o si el usuario ya eligió un tomo como favorito, se descartan los demás tomos. Se detecta por el patrón `(Nombre de Saga, #N)` en el título — no funciona con sagas que no tengan ese formato en el título.
- **Explicación de cada recomendación**: en el modo de favoritos, cada libro sugerido muestra cuál de tus favoritos es más parecido (similitud de coseno).

## Cómo correrlo

1. Bajar `books.csv` y `ratings.csv` de los [releases de goodbooks-10k](https://github.com/zygmuntz/goodbooks-10k/releases) y ponerlos en `data/`.

2. Entrenar el modelo:
```bash
pip install -r requirements.txt
py entrenar.py
```
Genera `modelo_svd.npz`.

3. Levantar la API:
```bash
py -m uvicorn app.main:app --reload
```
Queda en `http://localhost:8000/docs`.

4. Levantar el frontend:
```bash
cd book-recommender-frontend
npm install
npm run dev
```

## Endpoints

| Método | Ruta                     | Descripción                                    |
|--------|--------------------------|------------------------------------------------|                                                    
| GET    | /recomendar/{usuario_id} | Recomendaciones para un usuario del dataset    |
| GET    | /buscar_libros?texto=    | Buscar libros por título                       |
| POST   | /recomendar_por_libros   | Recomendaciones a partir de libros favoritos   |

## Decisiones de diseño

- Se usan 50 dimensiones en vez de las 10.000 posibles, para no sobreajustar a ruido de los datos.
- El modelo se entrena una sola vez (`entrenar.py`) y se guarda en disco, para que la API no tenga que recalcular SVD en cada request.
- El filtro de sagas es una heurística sobre el título, no algo perfecto.

