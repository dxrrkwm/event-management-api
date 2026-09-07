# Event Management API

Django REST Framework API with SQLite, token authentication, event registration,
search and email notifications.

## Run

Requires Python 3.12+ and GNU Make (`make` on PATH). From the project folder:

Copy `.env.example` to `.env` once, then run:

```sh
make deps
make run
```

The Makefile uses `.venv` and applies migrations. Django loads `.env` automatically;
the example enables debug mode locally. Existing environment variables take priority.
If needed, choose Python with `make deps PYTHON=python3.12`.

For Docker, start Docker Desktop, copy `.env.example` to `.env`, then run
`make up` instead. Use `make logs` to view logs and `make down` to stop.
Docker has its own persistent database.

## Try the API

Open [Swagger](http://localhost:8000/api/docs/). For each request, click
**Try it out**, fill in the values and click **Execute**.

1. **Sign up:** POST `/api/auth/register/` with:
   ```json
   {"username": "alex", "email": "alex@example.com", "password": "Good-pass-728!"}
   ```
2. **Log in:** POST `/api/auth/login/` with the same username and password.
   Copy the returned token into **Authorize** as `Token <your-token>`.
3. **Create an event:** POST `/api/events/` with:
   ```json
   {
     "title": "Python Meetup",
     "description": "Django talks and coffee",
     "date": "2030-06-10T18:00:00Z",
     "location": "Kyiv"
   }
   ```
   Use a future date. The organizer is assigned automatically. Save the event ID.
4. **View:** GET `/api/events/` or `/api/events/{id}/`. No login is needed.
5. **Edit:** PATCH `/api/events/{id}/` with `{"location": "Lviv"}`.
   PUT accepts all four editable fields. Only the organizer can edit.
6. **Register:** POST `/api/events/{id}/register/` with no body.
   The confirmation email appears in the server terminal or `make logs`.
   Repeating the request returns 400. DELETE the same URL to cancel.
7. **Search:** GET `/api/events/?search=python`. Searches title, description and
   location. Add `&ordering=-date` to show the latest events first.
8. **Delete:** DELETE `/api/events/{id}/`. Only the organizer can delete.
9. **Log out:** POST `/api/auth/logout/`, then clear the token in Swagger's
   **Authorize** dialog.

Replace `{id}` with the actual event ID. To check permissions, create a second
account and authorize with its token: editing or deleting the first user's event
should return 403. Create/register returns 201, reads/updates 200, and
successful deletion/cancellation/logout 204.

Emails print to the console by default. For inbox delivery, configure the SMTP
variables shown in `.env.example` in your `.env` file for local or Docker use.
Restart the local server after changes;
for Docker, run `docker compose up -d --force-recreate web`.

## Tests

```sh
make test
make lint
```

Tests cover authentication, CRUD, permissions, validation, search, registration
and email handling. Use `make format` to format code and `make help` for commands.
The [OpenAPI schema](http://localhost:8000/api/schema/) is also available.
