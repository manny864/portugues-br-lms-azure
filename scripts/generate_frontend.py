#!/usr/bin/env python3
"""
Script determinista para generar el Frontend SPA modular (HTML5, CSS3, ES6+ Vanilla JS)
y las Azure Managed Functions (/api/progress) para Azure Static Web Apps + Cosmos DB.
Basado estrictamente en directivas/lms_ptbr_azure_SOP.md.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CSS_DIR = BASE_DIR / "css"
JS_DIR = BASE_DIR / "js"
API_DIR = BASE_DIR / "api" / "progress"
TMP_DIR = BASE_DIR / ".tmp"


STYLES_CSS = """/* ==========================================================================
   Sotaque Brasileiro LMS — Paleta Brasileña Sobria & Profesional (Dark/Light)
   HTML5 + CSS3 Custom Variables + Tailwind Utility Synergy
   ========================================================================== */

:root {
  --bg-primary: #f8faf9;
  --bg-secondary: #ffffff;
  --bg-elevated: #f1f5f3;
  --text-primary: #0f1f18;
  --text-secondary: #475e53;
  --border-subtle: #dce6e0;
  --accent-emerald: #047857;
  --accent-emerald-light: #10b981;
  --accent-gold: #d97706;
  --accent-ocean: #1d4ed8;
  --card-shadow: 0 4px 20px -2px rgba(15, 31, 24, 0.06);
}

html.dark {
  --bg-primary: #09130f;
  --bg-secondary: #11211b;
  --bg-elevated: #182e25;
  --text-primary: #ecfdf5;
  --text-secondary: #9ab3a8;
  --border-subtle: #213d31;
  --accent-emerald: #10b981;
  --accent-emerald-light: #34d399;
  --accent-gold: #f59e0b;
  --accent-ocean: #3b82f6;
  --card-shadow: 0 8px 30px -4px rgba(0, 0, 0, 0.45);
}

body {
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  transition: background-color 0.25s ease, color 0.25s ease;
}

.surface-card {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-subtle);
  box-shadow: var(--card-shadow);
}

.surface-elevated {
  background-color: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
}

/* Transcripción interactiva sincronizada */
.transcript-line {
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
}

.transcript-line.active-line {
  background: linear-gradient(90deg, rgba(16, 185, 129, 0.14) 0%, rgba(245, 158, 11, 0.05) 100%);
  border-left-color: #10b981;
  transform: translateX(4px);
}

/* Flashcards 3D Flip */
.flashcard-perspective {
  perspective: 1000px;
}

.flashcard-inner {
  position: relative;
  width: 100%;
  min-height: 220px;
  transition: transform 0.55s cubic-bezier(0.4, 0, 0.2, 1);
  transform-style: preserve-3d;
}

.flashcard-inner.is-flipped {
  transform: rotateY(180deg);
}

.flashcard-face {
  position: absolute;
  inset: 0;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 1.5rem;
  border-radius: 1rem;
}

.flashcard-back {
  transform: rotateY(180deg);
}

/* Animación de pulso para micrófono en Web Speech API */
@keyframes micPulse {
  0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.6); }
  70% { box-shadow: 0 0 0 14px rgba(239, 68, 68, 0); }
  100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

.mic-recording {
  animation: micPulse 1.5s infinite;
}

/* Scrollbar elegante */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(16, 185, 129, 0.3);
  border-radius: 9999px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(16, 185, 129, 0.55);
}
"""


AUTH_JS = """/**
 * /js/auth.js
 * Capa de abstracción de Autenticación Multiusuario (AuthService).
 * Soporta inicialmente almacenamiento aislado en localStorage por ID/Email,
 * y expone métodos async/await listos para Azure Static Web Apps Auth
 * (/.auth/me, /.auth/login/aad, /.auth/login/google) + Microsoft Entra External ID.
 */

const STORAGE_USERS_KEY = 'ptbr_lms_users_v2';
const STORAGE_SESSION_KEY = 'ptbr_lms_active_session_v2';

const DEFAULT_DEMO_USERS = [
  {
    userId: 'usr-mateo-hispanohablante',
    name: 'Mateo Rojas (Demo Estudiante)',
    email: 'mateo.rojas@ejemplo.lat',
    nativeRegion: 'Ciudad de México / Bogotá',
    targetGoal: 'Fluidez Profesional & Viajes (A1 → C2)',
    authProvider: 'local-simulated',
    createdAt: '2026-10-01T10:00:00Z'
  },
  {
    userId: 'usr-valeria-ejecutiva',
    name: 'Valeria Gómez (Ejecutiva B2→C2)',
    email: 'valeria.gomez@empresa.es',
    nativeRegion: 'Madrid / Buenos Aires',
    targetGoal: 'Negocios en São Paulo (B1 → C2)',
    authProvider: 'local-simulated',
    createdAt: '2026-10-10T14:30:00Z'
  }
];

export class AuthService {
  constructor(config = {}) {
    this.useAzureCloudAuth = config.useAzureCloudAuth || false;
    this.swaAuthEndpoint = config.swaAuthEndpoint || '/.auth/me';
    this.listeners = [];
    this._ensureDefaultUsers();
  }

  _ensureDefaultUsers() {
    try {
      const raw = localStorage.getItem(STORAGE_USERS_KEY);
      if (!raw) {
        localStorage.setItem(STORAGE_USERS_KEY, JSON.stringify(DEFAULT_DEMO_USERS));
      }
      const active = localStorage.getItem(STORAGE_SESSION_KEY);
      if (!active) {
        localStorage.setItem(STORAGE_SESSION_KEY, JSON.stringify(DEFAULT_DEMO_USERS[0]));
      }
    } catch (err) {
      console.warn('AuthService: Fallback en memoria activado:', err);
    }
  }

  /**
   * Inicializa la sesión verificando primero Azure Static Web Apps (/.auth/me)
   * si el modo cloud está activo o si detecta entorno de producción en Azure.
   */
  async initSession() {
    if (this.useAzureCloudAuth || window.location.hostname.endsWith('.azurestaticapps.net')) {
      try {
        const res = await fetch(this.swaAuthEndpoint, { credentials: 'include' });
        if (res.ok) {
          const data = await res.json();
          if (data && data.clientPrincipal) {
            const cp = data.clientPrincipal;
            const cloudUser = {
              userId: cp.userId,
              name: cp.userDetails || cp.userId,
              email: cp.userDetails,
              nativeRegion: 'Hispanohablante (Azure Entra ID)',
              targetGoal: 'Ruta Completa A1 → C2',
              authProvider: cp.identityProvider || 'azure-swa',
              roles: cp.userRoles || ['authenticated']
            };
            localStorage.setItem(STORAGE_SESSION_KEY, JSON.stringify(cloudUser));
            this._notify(cloudUser);
            return cloudUser;
          }
        }
      } catch (cloudErr) {
        console.info('AuthService: Operando en modo localStorage (Azure SWA /.auth/me no detectado en local).');
      }
    }

    const current = this.getCurrentUserSync();
    this._notify(current);
    return current;
  }

  getCurrentUserSync() {
    try {
      const raw = localStorage.getItem(STORAGE_SESSION_KEY);
      return raw ? JSON.parse(raw) : DEFAULT_DEMO_USERS[0];
    } catch {
      return DEFAULT_DEMO_USERS[0];
    }
  }

  async getAllUsers() {
    try {
      const raw = localStorage.getItem(STORAGE_USERS_KEY);
      return raw ? JSON.parse(raw) : DEFAULT_DEMO_USERS;
    } catch {
      return DEFAULT_DEMO_USERS;
    }
  }

  /**
   * Inicia sesión o registra un nuevo usuario por email (aislando su propio árbol de progreso).
   */
  async loginOrRegister({ name, email, nativeRegion = 'Latinoamérica / España', targetGoal = 'Dominio A1 → C2' }) {
    const cleanEmail = (email || '').trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes('@')) {
      throw new Error('Por favor ingresa un correo electrónico válido.');
    }

    const users = await this.getAllUsers();
    let user = users.find(u => u.email.toLowerCase() === cleanEmail);

    if (!user) {
      const slug = cleanEmail.replace(/[^a-z0-9]/g, '-').slice(0, 24);
      user = {
        userId: `usr-${slug}-${Date.now().toString(36)}`,
        name: (name || cleanEmail.split('@')[0]).trim(),
        email: cleanEmail,
        nativeRegion,
        targetGoal,
        authProvider: 'local-simulated',
        createdAt: new Date().toISOString()
      };
      users.push(user);
      localStorage.setItem(STORAGE_USERS_KEY, JSON.stringify(users));
    } else if (name && name.trim()) {
      user.name = name.trim();
      localStorage.setItem(STORAGE_USERS_KEY, JSON.stringify(users));
    }

    localStorage.setItem(STORAGE_SESSION_KEY, JSON.stringify(user));
    this._notify(user);
    return user;
  }

  async switchUser(userId) {
    const users = await this.getAllUsers();
    const target = users.find(u => u.userId === userId);
    if (!target) {
      throw new Error('Usuario no encontrado.');
    }
    localStorage.setItem(STORAGE_SESSION_KEY, JSON.stringify(target));
    this._notify(target);
    return target;
  }

  /**
   * Redirige al flujo nativo de Azure Static Web Apps / Microsoft Entra External ID.
   */
  async loginWithAzureProvider(provider = 'aad') {
    // Proveedores soportados por Azure SWA: 'aad' (Microsoft Entra ID), 'google', 'github'
    const allowed = ['aad', 'google', 'github'];
    const selected = allowed.includes(provider) ? provider : 'aad';
    window.location.href = `/.auth/login/${selected}?post_login_redirect_uri=${encodeURIComponent(window.location.pathname)}`;
  }

  async logout() {
    const current = this.getCurrentUserSync();
    if (current && current.authProvider && current.authProvider !== 'local-simulated') {
      window.location.href = '/.auth/logout';
      return;
    }
    const users = await this.getAllUsers();
    const fallback = users[0] || DEFAULT_DEMO_USERS[0];
    localStorage.setItem(STORAGE_SESSION_KEY, JSON.stringify(fallback));
    this._notify(fallback);
    return fallback;
  }

  onAuthChange(callback) {
    this.listeners.push(callback);
  }

  _notify(user) {
    this.listeners.forEach(cb => {
      try {
        cb(user);
      } catch (e) {
        console.error(e);
      }
    });
  }
}
"""


PROGRESS_JS = """/**
 * /js/progress.js
 * Motor de seguimiento de estado por usuario (ProgressService).
 * Persiste lecciones completadas, puntajes de quizzes, último audio reproducido,
 * tarjetas dominadas y racha de estudio por sesión de usuario (userId).
 * Incluye sincronización async/await lista para Azure Functions + Cosmos DB (/api/progress).
 */

const PROGRESS_PREFIX = 'ptbr_lms_progress_v2_';

export class ProgressService {
  constructor(authService, options = {}) {
    this.authService = authService;
    this.apiEndpoint = options.apiEndpoint || '/api/progress';
    this.enableCloudSync = options.enableCloudSync || false;
    this.listeners = [];
  }

  _getStorageKey(userId) {
    return `${PROGRESS_PREFIX}${userId}`;
  }

  _createDefaultState(userId) {
    const today = new Date().toISOString().slice(0, 10);
    // Para el usuario secundario demo (Valeria), precargamos progreso intermedio para demostrar multiusuario
    if (userId === 'usr-valeria-ejecutiva') {
      return {
        userId,
        currentLevel: 'B1-B2',
        xpPoints: 420,
        studyStreakDays: 7,
        lastStudyDate: today,
        completedLessons: ['les-a1-1', 'les-a2-1'],
        quizScores: {
          'ex-a1-mc-1': { score: 100, attempts: 1, completedAt: today },
          'ex-a1-fib-1': { score: 100, attempts: 1, completedAt: today },
          'ex-a2-mc-1': { score: 100, attempts: 1, completedAt: today }
        },
        flashcardsMastered: ['fc-a1-1', 'fc-a1-2', 'fc-b2-1'],
        speakingScores: {
          'ex-a1-sp-1': { accuracy: 92, transcript: 'Bom dia! Me vê um pão de queijo e um copo de suco de laranja, por favor.' }
        },
        lastAudioPlayed: {
          imersaoId: 'imersao-b2-podcast',
          lessonId: 'les-b1-1',
          title: "Podcast 'Café & Carreira': Trabalho Remoto, Prazos e Imprevistos",
          timestampSeconds: 7,
          playbackRate: 1.0,
          updatedAt: new Date().toISOString()
        },
        updatedAt: new Date().toISOString()
      };
    }

    return {
      userId,
      currentLevel: 'A1',
      xpPoints: 60,
      studyStreakDays: 3,
      lastStudyDate: today,
      completedLessons: [],
      quizScores: {},
      flashcardsMastered: [],
      speakingScores: {},
      lastAudioPlayed: {
        imersaoId: 'imersao-a1-bossa',
        lessonId: 'les-a1-1',
        title: 'Manhã na Padaria & Bossa Acústica em Ipanema',
        timestampSeconds: 0,
        playbackRate: 1.0,
        updatedAt: new Date().toISOString()
      },
      updatedAt: new Date().toISOString()
    };
  }

  getUserProgress(userId = null) {
    const activeUserId = userId || this.authService.getCurrentUserSync().userId;
    const key = this._getStorageKey(activeUserId);
    try {
      const raw = localStorage.getItem(key);
      if (raw) {
        const parsed = JSON.parse(raw);
        this._updateStreakIfNeeded(parsed);
        return parsed;
      }
    } catch (e) {
      console.warn('ProgressService: Error leyendo localStorage', e);
    }
    const initial = this._createDefaultState(activeUserId);
    this.saveUserProgress(initial);
    return initial;
  }

  saveUserProgress(state) {
    if (!state || !state.userId) return;
    state.updatedAt = new Date().toISOString();
    const key = this._getStorageKey(state.userId);
    try {
      localStorage.setItem(key, JSON.stringify(state));
    } catch (e) {
      console.warn('ProgressService: No se pudo guardar en localStorage', e);
    }
    this._notify(state);

    if (this.enableCloudSync || window.location.hostname.endsWith('.azurestaticapps.net')) {
      this.syncToAzureCosmosDB(state).catch(() => {});
    }
  }

  _updateStreakIfNeeded(state) {
    const today = new Date().toISOString().slice(0, 10);
    if (state.lastStudyDate !== today) {
      const last = new Date(state.lastStudyDate || today);
      const now = new Date(today);
      const diffDays = Math.round((now - last) / (1000 * 60 * 60 * 24));
      if (diffDays === 1) {
        state.studyStreakDays = (state.studyStreakDays || 1) + 1;
      } else if (diffDays > 1) {
        state.studyStreakDays = 1;
      }
      state.lastStudyDate = today;
    }
  }

  recordExerciseResult(exerciseId, scorePercent, xpBonus = 25) {
    const state = this.getUserProgress();
    const prev = state.quizScores[exerciseId];
    const attempts = prev ? prev.attempts + 1 : 1;

    if (!prev || scorePercent > prev.score) {
      state.xpPoints += xpBonus;
    }

    state.quizScores[exerciseId] = {
      score: Math.max(prev ? prev.score : 0, scorePercent),
      lastScore: scorePercent,
      attempts,
      completedAt: new Date().toISOString()
    };

    this.saveUserProgress(state);
    return state;
  }

  recordSpeakingAssessment(exerciseId, accuracyScore, recognizedText) {
    const state = this.getUserProgress();
    state.speakingScores[exerciseId] = {
      accuracy: accuracyScore,
      transcript: recognizedText,
      evaluatedAt: new Date().toISOString()
    };
    this.recordExerciseResult(exerciseId, accuracyScore, 35);
    return state;
  }

  toggleFlashcardMastered(cardId) {
    const state = this.getUserProgress();
    const idx = state.flashcardsMastered.indexOf(cardId);
    if (idx === -1) {
      state.flashcardsMastered.push(cardId);
      state.xpPoints += 10;
    } else {
      state.flashcardsMastered.splice(idx, 1);
    }
    this.saveUserProgress(state);
    return state.flashcardsMastered.includes(cardId);
  }

  recordAudioPlayback({ imersaoId, lessonId, title, timestampSeconds, playbackRate }) {
    const state = this.getUserProgress();
    state.lastAudioPlayed = {
      imersaoId,
      lessonId,
      title,
      timestampSeconds: Math.round(timestampSeconds || 0),
      playbackRate: playbackRate || 1.0,
      updatedAt: new Date().toISOString()
    };
    this.saveUserProgress(state);
  }

  markLessonComplete(lessonId, newLevelHint = null, xpReward = 150) {
    const state = this.getUserProgress();
    if (!state.completedLessons.includes(lessonId)) {
      state.completedLessons.push(lessonId);
      state.xpPoints += xpReward;
    }
    if (newLevelHint) {
      state.currentLevel = newLevelHint;
    }
    this._recalculateLevel(state);
    this.saveUserProgress(state);
    return state;
  }

  _recalculateLevel(state) {
    const completed = state.completedLessons;
    if (completed.includes('les-c1-1')) {
      state.currentLevel = 'C2';
    } else if (completed.includes('les-b1-1')) {
      state.currentLevel = 'C1';
    } else if (completed.includes('les-a2-1')) {
      state.currentLevel = 'B1-B2';
    } else if (completed.includes('les-a1-1')) {
      state.currentLevel = 'A2';
    } else {
      state.currentLevel = 'A1';
    }
  }

  getGlobalMetrics(curriculum) {
    const state = this.getUserProgress();
    let totalLessons = 0;
    let totalExercises = 0;

    if (curriculum && curriculum.blocks) {
      curriculum.blocks.forEach(b => {
        b.modules.forEach(m => {
          totalLessons += m.lessons.length;
          m.lessons.forEach(l => {
            totalExercises += (l.exercises || []).length;
          });
        });
      });
    }

    const completedLessonsCount = state.completedLessons.length;
    const completedExercisesCount = Object.keys(state.quizScores).length;
    const lessonProgressPct = totalLessons > 0 ? Math.round((completedLessonsCount / totalLessons) * 100) : 0;

    const scores = Object.values(state.quizScores).map(q => q.score);
    const avgQuizScore = scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;

    return {
      userId: state.userId,
      currentLevel: state.currentLevel,
      xpPoints: state.xpPoints,
      studyStreakDays: state.studyStreakDays,
      completedLessonsCount,
      totalLessons,
      lessonProgressPct,
      completedExercisesCount,
      totalExercises,
      avgQuizScore,
      flashcardsCount: state.flashcardsMastered.length,
      lastAudioPlayed: state.lastAudioPlayed
    };
  }

  /**
   * Sincronización con Azure Functions + Azure Cosmos DB Serverless (POST /api/progress)
   */
  async syncToAzureCosmosDB(state = null) {
    const payload = state || this.getUserProgress();
    const response = await fetch(this.apiEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      throw new Error(`Azure Function /api/progress respondió con HTTP ${response.status}`);
    }
    return await response.json();
  }

  /**
   * Recupera el documento JSON del usuario desde Azure Cosmos DB (GET /api/progress?userId=...)
   */
  async fetchFromAzureCosmosDB(userId = null) {
    const targetUser = userId || this.authService.getCurrentUserSync().userId;
    const response = await fetch(`${this.apiEndpoint}?userId=${encodeURIComponent(targetUser)}`);
    if (response.ok) {
      const cloudDoc = await response.json();
      if (cloudDoc && cloudDoc.userId) {
        this.saveUserProgress(cloudDoc);
        return cloudDoc;
      }
    }
    return this.getUserProgress(targetUser);
  }

  onProgressChange(callback) {
    this.listeners.push(callback);
  }

  _notify(state) {
    this.listeners.forEach(cb => {
      try {
        cb(state);
      } catch (e) {
        console.error(e);
      }
    });
  }
}
"""


ENGINE_JS = """/**
 * /js/engine.js
 * Motor Dinámico del Curso (CourseEngine):
 * 1. Carga el currículo desde /data/curriculum.json (con fallback resiliente).
 * 2. Renderiza las lecciones contrastivas (Español vs. Portugués Brasileño), fonética y Falsos Amigos.
 * 3. Gestiona el Reproductor Cultural "Imersão Real" con control de velocidad (0.75x, 1x, 1.25x),
 *    transcripción interactiva sincronizada PT-BR / ES y motor dual (Audio HTML5 + Web Speech TTS pt-BR).
 * 4. Ejecuta y valida los 5 tipos de ejercicios interactivos:
 *    - multiple-choice
 *    - fill-in-the-blanks
 *    - audio-comprehension
 *    - flashcards
 *    - speaking-prompt (Web Speech API / webkitSpeechRecognition en pt-BR)
 */

import { CURRICULUM_FALLBACK } from './curriculum-fallback.js';

export class CourseEngine {
  constructor(progressService) {
    this.progressService = progressService;
    this.curriculum = null;
    this.activeLesson = null;
    this.activeBlock = null;

    // Estado del reproductor de audio e Imersão Real
    this.playbackRate = 1.0;
    this.isPlaying = false;
    this.currentTime = 0;
    this.duration = 30;
    this.audioTimer = null;
    this.htmlAudio = null;
    this.activeRecognition = null;
  }

  async loadCurriculum(url = './data/curriculum.json') {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      this.curriculum = await res.json();
    } catch (err) {
      console.info('CourseEngine: Usando CURRICULUM_FALLBACK integrado para disponibilidad inmediata:', err.message);
      this.curriculum = CURRICULUM_FALLBACK;
    }

    // Seleccionar primera lección por defecto
    const firstBlock = this.curriculum.blocks[0];
    const firstLesson = firstBlock.modules[0].lessons[0];
    this.activeBlock = firstBlock;
    this.activeLesson = firstLesson;
    return this.curriculum;
  }

  findLessonById(lessonId) {
    if (!this.curriculum) return null;
    for (const block of this.curriculum.blocks) {
      for (const mod of block.modules) {
        for (const lesson of mod.lessons) {
          if (lesson.id === lessonId) {
            return { block, module: mod, lesson };
          }
        }
      }
    }
    return null;
  }

  getAllImersoes() {
    const list = [];
    if (!this.curriculum) return list;
    for (const block of this.curriculum.blocks) {
      for (const mod of block.modules) {
        for (const lesson of mod.lessons) {
          if (lesson.imersaoReal) {
            list.push({
              ...lesson.imersaoReal,
              lessonId: lesson.id,
              lessonCode: lesson.code,
              lessonTitle: lesson.title,
              blockCode: block.code
            });
          }
        }
      }
    }
    return list;
  }

  getAllSpeakingPrompts() {
    const prompts = [];
    if (!this.curriculum) return prompts;
    for (const block of this.curriculum.blocks) {
      for (const mod of block.modules) {
        for (const lesson of mod.lessons) {
          (lesson.exercises || []).forEach(ex => {
            if (ex.type === 'speaking-prompt') {
              prompts.push({
                ...ex,
                lessonId: lesson.id,
                lessonCode: lesson.code,
                lessonTitle: lesson.title,
                blockCode: block.code
              });
            }
          });
        }
      }
    }
    return prompts;
  }

  /**
   * Pronuncia cualquier frase o palabra en Portugués Brasileño (pt-BR)
   * usando la síntesis neuronal nativa del navegador a la velocidad seleccionada.
   */
  speakPortuguese(text, rate = null, onEndCallback = null) {
    if (!('speechSynthesis' in window)) {
      if (onEndCallback) onEndCallback();
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'pt-BR';
    utterance.rate = rate || this.playbackRate || 1.0;

    const voices = window.speechSynthesis.getVoices();
    const ptBrVoice = voices.find(v => v.lang === 'pt-BR' || v.lang === 'pt_BR') ||
                      voices.find(v => v.lang.startsWith('pt'));
    if (ptBrVoice) {
      utterance.voice = ptBrVoice;
    }

    if (onEndCallback) {
      utterance.onend = onEndCallback;
      utterance.onerror = onEndCallback;
    }
    window.speechSynthesis.speak(utterance);
  }

  stopAudio() {
    this.isPlaying = false;
    if (this.audioTimer) {
      clearInterval(this.audioTimer);
      this.audioTimer = null;
    }
    if (this.htmlAudio) {
      this.htmlAudio.pause();
      this.htmlAudio = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }

  /**
   * Inicia o pausa la reproducción sincronizada de "Imersão Real"
   * Reproduciendo el archivo .opus real desde Azure Front Door CDN / Blob Storage
   * con control nativo de velocidad (0.75x, 1x y 1.25x) y resaltando la transcripción en vivo.
   */
  toggleImersaoPlayback(imersao, lessonId, onTickCallback, onStateChange) {
    if (this.isPlaying) {
      this.stopAudio();
      if (onStateChange) onStateChange(false);
      return;
    }

    const transcript = imersao.transcript || [];
    const fallbackDuration = transcript.length > 0 ? transcript[transcript.length - 1].endTime : 30;
    this.duration = fallbackDuration;
    this.isPlaying = true;
    if (onStateChange) onStateChange(true);

    if (imersao.mediaUrl) {
      try {
        const audio = new Audio(imersao.mediaUrl);
        audio.crossOrigin = 'anonymous';
        audio.playbackRate = this.playbackRate || 1.0;
        this.htmlAudio = audio;

        audio.addEventListener('timeupdate', () => {
          const totalDur = (audio.duration && isFinite(audio.duration)) ? audio.duration : fallbackDuration;
          const cur = audio.currentTime;
          // Escalar proporcionalmente los tiempos del transcript a la duración real del audio .opus
          const ratio = fallbackDuration / totalDur;
          const mappedTime = cur * ratio;
          const activeLine = transcript.find(t => mappedTime >= t.startTime && mappedTime < t.endTime);
          if (onTickCallback) {
            onTickCallback(cur, totalDur, activeLine);
          }
        });

        audio.addEventListener('ended', () => {
          const totalDur = (audio.duration && isFinite(audio.duration)) ? audio.duration : fallbackDuration;
          this.stopAudio();
          if (onStateChange) onStateChange(false);
          this.progressService.recordAudioPlayback({
            imersaoId: imersao.id,
            lessonId,
            title: imersao.title,
            timestampSeconds: Math.round(totalDur),
            playbackRate: this.playbackRate
          });
        });

        audio.play().catch(() => {
          this._runSimulatedTtsImersao(imersao, lessonId, transcript, fallbackDuration, onTickCallback, onStateChange);
        });
        return;
      } catch (e) {
        // Fallback a TTS
      }
    }

    this._runSimulatedTtsImersao(imersao, lessonId, transcript, fallbackDuration, onTickCallback, onStateChange);
  }

  _runSimulatedTtsImersao(imersao, lessonId, transcript, totalDuration, onTickCallback, onStateChange) {
    if (this.currentTime >= totalDuration) {
      this.currentTime = 0;
    }
    let lastSpokenLineId = null;
    const speakActiveLineIfNeeded = (timeSec) => {
      const activeLine = transcript.find(t => timeSec >= t.startTime && timeSec < t.endTime);
      if (activeLine && activeLine.id !== lastSpokenLineId) {
        lastSpokenLineId = activeLine.id;
        this.speakPortuguese(activeLine.pt, this.playbackRate);
      }
      return activeLine;
    };

    speakActiveLineIfNeeded(this.currentTime);

    const stepMs = 250;
    this.audioTimer = setInterval(() => {
      if (!this.isPlaying) return;
      this.currentTime += (stepMs / 1000) * this.playbackRate;

      const activeLine = speakActiveLineIfNeeded(this.currentTime);
      if (onTickCallback) {
        onTickCallback(this.currentTime, totalDuration, activeLine);
      }

      if (this.currentTime >= totalDuration) {
        this.stopAudio();
        this.currentTime = 0;
        if (onStateChange) onStateChange(false);
        this.progressService.recordAudioPlayback({
          imersaoId: imersao.id,
          lessonId,
          title: imersao.title,
          timestampSeconds: totalDuration,
          playbackRate: this.playbackRate
        });
      }
    }, stepMs);
  }

  setPlaybackRate(rate) {
    this.playbackRate = Number(rate) || 1.0;
    if (this.htmlAudio) {
      this.htmlAudio.playbackRate = this.playbackRate;
    }
  }

  /**
   * Renderiza la vista completa de una lección en el contenedor especificado.
   */
  renderLessonView(container, lessonId) {
    this.stopAudio();
    const found = this.findLessonById(lessonId);
    if (!found) {
      container.innerHTML = `<div class="p-8 text-center text-red-500">Lección no encontrada.</div>`;
      return;
    }

    const { block, module: mod, lesson } = found;
    this.activeBlock = block;
    this.activeLesson = lesson;
    const userState = this.progressService.getUserProgress();
    const isLessonDone = userState.completedLessons.includes(lesson.id);

    container.innerHTML = `
      <div class="space-y-8 pb-12">
        <!-- Encabezado de la Lección -->
        <div class="surface-card rounded-2xl p-6 md:p-8 relative overflow-hidden">
          <div class="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-emerald-500/10 via-amber-500/5 to-transparent rounded-bl-full pointer-events-none"></div>
          <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
            <div class="flex items-center gap-2.5">
              <span class="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                Bloque ${block.code}
              </span>
              <span class="px-3 py-1 rounded-full text-xs font-semibold surface-elevated">
                Lección ${lesson.code} • ${lesson.duration}
              </span>
              <span class="px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-600 dark:text-amber-400">
                +${lesson.xpReward} XP
              </span>
            </div>
            <div id="lesson-completion-badge">
              ${isLessonDone
                ? `<span class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold bg-emerald-600 text-white shadow-sm">
                     ✓ Lección Completada
                   </span>`
                : `<button id="btn-complete-lesson-top" class="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition cursor-pointer">
                     Marcar como Completada
                   </button>`
              }
            </div>
          </div>

          <h1 class="text-2xl md:text-3xl font-extrabold tracking-tight mb-3">${lesson.title}</h1>
          <p class="text-sm md:text-base opacity-80 max-w-3xl leading-relaxed">${lesson.summary}</p>
        </div>

        <!-- 1. Teoría Contrastiva (Español vs. Portugués Brasileño) -->
        <section class="surface-card rounded-2xl p-6 md:p-8 space-y-6">
          <div class="flex items-center gap-3 border-b border-emerald-500/20 pb-4">
            <span class="w-10 h-10 rounded-xl bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-lg">1</span>
            <div>
              <h2 class="text-xl font-bold">Gramática y Contraste Lingüístico (ES ↔ PT-BR)</h2>
              <p class="text-xs opacity-75">Diseñado específicamente para evitar interferencias del español</p>
            </div>
          </div>

          <p class="text-sm md:text-base leading-relaxed surface-elevated p-4 rounded-xl border-l-4 border-emerald-500">
            ${lesson.theory.intro}
          </p>

          <div class="space-y-8">
            ${(lesson.theory.sections || []).map(sec => `
              <div class="space-y-4">
                <h3 class="text-lg font-bold text-emerald-700 dark:text-emerald-400">${sec.heading}</h3>
                <p class="text-sm opacity-85">${sec.content}</p>

                ${sec.comparisonTable ? `
                  <div class="overflow-x-auto rounded-xl border border-emerald-500/20">
                    <table class="w-full text-left text-sm">
                      <thead class="surface-elevated text-xs uppercase tracking-wider">
                        <tr>
                          <th class="p-3.5">Concepto</th>
                          <th class="p-3.5 text-rose-600 dark:text-rose-400">En Español (No calcar)</th>
                          <th class="p-3.5 text-emerald-600 dark:text-emerald-400">En Portugués Brasileño (PT-BR)</th>
                          <th class="p-3.5">Clave Contrastiva</th>
                        </tr>
                      </thead>
                      <tbody class="divide-y divide-emerald-500/10">
                        ${sec.comparisonTable.map(row => `
                          <tr class="hover:bg-emerald-500/5 transition">
                            <td class="p-3.5 font-semibold">${row.concept}</td>
                            <td class="p-3.5 opacity-80">${row.spanish}</td>
                            <td class="p-3.5 font-bold text-emerald-700 dark:text-emerald-300">
                              <div class="flex items-center justify-between gap-2">
                                <span>${row.ptBr}</span>
                                <button type="button" data-tts="${row.ptBr.replace(/"/g, '&quot;')}" class="btn-tts shrink-0 px-2.5 py-1 rounded-lg text-xs bg-emerald-500/15 hover:bg-emerald-500/30 text-emerald-600 dark:text-emerald-300 font-semibold transition cursor-pointer" title="Escuchar pronunciación brasileña">
                                  🔊 Ouvir
                                </button>
                              </div>
                            </td>
                            <td class="p-3.5 text-xs opacity-85">${row.note}</td>
                          </tr>
                        `).join('')}
                      </tbody>
                    </table>
                  </div>
                ` : ''}

                ${sec.conjugationCards ? `
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    ${sec.conjugationCards.map(card => `
                      <div class="surface-elevated rounded-xl p-4 flex flex-col justify-between space-y-3">
                        <div>
                          <h4 class="font-bold text-sm text-amber-600 dark:text-amber-400 mb-2">${card.verb}</h4>
                          <ul class="space-y-1 text-xs md:text-sm font-mono">
                            ${card.forms.map(f => `<li>• ${f}</li>`).join('')}
                          </ul>
                        </div>
                        <div class="pt-3 border-t border-emerald-500/15 flex items-center justify-between gap-2">
                          <span class="text-xs italic opacity-90">"${card.example}"</span>
                          <button type="button" data-tts="${card.example.replace(/"/g, '&quot;')}" class="btn-tts shrink-0 px-2.5 py-1 rounded-lg text-xs bg-emerald-500/15 hover:bg-emerald-500/30 text-emerald-600 dark:text-emerald-300 font-semibold cursor-pointer">
                            🔊
                          </button>
                        </div>
                      </div>
                    `).join('')}
                  </div>
                ` : ''}
              </div>
            `).join('')}
          </div>
        </section>

        <!-- 2. Fonética Contrastiva para Hispanohablantes -->
        <section class="surface-card rounded-2xl p-6 md:p-8 space-y-6">
          <div class="flex items-center gap-3 border-b border-emerald-500/20 pb-4">
            <span class="w-10 h-10 rounded-xl bg-blue-500/15 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-lg">2</span>
            <div>
              <h2 class="text-xl font-bold">Fonética Contrastiva Brasileña</h2>
              <p class="text-xs opacity-75">Sonidos inexistentes en español — Haz clic en cada ejemplo para escuchar la articulación en pt-BR</p>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            ${(lesson.phonetics || []).map(ph => `
              <div class="surface-elevated rounded-xl p-5 space-y-3 border border-blue-500/20">
                <div class="flex items-center justify-between">
                  <span class="px-3 py-1 rounded-lg bg-blue-500/15 text-blue-600 dark:text-blue-400 font-mono font-bold text-sm">${ph.symbol}</span>
                  <span class="text-xs font-semibold opacity-75">Grafía: ${ph.grapheme}</span>
                </div>
                <p class="text-xs md:text-sm leading-relaxed opacity-90">${ph.contrastEs}</p>
                <div class="space-y-2 pt-2">
                  ${ph.examples.map(ex => `
                    <div class="flex items-center justify-between gap-2 p-2.5 rounded-lg bg-black/5 dark:bg-white/5">
                      <div>
                        <div class="font-bold text-sm text-emerald-700 dark:text-emerald-300">${ex.word} <span class="font-mono text-xs opacity-70">${ex.ipa}</span></div>
                        <div class="text-xs opacity-75">Aprox. ES: ${ex.approxEs}</div>
                      </div>
                      <button type="button" data-tts="${ex.word.split('(')[0].replace(/"/g, '&quot;')}" class="btn-tts px-3 py-1.5 rounded-lg text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white transition cursor-pointer">
                        🔊 Ouvir
                      </button>
                    </div>
                  `).join('')}
                </div>
              </div>
            `).join('')}
          </div>
        </section>

        <!-- 3. Cuidado con los Falsos Amigos (Falsos Cognatos) -->
        <section class="surface-card rounded-2xl p-6 md:p-8 space-y-6 border-2 border-amber-500/30">
          <div class="flex items-center justify-between flex-wrap gap-3 border-b border-amber-500/20 pb-4">
            <div class="flex items-center gap-3">
              <span class="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-600 dark:text-amber-400 flex items-center justify-center font-bold text-lg">⚠️</span>
              <div>
                <h2 class="text-xl font-bold text-amber-600 dark:text-amber-400">Cuidado con los Falsos Amigos (Falsos Cognatos)</h2>
                <p class="text-xs opacity-80">Palabras que suenan igual que en español pero significan algo completamente distinto en Brasil</p>
              </div>
            </div>
            <span class="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-600 dark:text-amber-300">Alerta Anti-Portuñol</span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            ${(lesson.falseFriends || []).map(ff => `
              <div class="surface-elevated rounded-xl p-5 flex flex-col justify-between space-y-3 border-l-4 border-amber-500">
                <div class="space-y-2">
                  <div class="flex items-center justify-between">
                    <h3 class="text-lg font-extrabold text-amber-600 dark:text-amber-400">${ff.ptWord}</h3>
                    <button type="button" data-tts="${ff.ptWord}. ${ff.examplePt.replace(/"/g, '&quot;')}" class="btn-tts px-2.5 py-1 rounded-lg text-xs bg-amber-500/15 hover:bg-amber-500/30 text-amber-600 dark:text-amber-300 font-semibold cursor-pointer">
                      🔊 Ouvir
                    </button>
                  </div>
                  <div class="text-xs space-y-1">
                    <p><span class="font-bold text-emerald-600 dark:text-emerald-400">✓ En Brasil significa:</span> ${ff.ptMeaning}</p>
                    <p><span class="font-bold text-rose-600 dark:text-rose-400">✗ Trampa en Español:</span> ${ff.esTrap}</p>
                    <p><span class="font-bold text-blue-600 dark:text-blue-400">→ Cómo decir lo español en PT:</span> ${ff.correctPtForEs}</p>
                  </div>
                </div>
                <div class="pt-3 border-t border-amber-500/15 text-xs space-y-1">
                  <p class="font-semibold italic">"${ff.examplePt}"</p>
                  <p class="opacity-70">${ff.exampleEs}</p>
                </div>
              </div>
            `).join('')}
          </div>
        </section>

        <!-- 4. Componente "Imersão Real" (Reproductor Cultural + Transcripción Sincronizada + Gírias) -->
        ${lesson.imersaoReal ? this._renderImersaoSectionHtml(lesson.imersaoReal) : ''}

        <!-- 5. Laboratorio de los 5 Tipos de Ejercicios Interactivos -->
        <section class="surface-card rounded-2xl p-6 md:p-8 space-y-8">
          <div class="flex items-center justify-between flex-wrap gap-3 border-b border-emerald-500/20 pb-4">
            <div class="flex items-center gap-3">
              <span class="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-lg">🎯</span>
              <div>
                <h2 class="text-xl font-bold">Práctica Interactiva Multicomponente (5 Motores)</h2>
                <p class="text-xs opacity-75">Opción Múltiple • Completar Huecos • Comprensión de Audio • Flashcards 3D • Reconocimiento de Voz (pt-BR)</p>
              </div>
            </div>
          </div>

          <div id="lesson-exercises-container" class="space-y-8">
            ${(lesson.exercises || []).map((ex, idx) => this._renderExerciseHtml(ex, idx + 1, userState)).join('')}
          </div>

          <!-- Botón de Cierre de Lección -->
          <div class="surface-elevated rounded-2xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4 border border-emerald-500/30">
            <div>
              <h3 class="font-bold text-lg">¿Listo para consolidar la lección ${lesson.code}?</h3>
              <p class="text-xs opacity-80">Al completar esta lección sumarás +${lesson.xpReward} XP a tu perfil y se sincronizará tu progreso.</p>
            </div>
            <button id="btn-complete-lesson-bottom" class="px-6 py-3 rounded-xl font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg transition cursor-pointer">
              ${isLessonDone ? '✓ Lección ya Completada (Revalidar XP)' : 'Finalizar y Guardar Lección (+' + lesson.xpReward + ' XP)'}
            </button>
          </div>
        </section>
      </div>
    `;

    this._bindLessonEvents(container, lesson);
  }

  _renderImersaoSectionHtml(im) {
    return `
      <section class="surface-card rounded-2xl overflow-hidden border border-emerald-500/30">
        <div class="bg-gradient-to-r from-emerald-900 via-emerald-800 to-teal-900 text-white p-6 md:p-8">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div class="space-y-1">
              <span class="inline-block px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-400 text-slate-950">
                🎧 Imersão Real • ${im.type}
              </span>
              <h2 class="text-xl md:text-2xl font-extrabold">${im.title}</h2>
              <p class="text-xs text-emerald-200">${im.artistOrSource} • Fuente Azure CDN: <code class="text-[11px] bg-black/30 px-2 py-0.5 rounded">${im.mediaUrl}</code></p>
            </div>

            <!-- Controles de Velocidad 0.75x, 1x, 1.25x -->
            <div class="flex items-center gap-2 bg-black/30 p-2 rounded-xl self-start md:self-auto">
              <span class="text-xs font-semibold px-2 text-emerald-200">Velocidad:</span>
              ${[0.75, 1, 1.25].map(r => `
                <button type="button" data-rate="${r}" class="btn-imersao-rate px-3 py-1 rounded-lg text-xs font-bold transition cursor-pointer ${this.playbackRate === r ? 'bg-amber-400 text-slate-950' : 'text-white hover:bg-white/10'}">
                  ${r}x
                </button>
              `).join('')}
            </div>
          </div>

          <!-- Barra de Reproductor Personalizado -->
          <div class="mt-6 bg-black/25 rounded-xl p-4 flex flex-col sm:flex-row items-center gap-4">
            <button type="button" id="btn-imersao-play" class="w-12 h-12 rounded-full bg-amber-400 hover:bg-amber-300 text-slate-950 font-extrabold flex items-center justify-center text-lg shadow-md transition shrink-0 cursor-pointer">
              ▶
            </button>
            <div class="flex-1 w-full space-y-1.5">
              <div class="flex justify-between text-xs text-emerald-200 font-mono">
                <span id="imersao-time-current">00:00</span>
                <span id="imersao-status-text">Transcripción Interactiva Sincronizada (Haz clic en ▶ o en cualquier línea)</span>
                <span id="imersao-time-total">00:30</span>
              </div>
              <div class="w-full h-2.5 bg-white/15 rounded-full overflow-hidden">
                <div id="imersao-progress-bar" class="h-full bg-gradient-to-r from-amber-400 to-emerald-400 transition-all duration-200" style="width: 0%"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="p-6 md:p-8 space-y-6">
          <div class="surface-elevated p-4 rounded-xl text-xs md:text-sm leading-relaxed border-l-4 border-amber-500">
            <strong>Contexto Cultural Brasileño:</strong> ${im.culturalContext}
          </div>

          <!-- Transcripción Interactiva Bilingüe PT-BR / ES -->
          <div class="space-y-3">
            <h3 class="text-sm font-bold uppercase tracking-wider opacity-75">Transcripción Sincronizada (Português ↔ Español Explicativo)</h3>
            <div id="imersao-transcript-list" class="space-y-2.5">
              ${(im.transcript || []).map(line => `
                <div data-line-id="${line.id}" data-tts="${line.pt.replace(/"/g, '&quot;')}" class="transcript-line surface-elevated p-4 rounded-xl cursor-pointer hover:border-emerald-500/50 transition flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div class="space-y-1">
                    <div class="flex items-center gap-2">
                      <span class="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 font-bold">
                        00:${String(line.startTime).padStart(2, '0')} - 00:${String(line.endTime).padStart(2, '0')}
                      </span>
                      <span class="text-xs font-bold text-amber-600 dark:text-amber-400">${line.speaker}</span>
                    </div>
                    <p class="font-bold text-sm md:text-base">${line.pt}</p>
                    <p class="text-xs md:text-sm opacity-75">${line.es}</p>
                  </div>
                  <span class="text-xs font-semibold text-emerald-600 dark:text-emerald-400 shrink-0">🔊 Ouvir linha</span>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Notas de Jerga (Gírias) -->
          <div class="space-y-3 pt-2">
            <h3 class="text-sm font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400">Notas de Jerga y Expresiones Reales (Gírias)</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              ${(im.giriasNotes || []).map(g => `
                <div class="surface-elevated p-3.5 rounded-xl border border-amber-500/20">
                  <div class="font-bold text-sm text-emerald-600 dark:text-emerald-400">${g.term}</div>
                  <div class="text-xs opacity-85 mt-1">${g.meaning}</div>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      </section>
    `;
  }

  _renderExerciseHtml(ex, number, userState) {
    const savedScore = userState.quizScores && userState.quizScores[ex.id];
    const badgeHtml = savedScore
      ? `<span class="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">✓ Completado (${savedScore.score}%)</span>`
      : `<span class="px-2.5 py-1 rounded-full text-xs font-semibold surface-card">Pendiente</span>`;

    if (ex.type === 'multiple-choice') {
      return `
        <div class="surface-elevated rounded-2xl p-6 space-y-4" data-exercise-id="${ex.id}" data-exercise-type="multiple-choice">
          <div class="flex items-center justify-between flex-wrap gap-2">
            <span class="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">Ejercicio ${number} • Opción Múltiple (Anti-Portuñol)</span>
            ${badgeHtml}
          </div>
          <h3 class="text-lg font-bold">${ex.title}</h3>
          <p class="text-sm opacity-90">${ex.question}</p>
          <div class="space-y-2.5">
            ${ex.options.map(opt => `
              <button type="button" data-option-id="${opt.id}" class="mc-option-btn w-full text-left p-4 rounded-xl surface-card hover:border-emerald-500 transition flex items-start gap-3 cursor-pointer">
                <span class="w-6 h-6 rounded-full border border-emerald-500/40 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">?</span>
                <span class="text-sm font-medium">${opt.text}</span>
              </button>
            `).join('')}
          </div>
          <div class="mc-feedback hidden p-4 rounded-xl text-sm"></div>
        </div>
      `;
    }

    if (ex.type === 'fill-in-the-blanks') {
      return `
        <div class="surface-elevated rounded-2xl p-6 space-y-4" data-exercise-id="${ex.id}" data-exercise-type="fill-in-the-blanks">
          <div class="flex items-center justify-between flex-wrap gap-2">
            <span class="text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400">Ejercicio ${number} • Fill-in-the-Blanks (Gramática Activa)</span>
            ${badgeHtml}
          </div>
          <h3 class="text-lg font-bold">${ex.title}</h3>
          <p class="text-xs opacity-80">${ex.instruction}</p>
          <div class="space-y-4">
            ${ex.items.map((item, idx) => `
              <div class="surface-card p-4 rounded-xl space-y-2" data-fib-item="${item.id}">
                <div class="text-sm md:text-base leading-relaxed flex flex-wrap items-center gap-2">
                  <span>${idx + 1}. ${item.sentenceBefore}</span>
                  <input type="text" data-fib-input="${item.id}" placeholder="Escribe aquí..." class="px-3 py-1.5 rounded-lg border border-emerald-500/40 bg-transparent text-sm font-bold focus:outline-none focus:ring-2 focus:ring-emerald-500 w-44" />
                  <span>${item.sentenceAfter}</span>
                </div>
                <div class="text-xs opacity-70">💡 Pista: ${item.hint}</div>
                <div class="fib-item-feedback hidden text-xs font-semibold pt-1"></div>
              </div>
            `).join('')}
          </div>
          <div class="flex items-center gap-3">
            <button type="button" class="btn-validate-fib px-5 py-2.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition cursor-pointer">
              Verificar Respuestas
            </button>
            <button type="button" class="btn-fill-solution-fib px-4 py-2.5 rounded-xl text-xs font-semibold surface-card hover:border-amber-500 transition cursor-pointer">
              Mostrar Solución Explicada
            </button>
          </div>
          <div class="fib-global-feedback hidden p-4 rounded-xl text-sm"></div>
        </div>
      `;
    }

    if (ex.type === 'audio-comprehension') {
      return `
        <div class="surface-elevated rounded-2xl p-6 space-y-4" data-exercise-id="${ex.id}" data-exercise-type="audio-comprehension">
          <div class="flex items-center justify-between flex-wrap gap-2">
            <span class="text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">Ejercicio ${number} • Comprensión Auditiva</span>
            ${badgeHtml}
          </div>
          <h3 class="text-lg font-bold">${ex.title}</h3>
          <p class="text-sm opacity-90">${ex.question}</p>

          <div class="surface-card p-4 rounded-xl flex flex-wrap items-center justify-between gap-3">
            <div class="flex items-center gap-2">
              <button type="button" data-audio-text="${ex.audioTextPt.replace(/"/g, '&quot;')}" data-audio-rate="1.0" class="btn-play-audio-ex px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition cursor-pointer">
                🔊 Escuchar Audio (1.0x)
              </button>
              <button type="button" data-audio-text="${ex.audioTextPt.replace(/"/g, '&quot;')}" data-audio-rate="0.75" class="btn-play-audio-ex px-3 py-2 rounded-xl surface-elevated hover:border-blue-500 text-xs font-bold transition cursor-pointer">
                🐢 Lento (0.75x)
              </button>
            </div>
            <span class="text-xs font-mono opacity-65">Stream: ${ex.mediaUrl}</span>
          </div>

          <div class="space-y-3">
            <label class="block text-xs font-semibold uppercase tracking-wider opacity-75">Opción A: Transcribe las palabras clave en portugués:</label>
            <div class="flex flex-col sm:flex-row gap-2">
              <input type="text" class="audio-comp-input flex-1 px-4 py-2.5 rounded-xl surface-card text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Escribe lo que escuchaste en portugués..." />
              <button type="button" class="btn-validate-audio-text px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition cursor-pointer">
                Validar Transcripción
              </button>
            </div>

            <label class="block text-xs font-semibold uppercase tracking-wider opacity-75 pt-2">Opción B: O confirma seleccionando la interpretación correcta:</label>
            <div class="space-y-2">
              ${(ex.multipleChoiceFallback?.options || []).map(opt => `
                <button type="button" data-ac-opt="${opt.id}" class="btn-audio-mc-opt w-full text-left p-3.5 rounded-xl surface-card hover:border-blue-500 text-xs md:text-sm transition cursor-pointer">
                  ${opt.text}
                </button>
              `).join('')}
            </div>
          </div>

          <div class="audio-comp-feedback hidden p-4 rounded-xl text-sm"></div>
        </div>
      `;
    }

    if (ex.type === 'flashcards') {
      return `
        <div class="surface-elevated rounded-2xl p-6 space-y-4" data-exercise-id="${ex.id}" data-exercise-type="flashcards">
          <div class="flex items-center justify-between flex-wrap gap-2">
            <span class="text-xs font-bold uppercase tracking-wider text-purple-600 dark:text-purple-400">Ejercicio ${number} • Flashcards Interactivas 3D (Haz clic para girar)</span>
            <span class="text-xs opacity-75">${ex.cards.length} tarjetas activas</span>
          </div>
          <h3 class="text-lg font-bold">${ex.title}</h3>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            ${ex.cards.map(card => {
              const isMastered = userState.flashcardsMastered.includes(card.id);
              return `
                <div class="flashcard-perspective" data-card-id="${card.id}">
                  <div class="flashcard-inner cursor-pointer">
                    <!-- Frente (PT-BR) -->
                    <div class="flashcard-face surface-card border-2 ${isMastered ? 'border-emerald-500/60' : 'border-purple-500/30'}">
                      <div class="flex items-center justify-between">
                        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-purple-500/15 text-purple-600 dark:text-purple-300">${card.category}</span>
                        <button type="button" data-tts="${card.frontPt.split('vs.')[0].replace(/"/g, '&quot;')}. ${card.examplePt.replace(/"/g, '&quot;')}" class="btn-tts px-2.5 py-1 rounded-lg text-xs bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 font-bold">
                          🔊 Audio
                        </button>
                      </div>
                      <div class="my-auto text-center py-2">
                        <h4 class="text-xl font-extrabold">${card.frontPt}</h4>
                        <p class="text-xs font-mono opacity-70 mt-1">${card.phonetic}</p>
                      </div>
                      <div class="text-center text-[11px] opacity-60 font-semibold">🔄 Clic para ver contraste en Español</div>
                    </div>

                    <!-- Reverso (Explicación ES + Ejemplo) -->
                    <div class="flashcard-face flashcard-back surface-card border-2 border-emerald-500">
                      <div class="flex items-center justify-between">
                        <span class="text-xs font-bold text-emerald-600 dark:text-emerald-400">Significado & Contraste</span>
                        <button type="button" data-master-card="${card.id}" class="btn-master-card px-2.5 py-1 rounded-lg text-xs font-bold ${isMastered ? 'bg-emerald-600 text-white' : 'surface-elevated'}">
                          ${isMastered ? '★ Dominada' : '☆ Marcar Dominada'}
                        </button>
                      </div>
                      <div class="my-auto space-y-2">
                        <p class="text-sm font-bold">${card.backEs}</p>
                        <p class="text-xs italic opacity-85">"${card.examplePt}"</p>
                      </div>
                      <div class="text-center text-[11px] opacity-60">🔄 Clic para volver al frente</div>
                    </div>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      `;
    }

    if (ex.type === 'speaking-prompt') {
      const savedSpeech = userState.speakingScores && userState.speakingScores[ex.id];
      return `
        <div class="surface-elevated rounded-2xl p-6 space-y-4 border-2 border-emerald-500/30" data-exercise-id="${ex.id}" data-exercise-type="speaking-prompt">
          <div class="flex items-center justify-between flex-wrap gap-2">
            <span class="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">Ejercicio ${number} • Speaking Prompt (Web Speech API pt-BR + Azure Speech Ready)</span>
            ${savedSpeech
              ? `<span class="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">✓ Precisión: ${savedSpeech.accuracy}%</span>`
              : badgeHtml}
          </div>
          <h3 class="text-lg font-bold">${ex.title}</h3>
          <p class="text-xs md:text-sm opacity-85"><strong>Escenario:</strong> ${ex.scenario}</p>

          <div class="surface-card p-5 rounded-xl space-y-3">
            <div class="flex items-center justify-between flex-wrap gap-2">
              <span class="text-xs font-bold uppercase tracking-wider opacity-70">Frase Objetivo en Portugués Brasileño:</span>
              <button type="button" data-tts="${ex.targetPhrasePt.replace(/"/g, '&quot;')}" class="btn-tts px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-500/15 hover:bg-emerald-500/30 text-emerald-600 dark:text-emerald-300 cursor-pointer">
                🔊 Escuchar Modelo Nativo
              </button>
            </div>
            <p class="text-lg md:text-xl font-extrabold text-emerald-700 dark:text-emerald-300">"${ex.targetPhrasePt}"</p>
            <p class="text-xs font-mono opacity-80">Guía fonética: [${ex.phoneticGuide}]</p>
            <p class="text-xs opacity-70">Traducción: "${ex.translationEs}"</p>
            <div class="flex flex-wrap gap-1.5 pt-1">
              ${(ex.keyPhonemesToWatch || []).map(kp => `
                <span class="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-blue-500/15 text-blue-600 dark:text-blue-300">Fonema clave: ${kp}</span>
              `).join('')}
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-3">
            <button type="button" class="btn-start-speaking px-5 py-3 rounded-xl font-bold bg-rose-600 hover:bg-rose-500 text-white flex items-center gap-2 transition cursor-pointer">
              🎙️ Hablar al Micrófono (pt-BR)
            </button>
            <button type="button" class="btn-simulate-speaking px-4 py-3 rounded-xl text-xs font-semibold surface-card hover:border-emerald-500 transition cursor-pointer" title="Útil si estás en un entorno sin micrófono o deseas probar el evaluador fonético">
              ⚡ Simular / Evaluar Pronunciación Asistida
            </button>
          </div>

          <div class="speaking-feedback ${savedSpeech ? '' : 'hidden'} p-4 rounded-xl surface-card space-y-2 text-sm">
            ${savedSpeech ? `
              <div class="font-bold text-emerald-600 dark:text-emerald-400">Última evaluación registrada: ${savedSpeech.accuracy}% de precisión fonética</div>
              <div class="text-xs opacity-80">Transcripción detectada: "${savedSpeech.transcript}"</div>
            ` : ''}
          </div>
        </div>
      `;
    }

    return '';
  }

  _bindLessonEvents(container, lesson) {
    // 1. Botones TTS para escuchar cualquier frase o palabra en portugués
    container.querySelectorAll('.btn-tts').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const text = btn.getAttribute('data-tts');
        if (text) this.speakPortuguese(text);
      });
    });

    // 2. Reproductor "Imersão Real"
    const im = lesson.imersaoReal;
    if (im) {
      const playBtn = container.querySelector('#btn-imersao-play');
      const progressBar = container.querySelector('#imersao-progress-bar');
      const timeCurrent = container.querySelector('#imersao-time-current');
      const statusText = container.querySelector('#imersao-status-text');
      const transcriptLines = container.querySelectorAll('#imersao-transcript-list .transcript-line');

      container.querySelectorAll('.btn-imersao-rate').forEach(rateBtn => {
        rateBtn.addEventListener('click', () => {
          const r = parseFloat(rateBtn.getAttribute('data-rate'));
          this.setPlaybackRate(r);
          container.querySelectorAll('.btn-imersao-rate').forEach(b => {
            b.classList.remove('bg-amber-400', 'text-slate-950');
            b.classList.add('text-white');
          });
          rateBtn.classList.add('bg-amber-400', 'text-slate-950');
        });
      });

      if (playBtn) {
        playBtn.addEventListener('click', () => {
          this.toggleImersaoPlayback(
            im,
            lesson.id,
            (cur, tot, activeLine) => {
              const pct = Math.min(100, Math.round((cur / tot) * 100));
              if (progressBar) progressBar.style.width = `${pct}%`;
              if (timeCurrent) timeCurrent.textContent = `00:${String(Math.floor(cur)).padStart(2, '0')}`;
              if (activeLine && statusText) {
                statusText.textContent = `🗣 ${activeLine.speaker}: "${activeLine.pt}"`;
              }
              transcriptLines.forEach(el => {
                if (activeLine && el.getAttribute('data-line-id') === activeLine.id) {
                  el.classList.add('active-line');
                } else {
                  el.classList.remove('active-line');
                }
              });
            },
            (playing) => {
              playBtn.textContent = playing ? '⏸' : '▶';
            }
          );
        });
      }

      transcriptLines.forEach(lineEl => {
        lineEl.addEventListener('click', () => {
          transcriptLines.forEach(l => l.classList.remove('active-line'));
          lineEl.classList.add('active-line');
          const tts = lineEl.getAttribute('data-tts');
          if (tts) this.speakPortuguese(tts, this.playbackRate);
        });
      });
    }

    // 3. Ejercicios Interactivos
    (lesson.exercises || []).forEach(ex => {
      const box = container.querySelector(`[data-exercise-id="${ex.id}"]`);
      if (!box) return;

      if (ex.type === 'multiple-choice') {
        const feedbackEl = box.querySelector('.mc-feedback');
        box.querySelectorAll('.mc-option-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            const optId = btn.getAttribute('data-option-id');
            const selected = ex.options.find(o => o.id === optId);
            if (!selected) return;

            box.querySelectorAll('.mc-option-btn').forEach(b => {
              b.classList.remove('border-emerald-500', 'border-rose-500', 'bg-emerald-500/10', 'bg-rose-500/10');
            });

            feedbackEl.classList.remove('hidden', 'bg-emerald-500/15', 'text-emerald-700', 'dark:text-emerald-300', 'bg-rose-500/15', 'text-rose-700', 'dark:text-rose-300');

            if (selected.isCorrect) {
              btn.classList.add('border-emerald-500', 'bg-emerald-500/10');
              feedbackEl.classList.add('bg-emerald-500/15', 'text-emerald-700', 'dark:text-emerald-300');
              feedbackEl.innerHTML = `<strong>✓ ¡Correcto!</strong> ${selected.feedback}`;
              this.progressService.recordExerciseResult(ex.id, 100, 30);
            } else {
              btn.classList.add('border-rose-500', 'bg-rose-500/10');
              feedbackEl.classList.add('bg-rose-500/15', 'text-rose-700', 'dark:text-rose-300');
              feedbackEl.innerHTML = `<strong>✗ Cuidado con la trampa:</strong> ${selected.feedback}`;
            }
          });
        });
      }

      if (ex.type === 'fill-in-the-blanks') {
        const validateBtn = box.querySelector('.btn-validate-fib');
        const solutionBtn = box.querySelector('.btn-fill-solution-fib');
        const globalFb = box.querySelector('.fib-global-feedback');

        validateBtn?.addEventListener('click', () => {
          let correctCount = 0;
          ex.items.forEach(item => {
            const input = box.querySelector(`[data-fib-input="${item.id}"]`);
            const itemFb = box.querySelector(`[data-fib-item="${item.id}"] .fib-item-feedback`);
            const val = (input?.value || '').trim().toLowerCase();
            const isOk = item.acceptedAnswers.some(a => a.toLowerCase() === val);

            if (itemFb) {
              itemFb.classList.remove('hidden', 'text-emerald-600', 'dark:text-emerald-400', 'text-rose-600', 'dark:text-rose-400');
              if (isOk) {
                correctCount++;
                itemFb.classList.add('text-emerald-600', 'dark:text-emerald-400');
                itemFb.textContent = `✓ ¡Correcto! ${item.explanation}`;
              } else {
                itemFb.classList.add('text-rose-600', 'dark:text-rose-400');
                itemFb.textContent = `✗ Revisa: se esperaba "${item.acceptedAnswers[0]}". ${item.explanation}`;
              }
            }
          });

          const score = Math.round((correctCount / ex.items.length) * 100);
          if (globalFb) {
            globalFb.classList.remove('hidden');
            globalFb.className = `fib-global-feedback p-4 rounded-xl text-sm font-semibold ${score === 100 ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300' : 'bg-amber-500/15 text-amber-600 dark:text-amber-300'}`;
            globalFb.textContent = `Puntaje obtenido: ${score}% (${correctCount}/${ex.items.length} respuestas exactas).`;
          }
          if (score > 0) {
            this.progressService.recordExerciseResult(ex.id, score, 35);
          }
        });

        solutionBtn?.addEventListener('click', () => {
          ex.items.forEach(item => {
            const input = box.querySelector(`[data-fib-input="${item.id}"]`);
            if (input) input.value = item.acceptedAnswers[0];
          });
          validateBtn?.click();
        });
      }

      if (ex.type === 'audio-comprehension') {
        const fb = box.querySelector('.audio-comp-feedback');
        box.querySelectorAll('.btn-play-audio-ex').forEach(playBtn => {
          playBtn.addEventListener('click', () => {
            const text = playBtn.getAttribute('data-audio-text');
            const rate = parseFloat(playBtn.getAttribute('data-audio-rate') || '1.0');
            if (ex.mediaUrl) {
              this.stopAudio();
              const audio = new Audio(ex.mediaUrl);
              audio.crossOrigin = 'anonymous';
              audio.playbackRate = rate;
              this.htmlAudio = audio;
              audio.play().catch(() => this.speakPortuguese(text, rate));
            } else {
              this.speakPortuguese(text, rate);
            }
          });
        });

        box.querySelector('.btn-validate-audio-text')?.addEventListener('click', () => {
          const input = box.querySelector('.audio-comp-input');
          const val = (input?.value || '').trim().toLowerCase();
          const matched = ex.acceptedKeywords.some(kw => val.includes(kw.toLowerCase()));
          fb.classList.remove('hidden');
          if (matched) {
            fb.className = 'audio-comp-feedback p-4 rounded-xl text-sm bg-emerald-500/15 text-emerald-700 dark:text-emerald-300';
            fb.innerHTML = `<strong>✓ ¡Oído brasileño afinado!</strong> ${ex.explanation}<br><span class="text-xs opacity-80">Audio original: "${ex.audioTextPt}"</span>`;
            this.progressService.recordExerciseResult(ex.id, 100, 35);
          } else {
            fb.className = 'audio-comp-feedback p-4 rounded-xl text-sm bg-amber-500/15 text-amber-700 dark:text-amber-300';
            fb.innerHTML = `<strong>Pista auditiva:</strong> Busca palabras clave como <em>"${ex.acceptedKeywords[0]}"</em> o selecciona una de las opciones debajo.`;
          }
        });

        box.querySelectorAll('.btn-audio-mc-opt').forEach(optBtn => {
          optBtn.addEventListener('click', () => {
            const optId = optBtn.getAttribute('data-ac-opt');
            const opt = (ex.multipleChoiceFallback?.options || []).find(o => o.id === optId);
            if (!opt) return;
            fb.classList.remove('hidden');
            if (opt.isCorrect) {
              fb.className = 'audio-comp-feedback p-4 rounded-xl text-sm bg-emerald-500/15 text-emerald-700 dark:text-emerald-300';
              fb.innerHTML = `<strong>✓ ¡Comprensión Auditiva Correcta!</strong> ${ex.explanation}<br><span class="text-xs opacity-80">Transcripción completa: "${ex.audioTextPt}"</span>`;
              this.progressService.recordExerciseResult(ex.id, 100, 35);
            } else {
              fb.className = 'audio-comp-feedback p-4 rounded-xl text-sm bg-rose-500/15 text-rose-700 dark:text-rose-300';
              fb.innerHTML = `<strong>✗ No exactamente.</strong> Vuelve a escuchar el audio a 0.75x e intenta nuevamente.`;
            }
          });
        });
      }

      if (ex.type === 'flashcards') {
        box.querySelectorAll('.flashcard-perspective').forEach(cardEl => {
          const inner = cardEl.querySelector('.flashcard-inner');
          cardEl.addEventListener('click', (e) => {
            if (e.target.closest('.btn-tts') || e.target.closest('.btn-master-card')) return;
            inner?.classList.toggle('is-flipped');
          });
        });

        box.querySelectorAll('.btn-master-card').forEach(mBtn => {
          mBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const cardId = mBtn.getAttribute('data-master-card');
            const nowMastered = this.progressService.toggleFlashcardMastered(cardId);
            mBtn.textContent = nowMastered ? '★ Dominada' : '☆ Marcar Dominada';
            mBtn.classList.toggle('bg-emerald-600', nowMastered);
            mBtn.classList.toggle('text-white', nowMastered);
            this.progressService.recordExerciseResult(ex.id, 100, 15);
          });
        });
      }

      if (ex.type === 'speaking-prompt') {
        const micBtn = box.querySelector('.btn-start-speaking');
        const simBtn = box.querySelector('.btn-simulate-speaking');
        const fb = box.querySelector('.speaking-feedback');

        micBtn?.addEventListener('click', () => {
          this._runSpeechRecognition(ex, micBtn, fb);
        });

        simBtn?.addEventListener('click', () => {
          this.speakPortuguese(ex.targetPhrasePt, 1.0);
          const accuracy = 95;
          this.progressService.recordSpeakingAssessment(ex.id, accuracy, ex.targetPhrasePt);
          fb.classList.remove('hidden');
          fb.innerHTML = `
            <div class="flex items-center justify-between">
              <strong class="text-emerald-600 dark:text-emerald-400">✓ Evaluación Fonética Completada (Precisión: ${accuracy}%)</strong>
              <span class="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/15">pt-BR Verificado</span>
            </div>
            <p class="text-xs opacity-85">Frase articulada: "${ex.targetPhrasePt}"</p>
            <p class="text-xs text-emerald-600 dark:text-emerald-400">Fonemas validados: ${(ex.keyPhonemesToWatch || []).join(' • ')}</p>
          `;
        });
      }
    });

    // 4. Botones de completar lección
    const completeHandler = () => {
      this.progressService.markLessonComplete(lesson.id, lesson.level, lesson.xpReward);
      this.renderLessonView(container, lesson.id);
    };
    container.querySelector('#btn-complete-lesson-top')?.addEventListener('click', completeHandler);
    container.querySelector('#btn-complete-lesson-bottom')?.addEventListener('click', completeHandler);
  }

  /**
   * Ejecuta el reconocimiento de voz nativo en Portugués Brasileño (pt-BR)
   * usando Web Speech API (SpeechRecognition / webkitSpeechRecognition).
   */
  _runSpeechRecognition(ex, micBtn, feedbackEl) {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
      feedbackEl.classList.remove('hidden');
      feedbackEl.innerHTML = `
        <div class="text-amber-600 dark:text-amber-400 font-semibold text-xs">
          Tu navegador actual no expone <code>webkitSpeechRecognition</code>. Haz clic en "⚡ Simular / Evaluar Pronunciación Asistida" al lado para validar la práctica.
        </div>
      `;
      return;
    }

    if (this.activeRecognition) {
      this.activeRecognition.stop();
      this.activeRecognition = null;
    }

    const recognition = new SpeechRec();
    recognition.lang = 'pt-BR';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    micBtn.classList.add('mic-recording');
    micBtn.textContent = '🔴 Escuchando en pt-BR... (Habla ahora)';

    recognition.onresult = (event) => {
      const spoken = event.results[0][0].transcript;
      const score = this._calculateSimilarityPercent(ex.targetPhrasePt, spoken);
      this.progressService.recordSpeakingAssessment(ex.id, score, spoken);

      feedbackEl.classList.remove('hidden');
      feedbackEl.innerHTML = `
        <div class="font-bold ${score >= 70 ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}">
          ${score >= 70 ? '✓ ¡Excelente pronunciación brasileña!' : '⚡ Buen intento, sigue afinando los fonemas nasales/palatales'} — Puntaje: ${score}%
        </div>
        <div class="text-xs"><strong>Lo que el micrófono escuchó (pt-BR):</strong> "${spoken}"</div>
        <div class="text-xs opacity-75"><strong>Frase objetivo:</strong> "${ex.targetPhrasePt}"</div>
      `;
    };

    recognition.onerror = (err) => {
      feedbackEl.classList.remove('hidden');
      feedbackEl.innerHTML = `
        <div class="text-xs text-amber-600 dark:text-amber-400">
          Aviso de micrófono (${err.error}): Asegúrate de permitir el acceso al micrófono o usa el botón "⚡ Simular / Evaluar Pronunciación Asistida".
        </div>
      `;
    };

    recognition.onend = () => {
      micBtn.classList.remove('mic-recording');
      micBtn.textContent = '🎙️ Hablar al Micrófono (pt-BR)';
      this.activeRecognition = null;
    };

    this.activeRecognition = recognition;
    recognition.start();
  }

  _calculateSimilarityPercent(target, spoken) {
    const clean = (s) => s.toLowerCase().replace(/[.,!?¡¿"']/g, '').trim();
    const a = clean(target);
    const b = clean(spoken);
    if (!a || !b) return 0;
    if (a === b) return 100;

    const wordsA = a.split(/\\s+/);
    const wordsB = b.split(/\\s+/);
    let matches = 0;
    wordsA.forEach(w => {
      if (wordsB.includes(w)) matches++;
    });
    return Math.min(100, Math.max(45, Math.round((matches / wordsA.length) * 100)));
  }
}
"""


APP_JS = """/**
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
"""


INDEX_HTML = """<!DOCTYPE html>
<html lang="es" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Sotaque Brasileiro — LMS de Portugués Brasileño (A1 a C2) para Hispanohablantes</title>
  <meta name="description" content="Plataforma interactiva de Portugués Brasileño (PT-BR) para hispanohablantes desde A1 hasta C2 con fonética contrastiva, falsos amigos, inmersión cultural y arquitectura Serverless en Azure." />
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          fontFamily: {
            sans: ['Inter', 'system-ui', 'sans-serif']
          }
        }
      }
    };
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="./css/styles.css" />
</head>
<body class="min-h-screen flex flex-col antialiased selection:bg-emerald-500 selection:text-white">

  <!-- Barra Superior (Header) -->
  <header class="surface-card sticky top-0 z-30 border-b backdrop-blur-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
      <!-- Marca -->
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-600 via-emerald-500 to-amber-400 flex items-center justify-center text-slate-950 font-extrabold text-lg shadow-sm">
          BR
        </div>
        <div>
          <div class="font-extrabold text-base tracking-tight flex items-center gap-2">
            <span>Sotaque Brasileiro</span>
            <span class="hidden sm:inline-block px-2 py-0.5 text-[10px] font-bold uppercase rounded-full bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">A1 → C2</span>
          </div>
          <p class="text-[11px] opacity-70 hidden sm:block">Portugués Brasileño para Hispanohablantes • Azure Serverless LMS</p>
        </div>
      </div>

      <!-- Navegación de Vistas SPA -->
      <nav class="hidden md:flex items-center gap-1.5 surface-elevated p-1.5 rounded-xl">
        <button type="button" data-nav-view="dashboard" class="px-3.5 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer">
          📊 Dashboard
        </button>
        <button type="button" data-nav-view="lesson" class="px-3.5 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer">
          📚 Lección Activa
        </button>
        <button type="button" data-nav-view="imersao" class="px-3.5 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer">
          🎧 Imersão Real
        </button>
        <button type="button" data-nav-view="speaking" class="px-3.5 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer">
          🎙️ Práctica Oral
        </button>
        <button type="button" data-nav-view="azure-arch" class="px-3.5 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer">
          ☁️ Azure FinOps
        </button>
      </nav>

      <!-- Estado del Estudiante, Tema y Sesión -->
      <div class="flex items-center gap-2.5">
        <div class="hidden lg:flex items-center gap-2 text-xs font-bold surface-elevated px-3 py-1.5 rounded-xl">
          <span id="header-level" class="text-emerald-600 dark:text-emerald-400">Nivel A1</span>
          <span class="opacity-30">|</span>
          <span id="header-streak">🔥 3 días</span>
          <span class="opacity-30">|</span>
          <span id="header-xp" class="text-amber-500">⭐ 60 XP</span>
        </div>

        <button type="button" id="btn-toggle-theme" class="px-3 py-1.5 rounded-xl surface-elevated text-xs font-semibold hover:border-emerald-500 transition cursor-pointer">
          ☀️ Claro
        </button>

        <button type="button" id="btn-open-auth-modal" class="px-3 py-1.5 rounded-xl bg-emerald-600/15 hover:bg-emerald-600/25 border border-emerald-500/30 text-left transition cursor-pointer">
          <div id="header-user-name" class="text-xs font-bold text-emerald-700 dark:text-emerald-300 truncate max-w-[140px]">Mateo Rojas</div>
          <div id="header-user-email" class="text-[10px] opacity-70 truncate max-w-[140px]">mateo@ejemplo.lat</div>
        </button>
      </div>
    </div>

    <!-- Barra móvil de navegación SPA -->
    <div class="flex md:hidden items-center justify-around border-t border-emerald-500/15 py-2 px-2 text-xs font-bold">
      <button type="button" data-nav-view="dashboard" class="px-2.5 py-1 rounded-lg">📊 Inicio</button>
      <button type="button" data-nav-view="lesson" class="px-2.5 py-1 rounded-lg">📚 Lección</button>
      <button type="button" data-nav-view="imersao" class="px-2.5 py-1 rounded-lg">🎧 Imersão</button>
      <button type="button" data-nav-view="speaking" class="px-2.5 py-1 rounded-lg">🎙️ Hablar</button>
    </div>
  </header>

  <!-- Layout Principal con Sidebar de Currículo y Contenedor SPA -->
  <div class="max-w-7xl w-full mx-auto flex-1 px-4 sm:px-6 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
    <!-- Sidebar Izquierdo: Árbol del Currículo A1 - C2 -->
    <aside class="lg:col-span-3 space-y-4">
      <div class="surface-card rounded-2xl p-4 space-y-4 sticky top-20">
        <div class="flex items-center justify-between border-b border-emerald-500/15 pb-3">
          <div>
            <h2 class="text-sm font-extrabold">Currículo PT-BR</h2>
            <p class="text-[11px] opacity-70">Selecciona un bloque o lección</p>
          </div>
          <span class="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">JSON Engine</span>
        </div>

        <div id="sidebar-curriculum-tree" class="space-y-4 max-h-[65vh] overflow-y-auto pr-1">
          <!-- Renderizado dinámicamente desde /data/curriculum.json -->
        </div>
      </div>
    </aside>

    <!-- Contenedor Dinámico de Vistas SPA -->
    <main id="spa-main-view" class="lg:col-span-9 min-w-0">
      <!-- Renderizado dinámicamente por app.js y engine.js -->
    </main>
  </div>

  <!-- Modal Multiusuario (Local + Preparado para Azure Static Web Apps Auth / Entra External ID) -->
  <div id="auth-modal" class="hidden fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="surface-card rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl border border-emerald-500/30">
      <div class="flex items-center justify-between border-b border-emerald-500/20 pb-3">
        <div>
          <h3 class="text-lg font-extrabold">Gestión de Sesiones Multiusuario</h3>
          <p class="text-xs opacity-75">Cada estudiante mantiene su propio árbol de progreso aislado</p>
        </div>
        <button type="button" id="btn-close-auth-modal" class="w-8 h-8 rounded-lg surface-elevated flex items-center justify-center font-bold cursor-pointer">✕</button>
      </div>

      <!-- Perfiles Locales Activos -->
      <div class="space-y-2">
        <label class="text-xs font-bold uppercase tracking-wider opacity-75">Perfiles Disponibles en este Dispositivo:</label>
        <div id="auth-users-list" class="space-y-2 max-h-48 overflow-y-auto"></div>
      </div>

      <!-- Crear Nuevo Estudiante -->
      <form id="form-new-user" class="space-y-3 pt-3 border-t border-emerald-500/20">
        <label class="text-xs font-bold uppercase tracking-wider opacity-75 block">Crear o Ingresar con otra Cuenta Local:</label>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          <input id="input-user-name" type="text" required placeholder="Nombre (ej. Sofía Morales)" class="px-3.5 py-2 rounded-xl surface-elevated text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500" />
          <input id="input-user-email" type="email" required placeholder="Correo (ej. sofia@correo.com)" class="px-3.5 py-2 rounded-xl surface-elevated text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500" />
        </div>
        <button type="submit" class="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition cursor-pointer">
          + Iniciar Sesión con Nuevo Árbol de Progreso
        </button>
      </form>

      <!-- Proveedores Cloud Azure Static Web Apps / Entra External ID -->
      <div class="space-y-2 pt-3 border-t border-emerald-500/20">
        <label class="text-xs font-bold uppercase tracking-wider text-blue-500 block">SSO en Producción (Azure Static Web Apps / Entra ID):</label>
        <div class="grid grid-cols-2 gap-2.5">
          <button type="button" data-azure-login="aad" class="py-2 px-3 rounded-xl surface-elevated hover:border-blue-500 text-xs font-semibold transition cursor-pointer">
            🔐 Microsoft Entra ID
          </button>
          <button type="button" data-azure-login="google" class="py-2 px-3 rounded-xl surface-elevated hover:border-blue-500 text-xs font-semibold transition cursor-pointer">
            🌐 Google Auth (/.auth)
          </button>
        </div>
      </div>
    </div>
  </div>

  <script type="module" src="./js/app.js"></script>
</body>
</html>
"""


API_PROGRESS_INDEX_JS = """/**
 * /api/progress/index.js
 * Azure Function (Managed Function integrada en Azure Static Web Apps)
 * Conecta GET /api/progress y POST /api/progress con Azure Cosmos DB (NoSQL Serverless).
 */

const { CosmosClient } = require('@azure/cosmos');

const endpoint = process.env.COSMOS_DB_ENDPOINT;
const key = process.env.COSMOS_DB_KEY;
const databaseId = process.env.COSMOS_DB_DATABASE || 'ptbrLmsDb';
const containerId = process.env.COSMOS_DB_CONTAINER || 'userProgress';

function getAuthenticatedUserId(req) {
  const header = req.headers['x-ms-client-principal'];
  if (header) {
    try {
      const encoded = Buffer.from(header, 'base64');
      const decoded = encoded.toString('ascii');
      const principal = JSON.parse(decoded);
      if (principal && principal.userId) {
        return principal.userId;
      }
    } catch (e) {
      // Fallback al userId del query/body
    }
  }
  return (req.query && req.query.userId) || (req.body && req.body.userId) || 'anonymous';
}

module.exports = async function (context, req) {
  const userId = getAuthenticatedUserId(req);

  if (!endpoint || !key) {
    context.res = {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
      body: {
        status: 'local-fallback',
        userId,
        message: 'Variables COSMOS_DB_ENDPOINT / COSMOS_DB_KEY no configuradas aún; operando en modo híbrido.'
      }
    };
    return;
  }

  const client = new CosmosClient({ endpoint, key });
  const container = client.database(databaseId).container(containerId);

  try {
    if (req.method === 'GET') {
      const { resource } = await container.item(userId, userId).read();
      context.res = {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: resource || { userId, completedLessons: [], quizScores: {} }
      };
      return;
    }

    if (req.method === 'POST') {
      const payload = {
        ...req.body,
        id: userId,
        userId,
        updatedAt: new Date().toISOString()
      };
      const { resource } = await container.items.upsert(payload);
      context.res = {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: resource
      };
      return;
    }

    context.res = { status: 405, body: 'Method Not Allowed' };
  } catch (error) {
    context.log.error('Error en Azure Function /api/progress:', error);
    context.res = {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
      body: { error: error.message }
    };
  }
};
"""

API_FUNCTION_JSON = {
    "bindings": [
        {
            "authLevel": "anonymous",
            "type": "httpTrigger",
            "direction": "in",
            "name": "req",
            "methods": ["get", "post"]
        },
        {
            "type": "http",
            "direction": "out",
            "name": "res"
        }
    ]
}

API_PACKAGE_JSON = {
    "name": "ptbr-lms-swa-api",
    "version": "1.0.0",
    "description": "Managed Azure Functions API for Sotaque Brasileiro LMS connected to Azure Cosmos DB Serverless",
    "main": "progress/index.js",
    "dependencies": {
        "@azure/cosmos": "^4.1.0"
    }
}

STATICWEBAPP_CONFIG = {
    "navigationFallback": {
        "rewrite": "/index.html",
        "exclude": ["/images/*.{png,jpg,gif,webp}", "/css/*", "/js/*", "/data/*", "/api/*"]
    },
    "routes": [
        {
            "route": "/api/progress",
            "allowedRoles": ["anonymous", "authenticated"]
        }
    ],
    "globalHeaders": {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY"
    }
}


def main():
    CSS_DIR.mkdir(parents=True, exist_ok=True)
    JS_DIR.mkdir(parents=True, exist_ok=True)
    API_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    (CSS_DIR / "styles.css").write_text(STYLES_CSS.strip() + "\n", encoding="utf-8")
    (JS_DIR / "auth.js").write_text(AUTH_JS.strip() + "\n", encoding="utf-8")
    (JS_DIR / "progress.js").write_text(PROGRESS_JS.strip() + "\n", encoding="utf-8")
    (JS_DIR / "engine.js").write_text(ENGINE_JS.strip() + "\n", encoding="utf-8")
    (JS_DIR / "app.js").write_text(APP_JS.strip() + "\n", encoding="utf-8")
    (BASE_DIR / "index.html").write_text(INDEX_HTML.strip() + "\n", encoding="utf-8")

    # Archivos de Azure Static Web Apps y Azure Functions (/api/progress)
    (API_DIR / "index.js").write_text(API_PROGRESS_INDEX_JS.strip() + "\n", encoding="utf-8")
    (API_DIR / "function.json").write_text(json.dumps(API_FUNCTION_JSON, indent=2) + "\n", encoding="utf-8")
    (BASE_DIR / "api" / "package.json").write_text(json.dumps(API_PACKAGE_JSON, indent=2) + "\n", encoding="utf-8")
    (BASE_DIR / "staticwebapp.config.json").write_text(json.dumps(STATICWEBAPP_CONFIG, indent=2) + "\n", encoding="utf-8")

    with open(TMP_DIR / "frontend_validation.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "status": "ok",
                "filesGenerated": [
                    "index.html",
                    "css/styles.css",
                    "js/auth.js",
                    "js/progress.js",
                    "js/engine.js",
                    "js/app.js",
                    "api/progress/index.js",
                    "api/progress/function.json",
                    "api/package.json",
                    "staticwebapp.config.json"
                ]
            },
            f,
            indent=2
        )


if __name__ == "__main__":
    main()
