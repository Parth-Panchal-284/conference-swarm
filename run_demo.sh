#!/bin/sh
set -eu
cd "$(dirname "$0")"

if command -v docker >/dev/null 2>&1; then
    if docker ps -a --format '{{.Names}}' | grep -qx 'falkordb-demo'; then
        docker start falkordb-demo >/dev/null 2>&1 || true
    else
        docker run -d --name falkordb-demo -p 6379:6379 -p 3000:3000 falkordb/falkordb:v4.22.0 >/dev/null
    fi
else
    echo "Docker is required to run the local FalkorDB graph."
    exit 1
fi

if [ -x ../patch-conf/bin/streamlit ]; then
    streamlit_bin=../patch-conf/bin/streamlit
elif [ ! -x .venv/bin/streamlit ]; then
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    streamlit_bin=.venv/bin/streamlit
else
    streamlit_bin=.venv/bin/streamlit
fi

if [ -f .env ]; then
    set -a
    . ./.env
    set +a
fi

exec "$streamlit_bin" run app.py --server.headless true
