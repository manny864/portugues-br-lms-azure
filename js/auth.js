/**
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
