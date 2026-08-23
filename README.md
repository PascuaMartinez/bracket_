# Bracket

Gestor de torneos de e-sports para grupos que juegan seguido.

## El problema

Un grupo que organiza torneos con regularidad necesita llevar registro de qué
pasó: quién ganó cada partido, cómo quedaron las posiciones, cómo viene el
historial entre todos. La planilla compartida alcanza para el primer torneo y
se rompe apenas los formatos se complican: un cuadro de eliminación con
repechajes, o un formato donde el orden final no sale de sumar victorias, ya no
entra en filas y columnas.

Bracket resuelve eso: se carga el resultado de cada partido y el sistema se
encarga del resto — armar los cruces, calcular las posiciones, decidir quién
clasifica y acumular el historial.

## Alcance

**Tres formatos de torneo**

- **Todos contra todos** — cada jugador se enfrenta con todos los demás.
- **Grupos + eliminación** — fase de grupos y después cuadro de eliminación
  directa, con repechaje cuando la cantidad de clasificados no completa el
  cuadro.
- **Rey de la cancha** — el que gana se queda en cancha y el que pierde una
  vida vuelve al final de la cola; termina cuando queda uno solo en pie.

**Historial acumulado**

Los torneos suman puntos a una tabla histórica. La tabla es el producto real
del sistema: un torneo puntual se olvida, el acumulado es lo que ordena al
grupo.

**Estadísticas**

Por jugador (rivales, rachas, mejores resultados) y por personaje, incluyendo
qué tan parejos son los enfrentamientos entre dos jugadores.

## Stack

- **Backend** — Python, Flask, MySQL. Arquitectura en capas
  (controller / service / repository).
- **Frontend** — Flask + Jinja2, servido como aplicación aparte que consume la
  API del backend.

## Cómo correrlo

Requiere Python 3 y MySQL.

```bash
./init.sh
```

El script crea el entorno virtual, instala las dependencias, arma el
archivo de configuración a partir del `.env.example` y ofrece crear la
base con el esquema. Se puede correr las veces que haga falta: no pisa
un `.env` que ya exista ni toca la base sin confirmación.

Después, completar `backend/.env` con los datos de la base y levantar las
dos aplicaciones, cada una en su terminal:

```bash
source venv/bin/activate
cd backend  && python app.py    # la API, en el puerto 5000
cd frontend && python app.py    # la interfaz, en el puerto 3000
```

## Pruebas

```bash
source venv/bin/activate
cd backend && pytest
```

Las pruebas no necesitan base de datos. La lógica que no depende de nada
externo (el armado del fixture) se prueba directo, y la que lee datos se
prueba sustituyendo los repositorios. Eso es posible porque el acceso a
datos está aislado en su propia capa.

## Usuarios

Ver es público: cualquiera puede mirar torneos, tablas y estadísticas sin
cuenta. Crear y modificar necesita sesión.

El primer usuario se crea desde la máquina donde corre el proyecto:

```bash
source venv/bin/activate
cd backend && python crear_usuario.py
```

Va como script y no como pantalla a propósito: un formulario público para
crear administradores le permitiría a cualquiera darse de alta.

## Estado

En desarrollo. Este README se actualiza a medida que el proyecto avanza.
