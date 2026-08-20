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
    imagen_icono_path VARCHAR(255) NULL
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
    modo ENUM('todos_contra_todos', 'eliminacion') NOT NULL,
    fecha DATE NOT NULL,
    -- El estado es del torneo, no un cálculo sobre sus partidos: un
    -- torneo puede estar planificado sin tener ningún partido todavía,
    -- y uno finalizado no debería volver a abrirse porque alguien
    -- edite un resultado.
    estado ENUM('planificado', 'en_curso', 'finalizado') DEFAULT 'planificado',
    descripcion TEXT NULL,
    lugar VARCHAR(150) NULL
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
