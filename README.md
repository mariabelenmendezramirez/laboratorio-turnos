# Laboratorio de turnos

Aplicación local para gestionar turnos diarios de un laboratorio. El frontend usa Angular y el backend usa Python con SQLite. No solicita ni almacena datos personales.

## Requisitos en Windows

- Python 3.10 o posterior. El comando `py` es preferible; también se acepta `python`.
- Node.js compatible con Angular 22 y npm incluido: Node 22.22.3 o posterior dentro de la rama 22, Node 24.15 o posterior dentro de la rama 24, o Node 26+. Se recomienda Node 24 LTS. Referencia: https://angular.dev/reference/versions.
- La primera ejecución necesita conexión a Internet para descargar Angular y sus dependencias.

## Iniciar

Haz doble clic en `Iniciar laboratorio.bat`. El archivo comprueba Python, `py`, Node.js y npm, instala Angular la primera vez y abre dos terminales independientes. Espera a que la terminal de Angular confirme que compiló.

- Cliente: http://localhost:4200/cliente
- Atención (cuatro ventanillas): http://localhost:4200/atencion
- API: http://localhost:8000/api/state

La base SQLite `backend/turnos.sqlite3` se crea automáticamente. Cada fecha local tiene su propio contador; al cambiar el día, la numeración inicia de nuevo en A01. Ambas pantallas consultan la misma API cada dos segundos.

## Operación

En cliente, pulsa **Tomar turno**. Si las cuatro ventanillas están ocupadas, el turno entra a la fila. En atención, **Finalizar** libera esa ventanilla y llama al turno pendiente con el número menor. Una ventanilla libre se mantiene disponible mientras no haya fila.

## Verificaciones realizadas en desarrollo

- Se asignaron A01–A04 a las ventanillas 1–4 en ese orden.
- A05 quedó esperando y, al finalizar la ventanilla 2, A05 se asignó a esa ventanilla.
- Al finalizar sin fila, la ventanilla quedó disponible.
- Se simuló el cambio de fecha en la capa de datos y el siguiente turno volvió a A01.
- `npm run build` compiló el frontend Angular.

## API básica

- `GET /api/state`: estado, ventanillas, fila y próximo número.
- `POST /api/tickets`: emite un turno.
- `POST /api/finish` con `{"window": 1}`: finaliza la atención de la ventanilla indicada.


