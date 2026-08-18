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

## Estado

En desarrollo. Este README se actualiza a medida que el proyecto avanza.
