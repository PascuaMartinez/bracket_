-- =====================================================================
-- Bracket -- modelo de datos
--
-- Este archivo crea el esquema desde cero. Arranca con el núcleo del
-- dominio: jugadores, personajes, torneos y partidos, que es lo mínimo
-- para el primer formato (todos contra todos). Los formatos con grupos
-- y eliminación necesitan más tablas y se agregan cuando se implementan.
-- =====================================================================

CREATE TABLE jugador (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    fecha_nacimiento DATE NULL,
    -- Las imágenes se guardan como REFERENCIA (una ruta o una URL), no
    -- como binario dentro de la base. Guardar archivos en MySQL infla el
    -- tamaño, encarece los backups y obliga a que cada lectura del
    -- jugador arrastre la imagen entera aunque no se vaya a mostrar.
    imagen_vertical_path VARCHAR(255) NULL,
    imagen_icono_path VARCHAR(255) NULL,
    -- Un jugador oculto desaparece de los listados, del ranking y de las
    -- estadísticas que nombran a alguien, pero sus partidos siguen
    -- existiendo: un torneo es un hecho que ocurrió, y borrar a un
    -- participante dejaría partidos con un solo jugador.
    --
    -- Se oculta en vez de borrarse porque el dato es un nombre de pila y
    -- equivocarse de botón es más probable que necesitar que el nombre
    -- desaparezca de la base. Un borrado real, si alguna vez hace falta,
    -- es una operación aparte.
    oculto BOOLEAN NOT NULL DEFAULT FALSE
);

-- Los personajes del juego. Se modelan como entidad propia y no como un
-- texto libre dentro del partido: así se puede preguntar cosas como con
-- qué personaje gana más un jugador, o qué enfrentamientos son parejos,
-- sin depender de que el nombre esté escrito siempre igual.
CREATE TABLE peleador (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    imagen_icono_path VARCHAR(255) NULL
);

CREATE TABLE torneo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    modo ENUM('todos_contra_todos', 'eliminacion', 'rey_de_la_cancha',
              'grupos_eliminacion') NOT NULL,
    fecha DATE NOT NULL,
    -- El estado es del torneo, no un cálculo sobre sus partidos: un
    -- torneo puede estar planificado sin tener ningún partido todavía,
    -- y uno finalizado no debería volver a abrirse porque alguien
    -- edite un resultado.
    estado ENUM('planificado', 'en_curso', 'finalizado') DEFAULT 'planificado',
    descripcion TEXT NULL,
    lugar VARCHAR(150) NULL,
    -- Solo para rey de la cancha: con cuántas vidas arranca cada uno.
    vidas_iniciales INT NULL,
    -- Solo para grupos + eliminación: cuántos clasifican en total a la
    -- fase final. Se guarda el total y no cuántos por grupo porque puede
    -- no dividirse parejo -- 5 cupos en 2 grupos son 3 y 2.
    cupos_eliminacion INT NULL
);

-- La participación de un jugador en un torneo es una entidad, no una
-- lista de ids adentro del torneo. Tiene identidad propia porque otras
-- tablas necesitan colgar información DE esa participación (el grupo que
-- le tocó, las vidas que le quedan), y esos datos no pertenecen ni al
-- jugador ni al torneo por separado.
CREATE TABLE torneo_jugador (
    id INT AUTO_INCREMENT PRIMARY KEY,
    torneo_id INT NOT NULL,
    jugador_id INT NOT NULL,
    FOREIGN KEY (torneo_id) REFERENCES torneo(id),
    FOREIGN KEY (jugador_id) REFERENCES jugador(id),
    -- Un jugador no puede anotarse dos veces al mismo torneo.
    UNIQUE (torneo_id, jugador_id)
);

CREATE TABLE partido (
    id INT AUTO_INCREMENT PRIMARY KEY,
    torneo_id INT NOT NULL,
    jugador1_id INT NOT NULL,
    jugador2_id INT NULL,
    -- NULL mientras no se jugó. El ganador es una referencia y no un
    -- booleano tipo "ganó el jugador 1" para que la consulta de "cuántos
    -- ganó tal jugador" sea directa, sin importar de qué lado estuvo.
    ganador_id INT NULL,

    -- Qué personaje usó cada uno. Es opcional: en un torneo en vivo el
    -- dato se carga si hay tiempo, y las estadísticas que dependen de él
    -- simplemente no aparecen cuando falta.
    jugador1_peleador_id INT NULL,
    jugador2_peleador_id INT NULL,

    -- Cuántas rondas duró el partido (2 = barrida, 3 = cerrado). También
    -- opcional, por el mismo motivo.
    rondas_jugadas INT NULL,

    -- El orden en que se juegan. Se guarda explícito y no se deduce de la
    -- fecha porque varios partidos de una misma noche comparten fecha, y
    -- el orden importa para reconstruir cómo se dio el torneo.
    orden INT NULL,
    jornada INT NULL,

    -- En qué ronda del cuadro se juega: 1 es la primera, y la última es la
    -- final. Se numera desde el principio y no desde el final ("octavos",
    -- "cuartos") porque eso depende de cuántos jugadores haya, y el mismo
    -- número significaría cosas distintas en cada torneo. El nombre de la
    -- ronda se deduce después, mirando cuántos partidos tiene.
    ronda INT NULL,

    -- Un partido sin rival: el jugador pasa de ronda sin jugar, porque la
    -- cantidad de participantes no completaba el cuadro. Se guarda como
    -- partido y no como una lista aparte para que el avance del cuadro
    -- tenga una sola forma de averiguar quién pasó: mirar los partidos de
    -- la ronda. Por eso jugador2_id admite NULL.
    es_pase_libre BOOLEAN NOT NULL DEFAULT FALSE,

    estado ENUM('pendiente', 'en_curso', 'finalizado', 'pospuesto') DEFAULT 'pendiente',
    fecha_jugado DATETIME NULL,

    FOREIGN KEY (torneo_id) REFERENCES torneo(id),
    FOREIGN KEY (jugador1_id) REFERENCES jugador(id),
    FOREIGN KEY (jugador2_id) REFERENCES jugador(id),
    FOREIGN KEY (ganador_id) REFERENCES jugador(id),
    FOREIGN KEY (jugador1_peleador_id) REFERENCES peleador(id),
    FOREIGN KEY (jugador2_peleador_id) REFERENCES peleador(id)
);


-- Estado de cada jugador en un torneo de rey de la cancha: cuántas vidas
-- le quedan, en qué lugar de la cola está y si ya quedó eliminado.
--
-- Va en su propia tabla y no como columnas de torneo_jugador porque solo
-- aplica a un formato: sumarle esas columnas a todos los torneos dejaría
-- la mayoría en NULL sin significar nada.
CREATE TABLE torneo_jugador_vidas (
    torneo_jugador_id INT PRIMARY KEY,
    vidas INT NOT NULL,
    -- La posición en la cola cambia todo el tiempo: el que pierde vuelve
    -- al final. Se guarda como número y se reordena, en vez de mover
    -- filas.
    posicion_cola INT NULL,
    en_cancha BOOLEAN NOT NULL DEFAULT FALSE,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    -- En qué orden fue cayendo cada uno. Sirve para la tabla final: el
    -- que aguantó hasta el final vale más que el primero en irse.
    orden_eliminacion INT NULL,
    FOREIGN KEY (torneo_jugador_id) REFERENCES torneo_jugador(id)
);


-- Usuarios que pueden modificar datos. Todo lo demás -- ver torneos,
-- tablas y estadísticas -- es público: la app está pensada para que el
-- grupo mire los resultados, y pedir cuenta para eso sería un obstáculo
-- sin motivo.
CREATE TABLE usuario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_usuario VARCHAR(50) NOT NULL UNIQUE,
    -- El hash de la contraseña, nunca la contraseña. Si alguien accede a
    -- la base no puede leer las claves, y tampoco puede el propio dueño
    -- del sistema. El campo es largo porque un hash moderno con su sal y
    -- sus parámetros ocupa bastante más que la contraseña original.
    password_hash VARCHAR(255) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Los grupos de un torneo de grupos + eliminación.
CREATE TABLE grupo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    torneo_id INT NOT NULL,
    nombre VARCHAR(50) NOT NULL,
    FOREIGN KEY (torneo_id) REFERENCES torneo(id)
);

-- A qué grupo le tocó cada participante, y si clasificó.
--
-- Cuelga de torneo_jugador y no de jugador porque es un dato de ESA
-- participación: el mismo jugador puede estar en el grupo A de un torneo
-- y en el B de otro.
CREATE TABLE torneo_jugador_grupo (
    torneo_jugador_id INT NOT NULL,
    grupo_id INT NOT NULL,
    -- NULL mientras la fase de grupos no terminó: todavía no se sabe.
    clasificado BOOLEAN NULL,
    -- Cuando el organizador decide a mano quién pasa, en vez de que salga
    -- de la tabla. Se marca para poder distinguirlo después: un
    -- clasificado forzado dice algo distinto de uno que ganó su lugar.
    clasificacion_forzada BOOLEAN NOT NULL DEFAULT FALSE,
    observacion TEXT NULL,
    PRIMARY KEY (torneo_jugador_id, grupo_id),
    FOREIGN KEY (torneo_jugador_id) REFERENCES torneo_jugador(id),
    FOREIGN KEY (grupo_id) REFERENCES grupo(id)
);


-- Configuración general del sistema. Una sola fila: los valores son del
-- sistema entero, no de cada usuario.
--
-- Va como tabla con columnas propias y no como una tabla genérica de
-- clave/valor. La genérica ahorra migraciones al agregar opciones, pero
-- guarda todo como texto y deja de servir apenas hace falta validar algo
-- o que un valor tenga tipo. Con pocas opciones que cambian poco, tener
-- las columnas explícitas vale más.
CREATE TABLE configuracion (
    id INT PRIMARY KEY DEFAULT 1,
    nombre_club VARCHAR(100) NOT NULL DEFAULT 'Bracket',
    texto_inicio TEXT NULL,
    texto_formatos TEXT NULL,
    -- Una fila sola: el CHECK impide que alguien inserte una segunda y
    -- deje al sistema sin saber cuál es la buena.
    CONSTRAINT una_sola_fila CHECK (id = 1)
);

INSERT INTO configuracion (id) VALUES (1);


-- Qué estadísticas se muestran. Solo se guardan las OCULTAS: así una
-- estadística nueva aparece visible sin que haya que agregarle una fila,
-- que es el comportamiento razonable por defecto.
CREATE TABLE estadistica_oculta (
    clave VARCHAR(80) PRIMARY KEY
);
