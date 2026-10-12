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

En el modo local, el PIN inicial para Atención es `1234` (el API local solo escucha en `127.0.0.1`). No reutilices ese PIN en Vercel; ahí `STAFF_PIN` debe ser distinto y seguro.

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

## Despliegue en Vercel

El modo local continúa usando SQLite. En Vercel se usa PostgreSQL porque el almacenamiento del filesystem de una función serverless no es persistente. El backend remoto crea sus tablas automáticamente en la primera petición. La fecha de reinicio diario usa `QUEUE_TIMEZONE` (por defecto `America/Mexico_City`).

1. Sube el proyecto a un repositorio GitHub y conéctalo a Vercel.
2. En Vercel, importa el repositorio. Configura el proyecto como **Services** y conserva la raíz de cada servicio indicada en `vercel.json` (`frontend/` y `backend/`). Vercel Services permite Angular y FastAPI en el mismo proyecto.
3. Añade una integración PostgreSQL de Neon y configura el secreto `DATABASE_URL` (o `POSTGRES_URL`) para Production, Preview y Development.
4. Añade `STAFF_PIN` como variable secreta de entorno (mínimo 4 caracteres). Usa un PIN que no reutilices en otros servicios. Opcionalmente define `QUEUE_TIMEZONE`, por ejemplo `America/Mexico_City`.
5. Despliega y espera que el build y las funciones estén listos.

Las rutas serán `https://<dominio-asignado>/cliente` y `https://<dominio-asignado>/atencion`. El panel de Atención pide el `STAFF_PIN`; la API también lo verifica al cerrar una ventanilla. Cliente queda público. No subas un archivo `.env` ni escribas los valores de los secretos en GitHub.

Si `STAFF_PIN` falta, el panel no permite iniciar sesión. Si falta la base de datos, la API responde 503 y las pantallas muestran desconexión. El estado SQLite de la computadora no se copia a Neon: al desplegar, la fila remota comienza limpia.


