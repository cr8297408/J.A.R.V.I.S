import React from 'react';
import { motion } from 'framer-motion';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Mic,
  Brain,
  Terminal,
  Zap,
  ShieldCheck,
  Cpu,
  CheckCircle2,
  AlertCircle,
  Code2,
  Github,
  Star
} from 'lucide-react';
import { Button } from './ui/button';

const ProjectInfo: React.FC = () => {
  const features = [
    {
      title: 'Control por Voz',
      description: 'Interacción manos libres con la CLI de Gemini mediante STT (Speech-to-Text).',
      icon: <Mic className="h-6 w-6 text-accent-blue" />,
    },
    {
      title: 'Cerebro Inteligente',
      description: 'Integración con Gemini, Groq y OpenRouter para procesamiento de lenguaje natural.',
      icon: <Brain className="h-6 w-6" style={{ color: '#a855f7' }} />,
    },
    {
      title: 'Inyección de Comandos',
      description: "Capacidad de 'escribir' comandos directamente en tu terminal activa.",
      icon: <Terminal className="h-6 w-6 text-status-success" />,
    },
    {
      title: 'Resúmenes de Código',
      description: 'Detección inteligente de bloques de código para resúmenes automáticos por voz.',
      icon: <Code2 className="h-6 w-6 text-status-warning" />,
    },
  ];

  const techStack = [
    { category: 'Lenguaje', items: ['Python 3.10+', 'TypeScript (React)'] },
    { category: 'IA/ML', items: ['Gemini AI', 'Whisper (STT)', 'WebRTC VAD'] },
    { category: 'Audio', items: ['Edge TTS', 'macOS Say', 'PyAudio'] },
    { category: 'Arquitectura', items: ['Puertos y Adaptadores', 'Asyncio', 'Daemon Server'] },
  ];

  const fadeIn = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] }
    }
  };

  const staggerContainer = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 space-y-16 max-w-5xl">

      {/* Propósito */}
      <motion.section 
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
        variants={fadeIn}
        className="max-w-4xl mx-auto text-center space-y-4"
      >
        <h2 className="text-3xl font-bold tracking-tight text-text-primary">Propósito del Proyecto</h2>
        <p className="text-text-secondary leading-relaxed">
          J.A.R.V.I.S. nace como una extensión para potenciar la experiencia de uso de la CLI de Gemini.
          Su objetivo es eliminar la fricción entre el pensamiento y la ejecución, permitiendo a los
          desarrolladores interactuar con su asistente de IA mediante la voz mientras mantienen las manos en el teclado.
        </p>
      </motion.section>

      {/* Características Principales */}
      <section id="features" className="space-y-8">
        <motion.div 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeIn}
          className="text-center space-y-2"
        >
          <h2 className="text-3xl font-bold tracking-tight text-text-primary">Características Clave</h2>
          <p className="text-text-secondary">Tecnología de vanguardia para tu terminal.</p>
        </motion.div>
        
        <motion.div 
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          {features.map((feature, index) => (
            <motion.div key={index} variants={fadeIn}>
              <Card variant="glass" hoverable padding="md" className="h-full">
                <CardHeader>
                  <div className="mb-2">{feature.icon}</div>
                  <CardTitle className="text-xl">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-sm leading-relaxed">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* Arquitectura */}
      <section id="architecture" className="space-y-8 py-8 overflow-hidden">
        <div className="flex flex-col md:flex-row gap-12 items-center">
          <motion.div 
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="flex-1 space-y-6"
          >
            <h2 className="text-3xl font-bold tracking-tight text-text-primary">Arquitectura de Puertos y Adaptadores</h2>
            <p className="text-text-secondary leading-relaxed">
              Diseñado bajo principios de arquitectura limpia, J.A.R.V.I.S. separa la lógica de negocio de las implementaciones tecnológicas.
              Esto permite intercambiar motores de STT, TTS o LLMs sin afectar el núcleo del sistema.
            </p>
            <div className="grid grid-cols-2 gap-4">
              {techStack.map((tech, idx) => (
                <div key={idx} className="space-y-2">
                  <h4 className="font-semibold text-sm uppercase tracking-wider text-accent-blue">{tech.category}</h4>
                  <div className="flex flex-wrap gap-2">
                    {tech.items.map((item, i) => (
                      <Badge key={i} variant="default" size="sm">
                        {item}
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
          
          <motion.div 
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="flex-1 w-full max-w-md"
          >
            <Card variant="outlined" padding="md" className="relative">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-accent-blue/20 to-purple-500/20 rounded-2xl blur opacity-30" />
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="h-5 w-5 text-accent-blue" /> Flujo de Datos
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm relative">
                {[
                  { num: 1, label: 'VAD Listener', desc: 'Detecta actividad de voz en tiempo real.' },
                  { num: 2, label: 'STT Adapter', desc: 'Transcribe el audio a texto técnico.' },
                  { num: 3, label: 'Jarvis Brain', desc: 'Evalúa la intención y procesa con LLM.' },
                  { num: 4, label: 'Output Handler', desc: 'Inyecta comandos o responde vía TTS.' },
                ].map(({ num, label, desc }) => (
                  <div key={num} className="flex items-start gap-3 group">
                    <div className="h-6 w-6 rounded-full bg-accent-blue/20 text-accent-blue flex items-center justify-center shrink-0 text-xs font-bold group-hover:scale-110 transition-transform">
                      {num}
                    </div>
                    <p className="text-text-secondary">
                      <span className="font-semibold text-text-primary">{label}:</span> {desc}
                    </p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </section>

      {/* Estado del Proyecto */}
      <section id="status" className="max-w-4xl mx-auto space-y-8">
        <motion.div 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={fadeIn}
          className="text-center space-y-2"
        >
          <h2 className="text-3xl font-bold tracking-tight text-text-primary">Estado del Desarrollo</h2>
          <p className="text-text-secondary">Seguimiento de hitos y estabilidad.</p>
        </motion.div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <Card variant="glass" padding="md" className="border-status-success/20 h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-status-success">
                  <CheckCircle2 className="h-5 w-5" /> Completado
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-text-secondary">
                  <li>• Core Lexer e interceptor PTY</li>
                  <li>• Integración con Gemini AI y Groq</li>
                  <li>• Sistema de Adaptadores TTS/STT</li>
                  <li>• Daemon de red para notificaciones</li>
                </ul>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <Card variant="glass" padding="md" className="border-status-warning/20 h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-status-warning">
                  <AlertCircle className="h-5 w-5" /> En Progreso
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-text-secondary">
                  <li>• Refactorización a Asyncio puro</li>
                  <li>• Implementación de FSM global</li>
                  <li>• Mejora de latencia en STT local</li>
                  <li>• Confirmación de comandos vía IA</li>
                </ul>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </section>

      {/* Guía de Instalación Rápida */}
      <section id="install" className="space-y-8">
        <motion.div 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          variants={fadeIn}
          className="text-center space-y-2"
        >
          <h2 className="text-3xl font-bold tracking-tight text-text-primary">Guía de Instalación Rápida</h2>
          <p className="text-text-secondary">Configura J.A.R.V.I.S. en pocos minutos y empieza a usar tu voz en la terminal.</p>
        </motion.div>
        
        <motion.div 
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto"
        >
          {/* GitHub card — full width */}
          <motion.div variants={fadeIn} className="md:col-span-2">
            <Card
              variant="glass"
              hoverable
              padding="md"
              className="border-accent-blue/30 cursor-pointer group"
              onClick={() => window.open('https://github.com/cr8297408/J.A.R.V.I.S', '_blank')}
            >
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-lg">
                  Paso 0: ¡Deja tu estrella en 
                  <Button
                    variant="outline"
                    size="sm"
                    leftIcon={<Github className="h-4 w-4" />}
                    onClick={(e) => { e.stopPropagation(); window.open('https://github.com/cr8297408/J.A.R.V.I.S', '_blank'); }}
                  >
                    GitHub
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col sm:flex-row sm:items-center gap-6">
                  <div className="flex-1 space-y-2">
                    <CardDescription>
                      Antes de empezar, visita el repositorio, dale una ⭐ si el proyecto te gusta y clona el código en tu máquina.
                    </CardDescription>
                    <div className="flex items-center gap-2 mt-3">
                      <button
                        onClick={(e) => { e.stopPropagation(); window.open('https://github.com/cr8297408/J.A.R.V.I.S', '_blank'); }}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent-blue text-white text-sm font-medium hover:bg-accent-blue-hover transition-apple"
                      >
                        <Star className="h-4 w-4 fill-white" /> Dar estrella
                      </button>
                    </div>
                  </div>
                  <div className="flex-1">
                    <pre className="p-3 rounded-xl bg-black/40 border border-accent-blue/30 text-xs overflow-x-auto font-mono text-accent-blue">
                      <code>git clone https://github.com/cr8297408/J.A.R.V.I.S.git{'\n'}cd J.A.R.V.I.S</code>
                    </pre>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {[
            {
              title: 'Paso 1: Instalación Automática',
              icon: <Terminal className="h-5 w-5 text-accent-blue" />,
              desc: 'Ejecuta el script para configurar el entorno virtual, instalar dependencias y crear el comando global.',
              code: './install.sh',
              codeColor: 'text-accent-blue'
            },
            {
              title: 'Paso 2: Configuración de API Keys',
              icon: <ShieldCheck className="h-5 w-5" style={{ color: '#a855f7' }} />,
              desc: 'Añade tus claves en el archivo .env. Se recomienda Groq por su extrema rapidez.',
              code: 'ACTIVE_BRAIN_ENGINE=groq\nGROQ_API_KEY=tu_clave_aqui',
              codeColor: 'text-purple-400'
            },
            {
              title: 'Paso 3: Configuración de Hooks',
              icon: <Code2 className="h-5 w-5 text-status-warning" />,
              desc: 'Vincula el script de notificación en ~/.gemini/settings.json.',
              code: '{\n  "hooks": {\n    "notification": "/ruta/a/hooks/notification.py"\n  }\n}',
              codeColor: 'text-status-warning'
            }
          ].map((step, i) => (
            <motion.div key={i} variants={fadeIn}>
              <Card variant="glass" hoverable padding="md" className="h-full">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    {step.icon} {step.title}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <CardDescription>{step.desc}</CardDescription>
                  <pre className={`p-3 rounded-xl bg-black/40 border border-border-secondary text-xs overflow-x-auto font-mono ${step.codeColor}`}>
                    <code>{step.code}</code>
                  </pre>
                </CardContent>
              </Card>
            </motion.div>
          ))}

          <motion.div variants={fadeIn}>
            <Card variant="elevated" hoverable padding="md" className="relative overflow-hidden group h-full">
              <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
                <Zap className="h-16 w-16 text-accent-blue" />
              </div>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <CheckCircle2 className="h-5 w-5 text-status-success" /> Paso 4: ¡Inicia J.A.R.V.I.S.!
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <CardDescription>
                  ¡Todo listo! Ejecuta el comando global desde cualquier terminal para iniciar la experiencia por voz.
                </CardDescription>
                <pre className="p-3 rounded-xl bg-accent-blue/10 border border-accent-blue/30 text-xs overflow-x-auto font-mono text-accent-blue font-bold">
                  <code>jarvis</code>
                </pre>
              </CardContent>
            </Card>
          </motion.div>

        </motion.div>
      </section>
    </div>
  );
};

export default ProjectInfo;
