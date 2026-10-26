import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds

ratings = pd.read_csv("data/ratings.csv")

test = ratings.sample(frac=0.2, random_state=42)
train = ratings.drop(test.index)

shape = (ratings["user_id"].max(), ratings["book_id"].max())
u = test["user_id"].values - 1
b = test["book_id"].values - 1
real = test["rating"].values

mu = train["rating"].mean()
media_usuario = train.groupby("user_id")["rating"].mean()
base_test = test["user_id"].map(media_usuario).fillna(mu).values


def rmse(pred):
    return np.sqrt(np.mean((pred - real) ** 2))


def construir(valores):
    return csr_matrix(
        (valores, (train["user_id"] - 1, train["book_id"] - 1)), shape=shape
    )


def predecir(matriz, k, base):
    U, sigma, Vt = svds(matriz, k=k)
    return base + np.sum((U[u] * sigma) * Vt.T[b], axis=1)


print(f"Baseline promedio global: {rmse(np.full(len(real), mu)):.3f}")
print(f"Baseline promedio de usuario: {rmse(np.clip(base_test, 1, 5)):.3f}")

sin_centrar = predecir(construir(train["rating"]), 50, 0)
print(f"SVD sin centrar (k=50): {rmse(sin_centrar):.3f}")

centrado = train["rating"] - train["user_id"].map(media_usuario)
matriz_centrada = construir(centrado)
for k in [10, 25, 50, 100]:
    pred = np.clip(predecir(matriz_centrada, k, base_test), 1, 5)
    print(f"SVD centrado (k={k}): {rmse(pred):.3f}")