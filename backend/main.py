"""API FastAPI para el servicio Python de Vercel."""

from hmac import compare_digest
from os import environ

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from cloud_store import finish_window, get_state, take_ticket

app = FastAPI(title="Laboratorio de turnos")


class FinishRequest(BaseModel):
    window: int = Field(ge=1, le=4)


class StaffLogin(BaseModel):
    pin: str = Field(min_length=4, max_length=128)


def verify_staff_pin(pin: str | None) -> None:
    configured_pin = environ.get("STAFF_PIN", "")
    if not configured_pin:
        raise HTTPException(status_code=503, detail="Atención no está configurada. Define STAFF_PIN en el entorno.")
    if pin is None or not compare_digest(pin, configured_pin):
        raise HTTPException(status_code=401, detail="PIN incorrecto.")


@app.get("/api/state")
def state():
    try:
        return get_state()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/tickets", status_code=201)
def create_ticket():
    try:
        return take_ticket()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/staff/auth")
def staff_auth(login: StaffLogin):
    verify_staff_pin(login.pin)
    return {"authenticated": True}


@app.post("/api/finish")
def finish(request: FinishRequest, x_staff_pin: str | None = Header(default=None)):
    verify_staff_pin(x_staff_pin)
    try:
        return finish_window(request.window)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

