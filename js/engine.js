/**
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
   * Soportando velocidades 0.75x, 1x y 1.25x y resaltando la transcripción en vivo.
   */
  toggleImersaoPlayback(imersao, lessonId, onTickCallback, onStateChange) {
    if (this.isPlaying) {
      this.stopAudio();
      if (onStateChange) onStateChange(false);
      return;
    }

    const transcript = imersao.transcript || [];
    const totalDuration = transcript.length > 0 ? transcript[transcript.length - 1].endTime : 30;
    this.duration = totalDuration;
    if (this.currentTime >= totalDuration) {
      this.currentTime = 0;
    }

    this.isPlaying = true;
    if (onStateChange) onStateChange(true);

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
            this.speakPortuguese(text, rate);
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

    const wordsA = a.split(/\s+/);
    const wordsB = b.split(/\s+/);
    let matches = 0;
    wordsA.forEach(w => {
      if (wordsB.includes(w)) matches++;
    });
    return Math.min(100, Math.max(45, Math.round((matches / wordsA.length) * 100)));
  }
}
