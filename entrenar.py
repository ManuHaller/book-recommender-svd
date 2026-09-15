import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds

ratings = pd.read_csv("data/ratings.csv")

filas = ratings["user_id"] - 1
columnas = ratings["book_id"] - 1
valores = ratings["rating"]

matriz = csr_matrix((valores, (filas, columnas)))

U, sigma, Vt = svds(matriz, k=50)

np.savez("modelo_svd.npz", U=U, sigma=sigma, Vt=Vt)