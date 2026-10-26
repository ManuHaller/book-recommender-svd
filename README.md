# Book Recommender SVD

Sistema de recomendación de libros con SVD, entrenado sobre el dataset [goodbooks-10k](https://github.com/zygmuntz/goodbooks-10k) (10.000 libros, 53.424 usuarios, 6 millones de ratings). Incluye frontend en React.

```
.
├── app/
│   └── main.py
├── data/                        # CSVs del dataset (no incluidos, ver abajo)
├── entrenar.py                  # entrena el modelo y lo guarda
├── validar.py                   # evalúa el modelo (RMSE vs baseline)
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

## Evaluación

`validar.py` esconde un 20% de los ratings, entrena con el resto y compara las predicciones contra los ratings reales (RMSE, en estrellas), junto a un baseline que siempre predice el promedio.

| Versión                                 | RMSE  |
|-----------------------------------------|-------|
| SVD sin centrar (como en `entrenar.py`) | 3.473 |
| Baseline: promedio global               | 0.990 |
| Baseline: promedio de cada usuario      | 0.893 |
| SVD centrado por promedio de usuario    | 0.875 |

Los libros sin calificar valen 0 en la matriz y el SVD los toma como ratings reales, lo que sesga las predicciones hacia abajo. Restar el promedio de cada usuario antes del SVD (y sumarlo al predecir) baja el error de forma notable. Esta mejora todavía no está aplicada en `entrenar.py` ni en la API.

Casi toda la mejora sobre el promedio global viene de ajustar por el promedio de cada usuario; el SVD agrega una mejora modesta. El RMSE mide la nota exacta, pero para recomendar importa más el orden de los libros. El modo de favoritos usa similitud de coseno y no está cubierto por esta métrica.
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

- Se usan 50 dimensiones en vez de las 10.000 posibles, para reducir ruido y costo de cálculo. Probé k = 10, 25, 50 y 100: el RMSE varía entre 0.875 y 0.878, sin diferencias relevantes.
- El modelo se entrena una sola vez (`entrenar.py`) y se guarda en disco, para que la API no tenga que recalcular SVD en cada request.
- El filtro de sagas es una heurística sobre el título, no algo perfecto.

