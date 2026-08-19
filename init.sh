#!/bin/bash
# Prepara el proyecto para correrlo en local: entorno virtual,
# dependencias, archivos de configuración y base de datos.
#
# Se puede correr las veces que haga falta: no pisa un .env que ya
# exista ni toca la base sin confirmación explícita.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Entorno virtual"
if [ -d "venv" ]; then
    echo "    venv/ ya existe, se reutiliza."
else
    python3 -m venv venv
    echo "    Creado."
fi
source venv/bin/activate

# Se instala desde requirements.txt y no desde una lista escrita acá
# adentro: si estuviera duplicada, quedaría desactualizada en cuanto se
# sume una dependencia nueva.
echo "==> Dependencias"
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "    Instaladas."

# El .env se arma copiando el .env.example, que es la fuente de verdad de
# qué variables hacen falta. Así, cuando el proyecto necesite una nueva,
# alcanza con agregarla al .example y este script la trae sola.
echo "==> Archivos de configuración"
if [ -f "backend/.env" ]; then
    echo "    backend/.env ya existe, no se toca."
else
    cp backend/.env.example backend/.env
    echo "    backend/.env creado desde el .env.example."
    echo "    Completá ahí los datos de tu base antes de arrancar."
fi

echo ""
read -p "==> ¿Crear la base de datos desde cero? Esto BORRA la que exista con ese nombre. [s/N] " respuesta
if [[ "$respuesta" =~ ^[sS]$ ]]; then
    read -p "    Usuario de MySQL: " db_user
    read -p "    Nombre de la base [bracket]: " db_name
    db_name="${db_name:-bracket}"

    # Se pide escribir el nombre completo y no un simple "sí": borrar una
    # base entera por haber apretado una tecla de más sería un mal día.
    read -p "    Escribí '$db_name' para confirmar que se puede borrar: " confirmacion
    if [ "$confirmacion" != "$db_name" ]; then
        echo "    No coincide. No se tocó nada."
    else
        mysql -u "$db_user" -p -e "DROP DATABASE IF EXISTS \`$db_name\`; CREATE DATABASE \`$db_name\`;"
        mysql -u "$db_user" -p "$db_name" < schema.sql
        echo "    Base '$db_name' creada con el esquema."
    fi
else
    echo "    Se salteó. Si hace falta, a mano:"
    echo "      mysql -u USUARIO -p -e \"CREATE DATABASE bracket;\""
    echo "      mysql -u USUARIO -p bracket < schema.sql"
fi

echo ""
echo "==> Listo. Para levantar el backend:"
echo "    source venv/bin/activate"
echo "    cd backend && python app.py"
