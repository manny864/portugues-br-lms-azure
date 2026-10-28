/**
 * /js/app.js
 * Orquestador SPA principal que conecta AuthService, ProgressService y CourseEngine
 * manejando las vistas dinámicas en index.html:
 * 1. Dashboard de Progreso
 * 2. Vista de Módulo / Lección (Bloques A1-A2, B1-B2, C1-C2)
 * 3. Reproductor Cultural ("Imersão Real" Hub)
 * 4. Práctica Conversacional (Speaking Lab pt-BR)
 * 5. Modal de Gestión de Sesiones Multiusuario & Arquitectura Azure FinOps
 */

import { AuthService } from './auth.js';
import { ProgressService } from './progress.js';
import { CourseEngine } from './engine.js';

class SotaqueApp {
  constructor() {
    this.auth = new AuthService();
    this.progress = new ProgressService(this.auth);
    this.engine = new CourseEngine(this.progress);
    this.activeView = 'dashboard';
  }

  async init() {
    this._initTheme();
    await this.auth.initSession();
    await this.engine.loadCurriculum();

    this.auth.onAuthChange(() => {
      this._renderHeaderUser();
      this.navigateTo(this.activeView);
    });

    this.progress.onProgressChange(() => {
      this._renderHeaderStats();
    });

    this._bindGlobalNavigation();
    this._renderHeaderUser();
    this._renderHeaderStats();
    this._renderSidebarCurriculum();
    this.navigateTo('dashboard');
  }

  _initTheme() {
    const savedTheme = localStorage.getItem('ptbr_lms_theme') || 'dark';
    document.documentElement.classList.toggle('dark', savedTheme === 'dark');
    const themeBtn = document.getElementById('btn-toggle-theme');
    if (themeBtn) {
      themeBtn.textContent = savedTheme === 'dark' ? '☀️ Claro' : '🌙 Oscuro';
      themeBtn.addEventListener('click', () => {
        const isDark = document.documentElement.classList.toggle('dark');
        localStorage.setItem('ptbr_lms_theme', isDark ? 'dark' : 'light');
        themeBtn.textContent = isDark ? '☀️ Claro' : '🌙 Oscuro';
      });
    }
  }

  _bindGlobalNavigation() {
    document.querySelectorAll('[data-nav-view]').forEach(btn => {
      btn.addEventListener('click', () => {
        const view = btn.getAttribute('data-nav-view');
        this.navigateTo(view);
      });
    });

    document.getElementById('btn-open-auth-modal')?.addEventListener('click', () => {
      this._openAuthModal();
    });

    document.getElementById('btn-close-auth-modal')?.addEventListener('click', () => {
      document.getElementById('auth-modal')?.classList.add('hidden');
    });
  }

  _renderHeaderUser() {
    const user = this.auth.getCurrentUserSync();
    const nameEl = document.getElementById('header-user-name');
    const emailEl = document.getElementById('header-user-email');
    if (nameEl) nameEl.textContent = user.name;
    if (emailEl) emailEl.textContent = user.email;
  }

  _renderHeaderStats() {
    const metrics = this.progress.getGlobalMetrics(this.engine.curriculum);
    const streakEl = document.getElementById('header-streak');
    const xpEl = document.getElementById('header-xp');
    const levelEl = document.getElementById('header-level');

    if (streakEl) streakEl.textContent = `🔥 ${metrics.studyStreakDays} días`;
    if (xpEl) xpEl.textContent = `⭐ ${metrics.xpPoints} XP`;
    if (levelEl) levelEl.textContent = `Nivel ${metrics.currentLevel}`;
  }

  _renderSidebarCurriculum() {
    const sidebar = document.getElementById('sidebar-curriculum-tree');
    if (!sidebar || !this.engine.curriculum) return;

    const userState = this.progress.getUserProgress();

    sidebar.innerHTML = this.engine.curriculum.blocks.map(block => `
      <div class="space-y-2">
        <div class="px-3 py-1.5 text-xs font-extrabold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 flex items-center justify-between">
          <span>Bloque ${block.code}</span>
          <span class="text-[10px] opacity-75">${block.cefrRange.join('•')}</span>
        </div>
        <div class="space-y-1">
          ${block.modules.map(mod => mod.lessons.map(les => {
            const done = userState.completedLessons.includes(les.id);
            const isCurrent = this.engine.activeLesson && this.engine.activeLesson.id === les.id && this.activeView === 'lesson';
            return `
              <button type="button" data-sidebar-lesson="${les.id}" class="w-full text-left px-3 py-2.5 rounded-xl text-xs transition flex items-center justify-between gap-2 cursor-pointer ${isCurrent ? 'bg-emerald-600 text-white font-bold shadow-sm' : 'hover:bg-emerald-500/10'}">
                <div class="truncate">
                  <span class="font-mono font-bold">${les.code}</span> • ${les.title}
                </div>
                <span class="shrink-0">${done ? '✅' : '▸'}</span>
              </button>
            `;
          }).join('')).join('')}
        </div>
      </div>
    `).join('');

    sidebar.querySelectorAll('[data-sidebar-lesson]').forEach(btn => {
      btn.addEventListener('click', () => {
        const lessonId = btn.getAttribute('data-sidebar-lesson');
        this.openLesson(lessonId);
      });
    });
  }

  openLesson(lessonId) {
    const found = this.engine.findLessonById(lessonId);
    if (found) {
      this.engine.activeLesson = found.lesson;
      this.engine.activeBlock = found.block;
    }
    this.navigateTo('lesson');
  }

  navigateTo(view) {
    this.engine.stopAudio();
    this.activeView = view;

    document.querySelectorAll('[data-nav-view]').forEach(btn => {
      const isMatch = btn.getAttribute('data-nav-view') === view;
      btn.classList.toggle('bg-emerald-600', isMatch);
      btn.classList.toggle('text-white', isMatch);
    });

    this._renderSidebarCurriculum();
    const mainContainer = document.getElementById('spa-main-view');
    if (!mainContainer) return;

    if (view === 'dashboard') {
      this._renderDashboardView(mainContainer);
    } else if (view === 'lesson') {
      const targetId = this.engine.activeLesson ? this.engine.activeLesson.id : 'les-a1-1';
      this.engine.renderLessonView(mainContainer, targetId);
    } else if (view === 'imersao') {
      this._renderImersaoHubView(mainContainer);
    } else if (view === 'speaking') {
      this._renderSpeakingLabView(mainContainer);
    } else if (view === 'azure-arch') {
      this._renderAzureArchitectureView(mainContainer);
    }
  }

  _renderDashboardView(container) {
    const user = this.auth.getCurrentUserSync();
    const metrics = this.progress.getGlobalMetrics(this.engine.curriculum);
    const userState = this.progress.getUserProgress();

    container.innerHTML = `
      <div class="space-y-8 pb-12">
        <!-- Hero Banner de Bienvenida -->
        <div class="rounded-2xl p-6 md:p-8 bg-gradient-to-r from-emerald-900 via-emerald-800 to-teal-900 text-white shadow-xl relative overflow-hidden">
          <div class="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div class="space-y-2 max-w-2xl">
              <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-amber-400 text-slate-950">
                🇧🇷 Portugués Brasileño Contrastivo para Hispanohablantes
              </div>
              <h1 class="text-2xl md:text-3xl font-extrabold">Bem-vindo(a), ${user.name}!</h1>
              <p class="text-sm text-emerald-100 leading-relaxed">
                Tu árbol de progreso está sincronizado para <strong>${user.email}</strong>. Avanza desde la supervivencia cotidiana (A1-A2) hasta el dominio del <em>Futuro do Subjuntivo</em> (B1-B2) y el <em>Infinitivo Pessoal & Crase</em> (C1-C2).
              </p>
            </div>
            <div class="flex flex-wrap gap-3">
              <button id="btn-dash-resume-lesson" class="px-5 py-3 rounded-xl font-bold bg-amber-400 hover:bg-amber-300 text-slate-950 shadow-md transition cursor-pointer">
                ▶ Continuar Lección (${userState.lastAudioPlayed?.lessonId === 'les-b1-1' ? 'B1.1' : 'A1.1'})
              </button>
              <button id="btn-dash-switch-user" class="px-4 py-3 rounded-xl font-semibold bg-white/10 hover:bg-white/20 text-white text-xs transition cursor-pointer">
                👥 Cambiar Usuario / Sesión
              </button>
            </div>
          </div>
        </div>

        <!-- KPIs de Progreso por Usuario -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="surface-card rounded-2xl p-5 space-y-1">
            <span class="text-xs opacity-70 font-semibold uppercase">Nivel Actual MCER</span>
            <div class="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400">${metrics.currentLevel}</div>
            <div class="text-xs opacity-75">${metrics.lessonProgressPct}% del currículo completado</div>
          </div>
          <div class="surface-card rounded-2xl p-5 space-y-1">
            <span class="text-xs opacity-70 font-semibold uppercase">Lecciones & Quizzes</span>
            <div class="text-2xl font-extrabold">${metrics.completedLessonsCount}/${metrics.totalLessons} lecciones</div>
            <div class="text-xs opacity-75">${metrics.completedExercisesCount} ejercicios • Promedio ${metrics.avgQuizScore}%</div>
          </div>
          <div class="surface-card rounded-2xl p-5 space-y-1">
            <span class="text-xs opacity-70 font-semibold uppercase">Racha & Experiencia</span>
            <div class="text-2xl font-extrabold text-amber-500">🔥 ${metrics.studyStreakDays} días</div>
            <div class="text-xs opacity-75">⭐ ${metrics.xpPoints} XP • ${metrics.flashcardsCount} flashcards dominadas</div>
          </div>
          <div class="surface-card rounded-2xl p-5 space-y-1">
            <span class="text-xs opacity-70 font-semibold uppercase">Último Audio Reproducido</span>
            <div class="text-sm font-bold truncate">${metrics.lastAudioPlayed?.title || 'Imersão A1'}</div>
            <div class="text-xs opacity-75">Velocidad ${metrics.lastAudioPlayed?.playbackRate || 1}x • Posición 00:${String(metrics.lastAudioPlayed?.timestampSeconds || 0).padStart(2, '0')}</div>
          </div>
        </div>

        <!-- Los 3 Bloques Curriculares (A1-A2, B1-B2, C1-C2) -->
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-extrabold">Mapa Completo del Currículo (A1 → C2)</h2>
            <span class="text-xs opacity-75">Impulsado dinámicamente por <code>/data/curriculum.json</code></span>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            ${this.engine.curriculum.blocks.map(block => `
              <div class="surface-card rounded-2xl p-6 flex flex-col justify-between space-y-5 border-t-4 border-emerald-500">
                <div class="space-y-3">
                  <div class="flex items-center justify-between">
                    <span class="px-3 py-1 rounded-full text-xs font-extrabold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">
                      Niveles ${block.code}
                    </span>
                    <span class="text-xs font-semibold opacity-70">${block.modules[0].lessons.length} lecciones activas</span>
                  </div>
                  <h3 class="text-lg font-extrabold">${block.title}</h3>
                  <p class="text-xs opacity-80 leading-relaxed">${block.description}</p>

                  <div class="space-y-1.5 pt-2">
                    <div class="text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400">Foco Gramatical y Fonético:</div>
                    <ul class="text-xs space-y-1 opacity-85">
                      ${block.grammarSummary.slice(0, 3).map(g => `<li>• ${g}</li>`).join('')}
                    </ul>
                  </div>
                </div>

                <div class="space-y-2 pt-4 border-t border-emerald-500/15">
                  <div class="text-xs font-bold opacity-75">Lecciones Jugables del Bloque:</div>
                  ${block.modules.map(m => m.lessons.map(l => {
                    const done = userState.completedLessons.includes(l.id);
                    return `
                      <button type="button" data-open-lesson="${l.id}" class="w-full text-left p-3 rounded-xl surface-elevated hover:border-emerald-500 transition flex items-center justify-between gap-2 cursor-pointer">
                        <div>
                          <div class="text-xs font-bold text-emerald-600 dark:text-emerald-400">${l.code} • ${l.duration}</div>
                          <div class="text-xs font-semibold line-clamp-1">${l.title}</div>
                        </div>
                        <span class="px-2.5 py-1 rounded-lg text-xs font-bold ${done ? 'bg-emerald-600 text-white' : 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300'}">
                          ${done ? '✓ Hecho' : 'Iniciar →'}
                        </span>
                      </button>
                    `;
                  }).join('')).join('')}
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;

    container.querySelectorAll('[data-open-lesson]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.openLesson(btn.getAttribute('data-open-lesson'));
      });
    });

    container.querySelector('#btn-dash-resume-lesson')?.addEventListener('click', () => {
      const lastId = userState.lastAudioPlayed?.lessonId || 'les-a1-1';
      this.openLesson(lastId);
    });

    container.querySelector('#btn-dash-switch-user')?.addEventListener('click', () => {
      this._openAuthModal();
    });
  }

  _renderImersaoHubView(container) {
    const imersoes = this.engine.getAllImersoes();
    container.innerHTML = `
      <div class="space-y-6 pb-12">
        <div class="surface-card rounded-2xl p-6 md:p-8 space-y-2">
          <span class="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400">🎧 Reproductor Cultural Brasileño</span>
          <h1 class="text-2xl font-extrabold">Hub de "Imersão Real" (A1 → C2)</h1>
          <p class="text-sm opacity-80">Escucha Bossa Nova/MPB, podcasts corporativos de São Paulo y debates ejecutivos con control de velocidad (0.75x, 1x, 1.25x), transcripción sincronizada y notas de <em>gírias</em>.</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          ${imersoes.map(im => `
            <div class="surface-card rounded-2xl p-6 flex flex-col justify-between space-y-4">
              <div class="space-y-2">
                <div class="flex items-center justify-between">
                  <span class="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">Bloque ${im.blockCode} • ${im.lessonCode}</span>
                  <span class="text-xs opacity-70">${im.type}</span>
                </div>
                <h3 class="text-lg font-bold">${im.title}</h3>
                <p class="text-xs opacity-80">${im.culturalContext}</p>
              </div>
              <div class="space-y-2 pt-3 border-t border-emerald-500/15">
                <div class="text-xs font-semibold text-amber-600 dark:text-amber-400">Gírias destacadas: ${im.giriasNotes.map(g => g.term).join(' • ')}</div>
                <button type="button" data-imersao-goto="${im.lessonId}" class="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition cursor-pointer">
                  Abrir Reproductor Sincronizado en Lección ${im.lessonCode} →
                </button>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    container.querySelectorAll('[data-imersao-goto]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.openLesson(btn.getAttribute('data-imersao-goto'));
      });
    });
  }

  _renderSpeakingLabView(container) {
    const prompts = this.engine.getAllSpeakingPrompts();
    const userState = this.progress.getUserProgress();

    container.innerHTML = `
      <div class="space-y-6 pb-12">
        <div class="surface-card rounded-2xl p-6 md:p-8 space-y-2">
          <span class="px-3 py-1 rounded-full text-xs font-bold bg-rose-500/15 text-rose-600 dark:text-rose-400">🎙️ Web Speech API (pt-BR) + Azure AI Speech Ready</span>
          <h1 class="text-2xl font-extrabold">Laboratorio de Práctica Conversacional y Pronunciación</h1>
          <p class="text-sm opacity-80">Entrena los fonemas exclusivos del portugués brasileño (nasales <code>ão/ões</code>, palatalización <code>/dʒi/</code> y <code>/tʃi/</code>, vocales abiertas <code>/ɛ/ /ɔ/</code> y <code>R</code> aspirada).</p>
        </div>

        <div class="grid grid-cols-1 gap-6">
          ${prompts.map((p, i) => {
            const saved = userState.speakingScores[p.id];
            return `
              <div class="surface-card rounded-2xl p-6 space-y-4">
                <div class="flex items-center justify-between flex-wrap gap-2">
                  <span class="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">Nivel ${p.blockCode} (${p.lessonCode})</span>
                  ${saved ? `<span class="text-xs font-bold text-emerald-500">✓ Precisión registrada: ${saved.accuracy}%</span>` : '<span class="text-xs opacity-65">Sin evaluar aún</span>'}
                </div>
                <h3 class="text-lg font-bold">${i + 1}. ${p.title}</h3>
                <p class="text-xs opacity-80">${p.scenario}</p>
                <div class="surface-elevated p-4 rounded-xl space-y-2">
                  <div class="font-extrabold text-base md:text-lg text-emerald-600 dark:text-emerald-400">"${p.targetPhrasePt}"</div>
                  <div class="text-xs font-mono opacity-75">Guía: [${p.phoneticGuide}]</div>
                  <div class="text-xs opacity-70">Español: "${p.translationEs}"</div>
                </div>
                <div class="flex flex-wrap gap-3">
                  <button type="button" data-tts-lab="${p.targetPhrasePt.replace(/"/g, '&quot;')}" class="px-4 py-2 rounded-xl bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 text-xs font-bold cursor-pointer">
                    🔊 Escuchar Modelo Nativo (pt-BR)
                  </button>
                  <button type="button" data-goto-speaking-lesson="${p.lessonId}" class="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold cursor-pointer">
                    🎙️ Practicar con Micrófono en Lección ${p.lessonCode} →
                  </button>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;

    container.querySelectorAll('[data-tts-lab]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.engine.speakPortuguese(btn.getAttribute('data-tts-lab'), 1.0);
      });
    });

    container.querySelectorAll('[data-goto-speaking-lesson]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.openLesson(btn.getAttribute('data-goto-speaking-lesson'));
      });
    });
  }

  _renderAzureArchitectureView(container) {
    container.innerHTML = `
      <div class="space-y-6 pb-12">
        <div class="surface-card rounded-2xl p-6 md:p-8 space-y-3">
          <span class="px-3 py-1 rounded-full text-xs font-bold bg-blue-500/15 text-blue-600 dark:text-blue-400">☁️ Infraestructura Cloud & FinOps (Terraform Incluido)</span>
          <h1 class="text-2xl font-extrabold">Arquitectura Serverless en Azure + Self-Hosted Runner</h1>
          <p class="text-sm opacity-80">Todo el código Terraform para desplegar esta plataforma y su Self-Hosted GitHub Runner en Azure se encuentra en la carpeta <code>/infra/terraform</code> del proyecto.</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div class="surface-card rounded-2xl p-5 space-y-2">
            <h3 class="font-bold text-emerald-600 dark:text-emerald-400">1. Azure Static Web Apps (SWA)</h3>
            <p class="text-xs opacity-85">Hosting global para HTML5/CSS/JS con SSL gratuito y <strong>Managed Azure Functions</strong> integradas en <code>/api/progress</code>.</p>
          </div>
          <div class="surface-card rounded-2xl p-5 space-y-2">
            <h3 class="font-bold text-emerald-600 dark:text-emerald-400">2. Microsoft Entra External ID</h3>
            <p class="text-xs opacity-85">Autenticación multiusuario integrada con <code>/.auth/login/aad</code> y <code>/.auth/login/google</code> (50,000 MAU gratuitos).</p>
          </div>
          <div class="surface-card rounded-2xl p-5 space-y-2">
            <h3 class="font-bold text-emerald-600 dark:text-emerald-400">3. Azure Cosmos DB (Serverless)</h3>
            <p class="text-xs opacity-85">Base de datos NoSQL particionada por <code>/userId</code> con costo $0 USD/mes en reposo o Free Tier (1000 RU/s y 25 GB gratis).</p>
          </div>
          <div class="surface-card rounded-2xl p-5 space-y-2">
            <h3 class="font-bold text-emerald-600 dark:text-emerald-400">4. Azure Blob Storage + Front Door CDN</h3>
            <p class="text-xs opacity-85">Entrega de audios <code>.opus</code>/<code>.aac</code> (64-96 kbps) e imágenes protegidos mediante SAS Tokens y caché de borde global.</p>
          </div>
          <div class="surface-card rounded-2xl p-5 space-y-2">
            <h3 class="font-bold text-emerald-600 dark:text-emerald-400">5. Azure AI Speech (F0 Free Tier)</h3>
            <p class="text-xs opacity-85">Evaluación de pronunciación fonema por fonema en <code>pt-BR</code> y síntesis neuronal con voces <em>FranciscaNeural</em> y <em>AntonioNeural</em>.</p>
          </div>
          <div class="surface-card rounded-2xl p-5 space-y-2">
            <h3 class="font-bold text-amber-600 dark:text-amber-400">6. GitHub Self-Hosted Runner en Azure</h3>
            <p class="text-xs opacity-85">Desplegado vía Terraform en <strong>Azure Container Apps (ACA)</strong> / ACI con registro automático en el repositorio de GitHub para CI/CD privado.</p>
          </div>
        </div>
      </div>
    `;
  }

  async _openAuthModal() {
    const modal = document.getElementById('auth-modal');
    const listEl = document.getElementById('auth-users-list');
    if (!modal || !listEl) return;

    const users = await this.auth.getAllUsers();
    const current = this.auth.getCurrentUserSync();

    listEl.innerHTML = users.map(u => {
      const progress = this.progress.getUserProgress(u.userId);
      const isCurrent = u.userId === current.userId;
      return `
        <div class="p-3.5 rounded-xl surface-elevated flex items-center justify-between gap-3 border ${isCurrent ? 'border-emerald-500' : 'border-transparent'}">
          <div>
            <div class="font-bold text-sm">${u.name} ${isCurrent ? '<span class="text-xs text-emerald-500">(Activo)</span>' : ''}</div>
            <div class="text-xs opacity-75">${u.email} • Nivel ${progress.currentLevel} • ⭐ ${progress.xpPoints} XP</div>
          </div>
          ${!isCurrent ? `
            <button type="button" data-switch-user="${u.userId}" class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold cursor-pointer">
              Cambiar a esta cuenta
            </button>
          ` : ''}
        </div>
      `;
    }).join('');

    listEl.querySelectorAll('[data-switch-user]').forEach(btn => {
      btn.addEventListener('click', async () => {
        await this.auth.switchUser(btn.getAttribute('data-switch-user'));
        modal.classList.add('hidden');
      });
    });

    const form = document.getElementById('form-new-user');
    if (form) {
      form.onsubmit = async (e) => {
        e.preventDefault();
        const name = document.getElementById('input-user-name')?.value;
        const email = document.getElementById('input-user-email')?.value;
        if (email) {
          await this.auth.loginOrRegister({ name, email });
          form.reset();
          modal.classList.add('hidden');
        }
      };
    }

    document.querySelectorAll('[data-azure-login]').forEach(btn => {
      btn.onclick = () => {
        this.auth.loginWithAzureProvider(btn.getAttribute('data-azure-login'));
      };
    });

    modal.classList.remove('hidden');
  }
}

window.addEventListener('DOMContentLoaded', () => {
  const app = new SotaqueApp();
  app.init();
});
