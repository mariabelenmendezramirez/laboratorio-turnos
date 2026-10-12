import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Subscription, interval, startWith, switchMap } from 'rxjs';

type WindowState = { window: number; ticket: string | null };
type QueueState = { date: string; lastNumber: number; windows: WindowState[]; waiting: string[]; nextTicket: string };
const API_URL = 'http://127.0.0.1:8000/api';

@Component({
  selector: 'app-root', standalone: true, imports: [CommonModule],
  template: `
    <header class="topbar"><a class="brand" href="/cliente"><span class="brand-mark">＋</span><span>LABORATORIO <b>CLÍNICO</b></span></a><nav><a [class.active]="screen==='cliente'" href="/cliente">Cliente</a><a [class.active]="screen==='atencion'" href="/atencion">Atención</a></nav></header>
    <main *ngIf="screen==='cliente'" class="client-layout">
      <section class="client-card"><div class="eyebrow"><span class="live-dot"></span> SISTEMA DE TURNOS</div><h1>Bienvenido</h1><p class="lead">Toma tu turno y espera a que te llamemos.</p>
        <button class="take-button" (click)="takeTicket()" [disabled]="busy">{{busy ? 'Asignando…' : 'Tomar turno'}} <span>→</span></button>
        <p class="error" *ngIf="error">{{error}}</p>
        <div class="ticket-box" *ngIf="myTicket"><span class="muted-label">TU TURNO</span><strong>{{myTicket}}</strong><p *ngIf="myWindow">Tu turno es {{myTicket}}. Pasa a la <b>ventanilla {{myWindow}}</b>.</p><p *ngIf="!myWindow">Espera a que te llamen. Te avisaremos en la pantalla.</p></div>
        <div class="ticket-box placeholder" *ngIf="!myTicket"><span class="ticket-icon">01</span><span>Tu turno aparecerá aquí</span></div>
      </section>
      <aside class="info-card"><div class="info-icon">◷</div><h2>¿Cómo funciona?</h2><ol><li><span>1</span>Toma un turno con el botón.</li><li><span>2</span>Espera a que aparezca tu número.</li><li><span>3</span>Acude a la ventanilla indicada.</li></ol><div class="wait-count"><span class="live-dot"></span>{{state?.waiting?.length ?? 0}} {{(state?.waiting?.length ?? 0) === 1 ? 'persona' : 'personas'}} esperando</div></aside>
    </main>
    <main *ngIf="screen==='atencion'" class="staff-layout"><div class="page-heading"><div><div class="eyebrow"><span class="live-dot"></span> PANEL DE ATENCIÓN</div><h1>Ventanillas</h1><p class="lead">Gestiona la fila de atención en tiempo real.</p></div><div class="waiting-pill"><span class="live-dot"></span>{{state?.waiting?.length ?? 0}} en espera</div></div>
      <p class="error" *ngIf="error">{{error}}</p>
      <section class="window-grid"><article class="window-card" *ngFor="let item of state?.windows"><div class="window-top"><span>VENTANILLA</span><b>{{item.window}}</b></div><div class="window-body" *ngIf="item.ticket"><span class="muted-label">ATENDIENDO AHORA</span><strong>{{item.ticket}}</strong><p>Cliente <b>{{item.ticket}}</b>, pasar a ventanilla {{item.window}}.</p></div><div class="window-body available" *ngIf="!item.ticket"><span class="available-icon">✓</span><strong>Disponible</strong><p>Esperando al siguiente cliente</p></div><button class="finish-button" [disabled]="!item.ticket || finishing===item.window" (click)="finish(item.window)">{{finishing===item.window?'Finalizando…':'Finalizar'}}</button></article></section>
      <section class="queue-strip"><div><span class="queue-icon">☷</span><div><b>Próximos turnos</b><small>Se asignan por orden de llegada</small></div></div><div class="queue-list"><span class="queue-empty" *ngIf="!state?.waiting?.length">No hay clientes esperando</span><span class="queue-ticket" *ngFor="let ticket of state?.waiting">{{ticket}}</span></div></section>
    </main>
    <footer><span>Laboratorio Clínico · Gestión de turnos</span><span class="connection"><i [class.offline]="!connected"></i>{{connected?'Conectado':'Sin conexión con el servidor'}}</span></footer>
  `
})
export class AppComponent implements OnInit, OnDestroy {
  private http = inject(HttpClient);
  screen: 'cliente' | 'atencion' = location.pathname.startsWith('/atencion') ? 'atencion' : 'cliente';
  state: QueueState | null = null;
  connected = false; busy = false; finishing: number | null = null; error = '';
  myTicket = ''; myWindow: number | null = null;
  private poll?: Subscription;
  ngOnInit(): void {
    this.poll = interval(2000).pipe(startWith(0), switchMap(() => this.http.get<QueueState>(`${API_URL}/state`))).subscribe({ next: value => { this.state = value; this.connected = true; this.error = ''; if (this.myTicket) this.myWindow = value.windows.find(w => w.ticket === this.myTicket)?.window ?? null; }, error: () => { this.connected = false; this.error = 'No se pudo conectar con la API. Comprueba que el backend esté iniciado.'; } });
  }
  takeTicket(): void {
    this.busy = true; this.error = '';
    this.http.post<{ticket: string; window: number | null; state: QueueState}>(`${API_URL}/tickets`, {}).subscribe({ next: result => { this.myTicket = result.ticket; this.myWindow = result.window; this.state = result.state; this.busy = false; }, error: () => { this.error = 'No se pudo emitir el turno. Intenta de nuevo.'; this.busy = false; } });
  }
  finish(window: number): void {
    this.finishing = window; this.error = '';
    this.http.post<{state: QueueState}>(`${API_URL}/finish`, {window}).subscribe({ next: result => { this.state = result.state; this.finishing = null; }, error: () => { this.error = 'No se pudo finalizar la atención.'; this.finishing = null; } });
  }
  ngOnDestroy(): void { this.poll?.unsubscribe(); }
}

