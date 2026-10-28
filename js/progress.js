/**
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
