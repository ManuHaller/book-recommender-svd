import { useState } from 'react'
import {
  TextField, Button, Card, CardMedia, CardContent, Typography,
  Grid, Box, CircularProgress, Chip, List, ListItem, ListItemButton,
  ListItemText, ListItemAvatar, Avatar, Tabs, Tab
} from '@mui/material'

const API = "http://localhost:8000"

function App() {
  const [tab, setTab] = useState(0)

  // ---- Modo 1: por user_id existente ----
  const [usuarioId, setUsuarioId] = useState("1")

  // ---- Modo 2: por libros favoritos ----
  const [textoBusqueda, setTextoBusqueda] = useState("")
  const [sugerencias, setSugerencias] = useState([])
  const [favoritos, setFavoritos] = useState([])

  const [recomendaciones, setRecomendaciones] = useState([])
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState(null)

  const buscarPorUsuario = async () => {
    if (usuarioId.trim() === "") return
    setCargando(true)
    setError(null)
    try {
      const response = await fetch(`${API}/recomendar/${usuarioId}`)
      if (!response.ok) throw new Error("No se pudo obtener recomendaciones")
      setRecomendaciones(await response.json())
    } catch (err) {
      setError(err.message)
      setRecomendaciones([])
    } finally {
      setCargando(false)
    }
  }

  const buscarSugerencias = async (texto) => {
    setTextoBusqueda(texto)
    if (texto.trim().length < 2) {
      setSugerencias([])
      return
    }
    const response = await fetch(`${API}/buscar_libros?texto=${encodeURIComponent(texto)}`)
    const data = await response.json()
    setSugerencias(data)
  }

  const agregarFavorito = (libro) => {
    if (!favoritos.some((f) => f.book_id === libro.book_id)) {
      setFavoritos((prev) => [...prev, libro])
    }
    setTextoBusqueda("")
    setSugerencias([])
  }

  const quitarFavorito = (bookId) => {
    setFavoritos((prev) => prev.filter((f) => f.book_id !== bookId))
  }

  const buscarPorFavoritos = async () => {
    if (favoritos.length === 0) return
    setCargando(true)
    setError(null)
    try {
      const response = await fetch(`${API}/recomendar_por_libros`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids_libros: favoritos.map((f) => f.book_id) })
      })
      if (!response.ok) throw new Error("No se pudo obtener recomendaciones")
      setRecomendaciones(await response.json())
    } catch (err) {
      setError(err.message)
      setRecomendaciones([])
    } finally {
      setCargando(false)
    }
  }

  return (
    <Box sx={{ maxWidth: 900, margin: "50px auto", padding: 2 }}>
      <Typography variant="h4" gutterBottom>
        Recomendador de Libros
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Sistema basado en SVD sobre el dataset goodbooks-10k (53.424 usuarios, 6M de ratings)
      </Typography>

      <Tabs value={tab} onChange={(e, v) => setTab(v)} sx={{ marginTop: 2, marginBottom: 2 }}>
        <Tab label="Por ID de usuario" />
        <Tab label="Por libros que me gustan" />
      </Tabs>

      {tab === 0 && (
        <Box sx={{ display: "flex", gap: 1, marginBottom: 3 }}>
          <TextField
            label="ID de usuario (1 a 53424)"
            type="number"
            value={usuarioId}
            onChange={(e) => setUsuarioId(e.target.value)}
          />
          <Button variant="contained" onClick={buscarPorUsuario}>
            Recomendar
          </Button>
        </Box>
      )}

      {tab === 1 && (
        <Box sx={{ marginBottom: 3 }}>
          <TextField
            label="Buscar un libro que te guste"
            fullWidth
            value={textoBusqueda}
            onChange={(e) => buscarSugerencias(e.target.value)}
          />

          {sugerencias.length > 0 && (
            <List sx={{ bgcolor: "background.paper", border: 1, borderColor: "divider" }}>
              {sugerencias.map((libro) => (
                <ListItemButton key={libro.book_id} onClick={() => agregarFavorito(libro)}>
                  <ListItemAvatar>
                    <Avatar src={libro.image_url} variant="square" />
                  </ListItemAvatar>
                  <ListItemText primary={libro.title} secondary={libro.authors} />
                </ListItemButton>
              ))}
            </List>
          )}

          <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", marginTop: 2 }}>
            {favoritos.map((libro) => (
              <Chip
                key={libro.book_id}
                label={libro.title}
                onDelete={() => quitarFavorito(libro.book_id)}
              />
            ))}
          </Box>

          <Button
            variant="contained"
            sx={{ marginTop: 2 }}
            disabled={favoritos.length === 0}
            onClick={buscarPorFavoritos}
          >
            Recomendarme algo
          </Button>
        </Box>
      )}

      {cargando && <CircularProgress />}
      {error && <Typography color="error">{error}</Typography>}

      <Grid container spacing={2}>
        {recomendaciones.map((libro) => (
          <Grid item xs={12} sm={6} md={4} key={libro.book_id}>
            <Card sx={{ display: "flex", height: "100%" }}>
              <CardMedia
                component="img"
                sx={{ width: 100, objectFit: "cover" }}
                image={libro.image_url}
                alt={libro.title}
              />
              <CardContent>
                <Typography variant="subtitle1">{libro.title}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {libro.authors}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  ⭐ {libro.average_rating}
                </Typography>
                {libro.porque && (
                  <Typography variant="caption" display="block" color="primary">
                    Porque te gustó: {libro.porque}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

export default App