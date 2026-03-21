import React, { useState } from 'react';
import { motion } from 'framer-motion';
import ProjectInfo from './components/ProjectInfo';
import ToolsSection from './components/ToolsSection';
import { Button } from '@/components/ui/button';
import { Modal, ModalHeader, ModalTitle, ModalContent, ModalCloseButton } from '@/components/ui/Modal';
import { NavBar, NavBarBrand, NavBarContent, NavBarItem } from '@/components/ui/NavBar';
import { Divider } from '@/components/ui/Divider';
import { Github, Play, ArrowRight } from 'lucide-react';
import './styles/apple-ds.css';
import './styles/App.css';

const App: React.FC = () => {
  const [demoOpen, setDemoOpen] = useState(false);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
        delayChildren: 0.2
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] }
    }
  };

  return (
    <div className="min-h-screen bg-background-primary text-text-primary font-sans">

      {/* Header/Nav — Apple Design System NavBar */}
      <motion.div
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        className="fixed top-0 left-0 right-0 z-50"
      >
        <NavBar variant="glass" sticky>
          <NavBarBrand href="/">
            <img src="/logo.png" alt="J.A.R.V.I.S. Logo" className="w-9 h-9 object-contain" />
            <span className="text-xl font-bold tracking-tight">J.A.R.V.I.S.</span>
          </NavBarBrand>

          <NavBarContent align="center" className="hidden md:flex">
            <NavBarItem href="#features">Características</NavBarItem>
            <NavBarItem href="#architecture">Arquitectura</NavBarItem>
            <NavBarItem href="#status">Estado</NavBarItem>
          </NavBarContent>

          <NavBarContent align="right">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Github className="h-4 w-4" />}
              onClick={() => window.open('https://github.com/cr8297408/J.A.R.V.I.S', '_blank')}
            >
              GitHub
            </Button>
          </NavBarContent>
        </NavBar>
      </motion.div>

      <main className="flex-1 pt-16">
        {/* Hero Section */}
        <section className="relative overflow-hidden py-24 lg:py-32">
          <div className="absolute inset-0 hero-gradient -z-10" />
          
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="container relative z-10 flex flex-col items-center text-center gap-8 mx-auto max-w-5xl px-4"
          >
            {/* Status pill */}
            <motion.div 
              variants={itemVariants}
              className="inline-flex items-center rounded-full border border-border-secondary px-4 py-1.5 text-sm font-medium bg-surface-secondary/50 backdrop-blur-sm shadow-sm"
            >
              <span className="flex h-2 w-2 rounded-full bg-accent-blue mr-2 animate-pulse" />
              <span className="opacity-90">v1.0.0-alpha en desarrollo</span>
            </motion.div>

            <motion.h1 
              variants={itemVariants}
              className="text-5xl font-extrabold tracking-tight sm:text-6xl lg:text-7xl"
            >
              <span className="text-gradient">J.A.R.V.I.S.</span>
            </motion.h1>
            
            <motion.p 
              variants={itemVariants}
              className="max-w-[680px] text-lg text-text-secondary sm:text-xl leading-relaxed"
            >
              La extensión de voz inteligente para la CLI de Gemini.
              Control manos libres, resúmenes de código inteligentes y un flujo de trabajo
              optimizado para desarrolladores modernos.
            </motion.p>

            <motion.div 
              variants={itemVariants}
              className="flex flex-col sm:flex-row gap-4 mt-4"
            >
              <Button
                size="lg"
                variant="primary"
                rightIcon={<ArrowRight className="h-5 w-5" />}
                onClick={() => document.getElementById('install')?.scrollIntoView({ behavior: 'smooth' })}
              >
                Comenzar ahora
              </Button>

              <Button
                size="lg"
                variant="outline"
                leftIcon={<Play className="h-5 w-5 fill-current" />}
                onClick={() => setDemoOpen(true)}
              >
                Ver Demo
              </Button>
            </motion.div>
          </motion.div>
        </section>

        <Divider className="max-w-5xl mx-auto" />

        <section id="features" className="py-12">
          <ProjectInfo />
        </section>

        <Divider className="max-w-5xl mx-auto" />

        <ToolsSection />
      </main>

      {/* Footer */}
      <footer className="border-t border-border-primary py-12 bg-surface-secondary/30">
        <div className="container mx-auto max-w-5xl px-4 flex flex-col items-center gap-8 md:flex-row md:justify-between">
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <img src="/logo.png" alt="J.A.R.V.I.S. Logo" className="w-8 h-8 object-contain" />
              <span className="font-bold text-text-primary">J.A.R.V.I.S.</span>
            </div>
            <p className="text-sm text-text-secondary">Just A Rather Very Intelligent System</p>
          </div>

          <div className="flex gap-12 text-sm">
            <div className="flex flex-col gap-3">
              <h4 className="font-semibold text-text-primary">Proyecto</h4>
              <a href="#docs" className="text-text-secondary hover:text-text-primary transition-apple">Documentación</a>
              <a href="#github" className="text-text-secondary hover:text-text-primary transition-apple">GitHub</a>
            </div>
            <div className="flex flex-col gap-3">
              <h4 className="font-semibold text-text-primary">Comunidad</h4>
              <a href="#smartcoderlabs" className="text-text-secondary hover:text-text-primary transition-apple">SmartCoderLabs</a>
              <a href="#discord" className="text-text-secondary hover:text-text-primary transition-apple">Discord</a>
            </div>
          </div>
        </div>
        <div className="container mx-auto max-w-5xl px-4 mt-12 pt-8 border-t border-border-primary text-center text-xs text-text-secondary">
          <p>&copy; {new Date().getFullYear()} J.A.R.V.I.S. Project. Desarrollado con ❤️ para la comunidad de SmartCoderLabs.</p>
        </div>
      </footer>

      {/* Demo Modal — Apple Design System Modal */}
      <Modal open={demoOpen} onOpenChange={setDemoOpen} size="xl">
        <ModalCloseButton />
        <ModalHeader>
          <ModalTitle>J.A.R.V.I.S. Demo</ModalTitle>
        </ModalHeader>
        <ModalContent>
          <div className="aspect-video overflow-hidden rounded-xl border border-border-secondary bg-black">
            <iframe
              width="100%"
              height="100%"
              src="https://www.youtube.com/embed/52X9yOZ_ICo"
              title="J.A.R.V.I.S. Demo"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        </ModalContent>
      </Modal>
    </div>
  );
};

export default App;
