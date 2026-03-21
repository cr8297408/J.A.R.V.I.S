import React from 'react';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Mic, 
  Brain, 
  Terminal, 
  Zap, 
  ShieldCheck, 
  Cpu,
  CheckCircle2,
  AlertCircle,
  Code2
} from "lucide-react";

const ProjectInfo: React.FC = () => {
  const features = [
    {
      title: "Control por Voz",
      description: "Interacción manos libres con la CLI de Gemini mediante STT (Speech-to-Text).",
      icon: <Mic className="h-6 w-6 text-blue-500" />,
    },
    {
      title: "Cerebro Inteligente",
      description: "Integración con Gemini, Groq y OpenRouter para procesamiento de lenguaje natural.",
      icon: <Brain className="h-6 w-6 text-purple-500" />,
    },
    {
      title: "Inyección de Comandos",
      description: "Capacidad de 'escribir' comandos directamente en tu terminal activa.",
      icon: <Terminal className="h-6 w-6 text-green-500" />,
    },
    {
      title: "Resúmenes de Código",
      description: "Detección inteligente de bloques de código para resúmenes automáticos por voz.",
      icon: <Code2 className="h-6 w-6 text-orange-500" />,
    },
  ];

  const techStack = [
    { category: "Lenguaje", items: ["Python 3.10+", "TypeScript (React)"] },
    { category: "IA/ML", items: ["Gemini AI", "Whisper (STT)", "WebRTC VAD"] },
    { category: "Audio", items: ["Edge TTS", "macOS Say", "PyAudio"] },
    { category: "Arquitectura", items: ["Puertos y Adaptadores", "Asyncio", "Daemon Server"] },
  ];

  return (
    <div className="container mx-auto px-4 py-8 space-y-16">
      {/* Propósito */}
      <section className="max-w-4xl mx-auto text-center space-y-4">
        <h2 className="text-3xl font-bold tracking-tight">Propósito del Proyecto</h2>
        <p className="text-muted-foreground leading-relaxed">
          J.A.R.V.I.S. nace como una extensión para potenciar la experiencia de uso de la CLI de Gemini. 
          Su objetivo es eliminar la fricción entre el pensamiento y la ejecución, permitiendo a los 
          desarrolladores interactuar con su asistente de IA mediante la voz mientras mantienen las manos en el teclado.
        </p>
      </section>

      {/* Características Principales */}
      <section id="features" className="space-y-8">
        <div className="text-center space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Características Clave</h2>
          <p className="text-muted-foreground">Tecnología de vanguardia para tu terminal.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <Card key={index} className="border-muted/40 hover:border-blue-500/50 transition-colors bg-card/50 backdrop-blur-sm">
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
          ))}
        </div>
      </section>

      {/* Arquitectura */}
      <section id="architecture" className="space-y-8 py-8">
        <div className="flex flex-col md:flex-row gap-12 items-center">
          <div className="flex-1 space-y-6">
            <h2 className="text-3xl font-bold tracking-tight">Arquitectura de Puertos y Adaptadores</h2>
            <p className="text-muted-foreground leading-relaxed">
              Diseñado bajo principios de arquitectura limpia, J.A.R.V.I.S. separa la lógica de negocio de las implementaciones tecnológicas. 
              Esto permite intercambiar motores de STT, TTS o LLMs sin afectar el núcleo del sistema.
            </p>
            <div className="grid grid-cols-2 gap-4">
              {techStack.map((tech, idx) => (
                <div key={idx} className="space-y-2">
                  <h4 className="font-semibold text-sm uppercase tracking-wider text-blue-400">{tech.category}</h4>
                  <div className="flex flex-wrap gap-2">
                    {tech.items.map((item, i) => (
                      <Badge key={i} variant="secondary" className="font-normal">
                        {item}
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="flex-1 w-full max-w-md">
            <Card className="border-muted/40 bg-muted/20">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="h-5 w-5 text-blue-500" /> Flujo de Datos
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                <div className="flex items-start gap-3">
                  <div className="h-6 w-6 rounded-full bg-blue-500/20 text-blue-500 flex items-center justify-center shrink-0">1</div>
                  <p><span className="font-semibold">VAD Listener:</span> Detecta actividad de voz en tiempo real.</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="h-6 w-6 rounded-full bg-blue-500/20 text-blue-500 flex items-center justify-center shrink-0">2</div>
                  <p><span className="font-semibold">STT Adapter:</span> Transcribe el audio a texto técnico.</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="h-6 w-6 rounded-full bg-blue-500/20 text-blue-500 flex items-center justify-center shrink-0">3</div>
                  <p><span className="font-semibold">Jarvis Brain:</span> Evalúa la intención y procesa con LLM.</p>
                </div>
                <div className="flex items-start gap-3">
                  <div className="h-6 w-6 rounded-full bg-blue-500/20 text-blue-500 flex items-center justify-center shrink-0">4</div>
                  <p><span className="font-semibold">Output Handler:</span> Inyecta comandos o responde vía TTS.</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Estado del Proyecto */}
      <section id="status" className="max-w-4xl mx-auto space-y-8">
        <div className="text-center space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Estado del Desarrollo</h2>
          <p className="text-muted-foreground">Seguimiento de hitos y estabilidad.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <Card className="border-green-500/20 bg-green-500/5">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-green-500">
                <CheckCircle2 className="h-5 w-5" /> Completado
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                <li>• Core Lexer e interceptor PTY</li>
                <li>• Integración con Gemini AI y Groq</li>
                <li>• Sistema de Adaptadores TTS/STT</li>
                <li>• Daemon de red para notificaciones</li>
              </ul>
            </CardContent>
          </Card>
          <Card className="border-amber-500/20 bg-amber-500/5">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-amber-500">
                <AlertCircle className="h-5 w-5" /> En Progreso
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                <li>• Refactorización a Asyncio puro</li>
                <li>• Implementación de FSM global</li>
                <li>• Mejora de latencia en STT local</li>
                <li>• Confirmación de comandos vía IA</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Guía de Instalación Rápida */}
      <section id="install" className="space-y-8">
        <div className="text-center space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Guía de Instalación Rápida</h2>
          <p className="text-muted-foreground">Configura J.A.R.V.I.S. en pocos minutos y empieza a usar tu voz en la terminal.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto">
          <Card className="border-muted/40 bg-card/50 backdrop-blur-sm hover:border-blue-500/30 transition-colors">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Terminal className="h-5 w-5 text-blue-500" /> Paso 1: Instalación Automática
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Ejecuta el script para configurar el entorno virtual, instalar dependencias y crear el comando global.
              </p>
              <pre className="p-3 rounded-lg bg-black/40 border border-muted/40 text-xs overflow-x-auto font-mono text-blue-300">
                <code>./install.sh</code>
              </pre>
            </CardContent>
          </Card>

          <Card className="border-muted/40 bg-card/50 backdrop-blur-sm hover:border-purple-500/30 transition-colors">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-lg">
                <ShieldCheck className="h-5 w-5 text-purple-500" /> Paso 2: Configuración de API Keys
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Añade tus claves en el archivo <code className="text-blue-400 text-xs">.env</code>. Se recomienda Groq por su extrema rapidez.
              </p>
              <pre className="p-3 rounded-lg bg-black/40 border border-muted/40 text-xs overflow-x-auto font-mono text-purple-300">
                <code>
                  ACTIVE_BRAIN_ENGINE=groq{"\n"}
                  GROQ_API_KEY=tu_clave_aqui
                </code>
              </pre>
            </CardContent>
          </Card>

          <Card className="border-muted/40 bg-card/50 backdrop-blur-sm hover:border-orange-500/30 transition-colors">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Code2 className="h-5 w-5 text-orange-500" /> Paso 3: Configuración de Hooks
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Vincula el script de notificación en <code className="text-blue-400 text-xs">~/.gemini/settings.json</code>.
              </p>
              <pre className="p-3 rounded-lg bg-black/40 border border-muted/40 text-xs overflow-x-auto font-mono text-orange-300">
                <code>
                  {"{"}{"\n"}
                  {"  "}"hooks": {"{"}{"\n"}
                  {"    "}"notification": "/ruta/a/hooks/notification.py"{"\n"}
                  {"  "}{"}"}{"\n"}
                  {"}"}
                </code>
              </pre>
            </CardContent>
          </Card>

          <Card className="border-blue-500/20 bg-blue-500/5 backdrop-blur-sm hover:border-blue-500/50 transition-colors relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
              <Zap className="h-16 w-16 text-blue-500" />
            </div>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-lg">
                <CheckCircle2 className="h-5 w-5 text-green-500" /> Paso 4: ¡Inicia J.A.R.V.I.S.!
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-muted-foreground">
                ¡Todo listo! Ejecuta el comando global desde cualquier terminal para iniciar la experiencia por voz.
              </p>
              <pre className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/30 text-xs overflow-x-auto font-mono text-blue-400 font-bold">
                <code>jarvis</code>
              </pre>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
};

export default ProjectInfo;
