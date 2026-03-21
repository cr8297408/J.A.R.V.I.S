import React from 'react';
import ProjectInfo from './components/ProjectInfo';
import SubscribeFAB from './components/SubscribeFAB';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Github, Play, ArrowRight, Send, Youtube, Twitch, MessageSquare } from "lucide-react";
import './styles/App.css';

const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      {/* Header/Nav */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="J.A.R.V.I.S. Logo" className="w-10 h-10 object-contain" />
            <span className="text-xl font-bold tracking-tight">J.A.R.V.I.S.</span>
          </div>
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
            <a href="#features" className="transition-colors hover:text-primary">Características</a>
            <a href="#architecture" className="transition-colors hover:text-primary">Arquitectura</a>
            <a href="#status" className="transition-colors hover:text-primary">Estado</a>
            <Button variant="outline" size="sm" asChild>
              <a href="https://github.com/cr8297408/J.A.R.V.I.S" target="_blank" rel="noopener noreferrer">
                <Github className="mr-2 h-4 w-4" /> GitHub
              </a>
            </Button>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative overflow-hidden py-24 lg:py-32">
          <div className="absolute inset-0 hero-gradient -z-10" />
          <div className="container relative z-10 flex flex-col items-center text-center gap-8">
            <div className="inline-flex items-center rounded-full border px-4 py-1.5 text-sm font-medium bg-muted/50">
              <span className="flex h-2 w-2 rounded-full bg-blue-500 mr-2" />
              v1.0.0-alpha en desarrollo
            </div>
            <h1 className="text-4xl font-extrabold tracking-tight sm:text-6xl lg:text-7xl">
              <span className="text-gradient">J.A.R.V.I.S.</span>
            </h1>
            <p className="max-w-[700px] text-lg text-muted-foreground sm:text-xl">
              La extensión de voz inteligente para la CLI de Gemini. 
              Control manos libres, resúmenes de código inteligentes y un flujo de trabajo optimizado para desarrolladores modernos.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 mt-4">
              <Button size="lg" className="h-12 px-8">
                Comenzar ahora <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              <Dialog>
                <DialogTrigger asChild>
                  <Button size="lg" variant="outline" className="h-12 px-8">
                    <Play className="mr-2 h-5 w-5 fill-current" /> Ver Demo
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[800px] bg-background border-blue-500/20 shadow-2xl shadow-blue-500/10">
                  <DialogHeader>
                    <DialogTitle className="text-2xl font-bold">J.A.R.V.I.S. Demo</DialogTitle>
                  </DialogHeader>
                  <div className="aspect-video mt-4 overflow-hidden rounded-xl border border-blue-500/20 bg-black">
                    <iframe
                      width="100%"
                      height="100%"
                      src="https://www.youtube.com/embed/dQw4w9WgXcQ"
                      title="J.A.R.V.I.S. Demo"
                      frameBorder="0"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                    ></iframe>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </section>

        <Separator className="container" />

        <section id="features" className="py-12">
          <ProjectInfo />
        </section>

        {/* Newsletter Section - Hidden temporarily
        <section className="py-24 relative overflow-hidden">
          <div className="container relative z-10">
            <div className="mx-auto max-w-4xl rounded-3xl border bg-card/50 backdrop-blur-md p-8 md:p-12 shadow-2xl border-blue-500/20">
              <div className="flex flex-col md:flex-row items-center gap-8 md:gap-12">
                <div className="flex-1 text-center md:text-left">
                  <h2 className="text-3xl font-bold tracking-tight sm:text-4xl mb-4">
                    Únete a la iniciativa <span className="text-gradient">J.A.R.V.I.S.</span>
                  </h2>
                  <p className="text-muted-foreground text-lg">
                    Suscríbete para recibir actualizaciones exclusivas, acceso temprano a nuevas funciones y noticias sobre el desarrollo del sistema.
                  </p>
                </div>
                <div className="w-full md:w-auto flex-shrink-0">
                  <form className="flex flex-col sm:flex-row gap-3 w-full max-w-md mx-auto md:mx-0" onSubmit={(e) => e.preventDefault()}>
                    <Input 
                      type="email" 
                      placeholder="tu@email.com" 
                      className="h-12 bg-background/50 border-blue-500/20 focus:border-blue-500/50 transition-all duration-300"
                      required
                    />
                    <Button type="submit" className="h-12 px-6 group transition-all duration-300 hover:shadow-[0_0_20px_rgba(59,130,246,0.5)] bg-blue-600 hover:bg-blue-700 text-white border-none">
                      Suscribirse
                      <Send className="ml-2 h-4 w-4 transition-transform duration-300 group-hover:translate-x-1 group-hover:-translate-y-1" />
                    </Button>
                  </form>
                </div>
              </div>
            </div>
          </div>
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full -z-10 opacity-30">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-500/20 rounded-full blur-[100px]" />
          </div>
        </section>
        */}

        {/* Comunidad Section - Hidden temporarily
        <section id="comunidad" className="py-24 relative bg-muted/10 border-t border-b border-white/5">
          <div className="container relative z-10">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl mb-4">SmartCoderLabs <span className="text-gradient font-black">COMMUNITY</span></h2>
              <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
                Únete a miles de desarrolladores, aprende nuevas tecnologías y comparte tus experiencias con la comunidad más apasionada.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <a 
                href="https://youtube.com/@SmartCoderLabs" 
                target="_blank" 
                rel="noopener noreferrer"
                className="group relative flex flex-col items-center p-8 rounded-3xl border bg-card/40 backdrop-blur-sm transition-all duration-500 hover:scale-105 animate-glow-red border-red-500/10 hover:border-red-500/30 overflow-hidden"
              >
                <div className="absolute inset-0 bg-red-600/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="w-16 h-16 rounded-2xl bg-red-600/10 flex items-center justify-center mb-6 group-hover:rotate-12 transition-transform duration-500">
                  <Youtube className="w-8 h-8 text-red-600" />
                </div>
                <h3 className="text-xl font-bold mb-2">YouTube</h3>
                <p className="text-muted-foreground text-center mb-6 text-sm">Contenido de alta calidad para desarrolladores modernos.</p>
                <div className="mt-auto w-full space-y-3">
                  <div className="flex items-center justify-between text-[10px] font-black uppercase tracking-widest">
                    <span className="text-red-500 bg-red-500/10 px-2 py-0.5 rounded">¡SUSCRÍBETE!</span>
                    <span className="text-muted-foreground">85K+ Subs</span>
                  </div>
                  <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-red-600 w-[85%] relative overflow-hidden">
                       <div className="absolute inset-0 bg-white/20 animate-[pulse_1.5s_infinite]" />
                    </div>
                  </div>
                  <div className="text-center text-[10px] text-muted-foreground mt-2 font-medium">¡Únete a la legión!</div>
                </div>
              </a>

              <a 
                href="https://twitch.tv/smartcoderlabs" 
                target="_blank" 
                rel="noopener noreferrer"
                className="group relative flex flex-col items-center p-8 rounded-3xl border bg-card/40 backdrop-blur-sm transition-all duration-500 hover:scale-105 animate-glow-purple border-purple-500/10 hover:border-purple-500/30 overflow-hidden"
              >
                <div className="absolute inset-0 bg-purple-600/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="absolute top-4 right-4 flex items-center gap-1.5 bg-red-600 text-white text-[10px] font-black px-2 py-1 rounded-md uppercase tracking-tighter animate-bounce">
                  <span className="w-1.5 h-1.5 bg-white rounded-full" />
                  Live
                </div>
                <div className="w-16 h-16 rounded-2xl bg-purple-600/10 flex items-center justify-center mb-6 group-hover:-rotate-12 transition-transform duration-500">
                  <Twitch className="w-8 h-8 text-purple-600" />
                </div>
                <h3 className="text-xl font-bold mb-2">Twitch</h3>
                <p className="text-muted-foreground text-center mb-6 text-sm">Directos de programación, reviews y chill cada semana.</p>
                <div className="mt-auto w-full">
                  <Button variant="secondary" className="w-full bg-purple-600/10 hover:bg-purple-600/20 text-purple-400 border-purple-500/20 group-hover:bg-purple-600 group-hover:text-white transition-all duration-300">
                    Seguir Canal
                  </Button>
                </div>
              </a>

              <a 
                href="https://discord.gg/smartcoderlabs" 
                target="_blank" 
                rel="noopener noreferrer"
                className="group relative flex flex-col items-center p-8 rounded-3xl border bg-card/40 backdrop-blur-sm transition-all duration-500 hover:scale-105 animate-glow-blue border-blue-500/10 hover:border-blue-500/30 overflow-hidden"
              >
                <div className="absolute inset-0 bg-blue-600/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="w-16 h-16 rounded-2xl bg-blue-600/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-500">
                  <MessageSquare className="w-8 h-8 text-blue-600" />
                </div>
                <h3 className="text-xl font-bold mb-2">Discord</h3>
                <p className="text-muted-foreground text-center mb-6 text-sm">Únete a la charla, resuelve dudas y haz networking real.</p>
                <div className="mt-auto w-full">
                  <Button variant="secondary" className="w-full bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 border-blue-500/20 group-hover:bg-blue-600 group-hover:text-white transition-all duration-300">
                    Únete al servidor
                  </Button>
                </div>
              </a>
            </div>
          </div>
        </section>
        */}
      </main>

      <footer className="border-t py-12 bg-muted/30">
        <div className="container flex flex-col items-center gap-8 md:flex-row md:justify-between">
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <img src="/logo.png" alt="J.A.R.V.I.S. Logo" className="w-8 h-8 object-contain" />
              <span className="font-bold">J.A.R.V.I.S.</span>
            </div>
            <p className="text-sm text-muted-foreground">Just A Rather Very Intelligent System</p>
          </div>
          
          <div className="flex gap-12 text-sm">
            <div className="flex flex-col gap-3">
              <h4 className="font-semibold">Proyecto</h4>
              <a href="#docs" className="text-muted-foreground hover:text-foreground">Documentación</a>
              <a href="#github" className="text-muted-foreground hover:text-foreground">GitHub</a>
            </div>
            <div className="flex flex-col gap-3">
              <h4 className="font-semibold">Comunidad</h4>
              <a href="#smartcoderlabs" className="text-muted-foreground hover:text-foreground">SmartCoderLabs</a>
              <a href="#discord" className="text-muted-foreground hover:text-foreground">Discord</a>
            </div>
          </div>
        </div>
        <div className="container mt-12 pt-8 border-t text-center text-xs text-muted-foreground">
          <p>&copy; {new Date().getFullYear()} J.A.R.V.I.S. Project. Desarrollado con ❤️ para la comunidad de SmartCoderLabs.</p>
        </div>
      </footer>
      {/* <SubscribeFAB /> */}
    </div>
  );
};

export default App;
