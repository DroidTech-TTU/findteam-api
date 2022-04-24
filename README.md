# findteam-api
FindTeam backend FastAPI source code repo

## Running

- With Docker
    - Start: `docker-compose up -d`
    - Containers "api" (this repo) and "db" (MariaDB) will be brought up
    - Visit `http://localhost:8080` in browser
    - Stop: `docker-compose down`

## Documentation

Visit https://findteam.2labz.com or bring up your own findteam-api instance and visit /docs or /redoc

To docs export with redoc-cli: `redoc-cli bundle http://localhost:8080/openapi.json`

## Testing
- With Docker db only
    - Start: `docker-compose up db -d`
    - Container "db" (MariaDB) will be brought up
    - Run `pytest` to conduct four unit tests
    - Stop: `docker-compose down db`
