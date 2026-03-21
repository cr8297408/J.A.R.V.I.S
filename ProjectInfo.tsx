import React from 'react';

const ProjectInfo: React.FC = () => {
  const styles = `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Fira+Code:wght@400;500&display=swap');

    :root {
      --primary: #4f46e5;
      --primary-hover: #4338ca;
      --bg: #0f172a;
      --card-bg: #1e293b;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #10b981;
      --border: #334155;
    }

    .project-container {
      font-family: 'Inter', sans-serif;
      background-color: var(--bg);
      color: var(--text);
      max-width: 900px;
      margin: 2rem auto;
      padding: 3rem;
      border-radius: 1.5rem;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
      border: 1px solid var(--border);
      line-height: 1.6;
    }

    header {
      text-align: center;
      margin-bottom: 4rem;
      border-bottom: 1px solid var(--border);
      padding-bottom: 2rem;
    }

    h1 {
      font-size: 3rem;
      font-weight: 800;
      background: linear-gradient(to right, #818cf8, #c084fc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 1rem;
    }

    .subtitle {
      font-size: 1.25rem;
      color: var(--text-muted);
      font-weight: 300;
    }

    section {
      margin-bottom: 3rem;
      animation: fadeIn 0.8s ease-out forwards;
    }

    h2 {
      font-size: 1.75rem;
      color: var(--accent);
      margin-bottom: 1.5rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .card {
      background: var(--card-bg);
      padding: 2rem;
      border-radius: 1rem;
      border: 1px solid var(--border);
      transition: transform 0.2s ease, border-color 0.2s ease;
    }

    .card:hover {
      transform: translateY(-4px);
      border-color: var(--primary);
    }

    .features-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 1.5rem;
    }

    .feature-item h3 {
      color: #818cf8;
      margin-top: 0;
      font-size: 1.25rem;
    }

    code, pre {
      font-family: 'Fira Code', monospace;
      background: #020617;
      padding: 0.2rem 0.4rem;
      border-radius: 0.25rem;
      font-size: 0.9em;
      color: #e2e8f0;
    }

    pre {
      padding: 1.5rem;
      overflow-x: auto;
      border: 1px solid var(--border);
      display: block;
      margin: 1rem 0;
    }

    .status-badge {
      display: inline-block;
      background: rgba(16, 185, 129, 0.1);
      color: var(--accent);
      padding: 0.5rem 1rem;
      border-radius: 9999px;
      font-weight: 600;
      font-size: 0.875rem;
      border: 1px solid var(--accent);
    }

    ul {
      list-style: none;
      padding: 0;
    }

    li {
      margin-bottom: 0.75rem;
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
    }

    li::before {
      content: "→";
      color: var(--primary);
      font-weight: bold;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 640px) {
      .project-container {
        margin: 1rem;
        padding: 1.5rem;
      }
      h1 { font-size: 2rem; }
    }
  `;

  return (
    <>
      <style>{styles}</style>
      <div className="project-container">
        <header>
          <h1>🎙️ Gemini Voice CLI Extension</h1>
          <p className="subtitle">Codename: J.A.R.V.I.S.</p>
        </header>

        <section>
          <h2>📝 Descripción General</h2>
          <div className="card">
            <p>
              <strong>J.A.R.V.I.S.</strong> es una extensión de interfaz de voz (Voice-First) diseñada para actuar como un intermediario inteligente para la CLI de Gemini.
            </p>
            <p>
              Optimiza el flujo de trabajo de los desarrolladores permitiendo un control "manos libres" y transformando las extensas salidas de texto o código en resúmenes conversacionales digeribles.
            </p>
          </div>
        </section>

        <section>
          <h2>🎯 El Problema que Resuelve</h2>
          <div className="card">
            <p>
              Los sistemas tradicionales de Text-to-Speech (TTS) fallan al intentar leer código fuente o respuestas largas de forma literal, interrumpiendo la concentración.
            </p>
            <p>
              <strong>J.A.R.V.I.S.</strong> intercepta estas salidas, las procesa mediante un "traductor inteligente" y permite interactuar mediante comandos de voz naturales.
            </p>
          </div>
        </section>

        <section>
          <h2>✨ Características Principales</h2>
          <div className="features-grid">
            <div className="card feature-item">
              <h3>1. Traductor Inteligente</h3>
              <p>Evita la lectura tediosa de bloques de código crudos. Genera resúmenes ejecutivos especializados.</p>
              <code>"He generado el script de Python solicitado. ¿Quieres que lo ejecute...?"</code>
            </div>
            <div className="card feature-item">
              <h3>2. Motor Híbrido de Voz</h3>
              <p>Soporte para proveedores locales (faster-whisper, Piper) y remotos (OpenAI, ElevenLabs). Flexibilidad total por configuración.</p>
            </div>
            <div className="card feature-item">
              <h3>3. Barge-in e Interrupción</h3>
              <p>Detección de Actividad de Voz (VAD) de ultra baja latencia. Interrumpe al asistente en cualquier momento.</p>
            </div>
            <div className="card feature-item">
              <h3>4. Control de Flujo</h3>
              <p>Reconocimiento de intenciones y pausa automática de acciones críticas hasta recibir aprobación verbal.</p>
            </div>
          </div>
        </section>

        <section>
          <h2>🏗️ Arquitectura Técnica</h2>
          <div className="card">
            <p>Sigue una <strong>Arquitectura Hexagonal</strong> para garantizar modularidad y facilitar el intercambio de tecnologías.</p>
            <h3>Componentes Core:</h3>
            <ul>
              <li><strong>FSM:</strong> Orquesta el ciclo de vida (IDLE, LISTENING, THINKING, etc.).</li>
              <li><strong>Orquestador:</strong> Lógica de negocio y coordinación de adaptadores.</li>
              <li><strong>Concurrencia:</strong> Threading estratégico para separar UI, audio y micrófono.</li>
            </ul>
            <h3>Stack Tecnológico:</h3>
            <p>Python 3.10+, PyAudio, Silero-VAD, Faster-Whisper, Piper-TTS, Gemini.</p>
          </div>
        </section>

        <section>
          <h2>📁 Estructura del Proyecto</h2>
          <pre>
{`├── core/           # Lógica principal, FSM y orquestación.
├── adapters/       # Implementaciones de STT, TTS y LLM.
├── audio/          # Captura con VAD y reproducción.
├── apps/           # Aplicaciones específicas.
├── hooks/          # Integración con el sistema.
└── docs/           # Documentación y registros.`}
          </pre>
        </section>

        <section>
          <h2>🚀 Estado del Proyecto</h2>
          <div className="card" style={{textAlign: 'center'}}>
            <span className="status-badge">Fase de Desarrollo (Draft/PoC)</span>
            <p style={{marginTop: '1rem', color: 'var(--text-muted)'}}>
              Arquitectura sólida diseñada para extensibilidad y rendimiento en tiempo real.
            </p>
          </div>
        </section>
      </div>
    </>
  );
};

export default ProjectInfo;
