import React from 'react';
import { motion } from 'framer-motion';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from './ui/card';
import { Button } from './ui/button';
import { 
  Github, 
  Layout, 
  Zap, 
  Wind, 
  Atom, 
  Layers, 
  Brain, 
  Terminal 
} from 'lucide-react';

const tools = [
  {
    name: 'Apple Design System',
    description: 'Sistema de diseño premium inspirado en Apple para componentes React modernos y elegantes.',
    icon: <Layout className="h-6 w-6 text-accent-blue" />,
    link: 'https://github.com/smart-coder-labs/design-system',
    tag: 'UI/UX'
  },
  {
    name: 'Gemini AI & Groq',
    description: 'Procesamiento de lenguaje natural ultrarrápido y modelos de visión avanzados.',
    icon: <Brain className="h-6 w-6 text-purple-500" />,
    link: 'https://groq.com/',
    tag: 'AI Brain'
  },
  {
    name: 'Python Asyncio',
    description: 'Core de la CLI diseñado para concurrencia masiva y latencia mínima en tiempo real.',
    icon: <Terminal className="h-6 w-6 text-green-500" />,
    link: 'https://docs.python.org/3/library/asyncio.html',
    tag: 'Core'
  },
  {
    name: 'React 18',
    description: 'La base de nuestra interfaz de usuario, optimizada para rendimiento y reactividad.',
    icon: <Atom className="h-6 w-6 text-blue-400" />,
    link: 'https://react.dev/',
    tag: 'Frontend'
  },
  {
    name: 'Vite',
    description: 'Herramienta de build de última generación para una experiencia de desarrollo instantánea.',
    icon: <Zap className="h-6 w-6 text-yellow-400" />,
    link: 'https://vitejs.dev/',
    tag: 'Build Tool'
  },
  {
    name: 'Tailwind CSS',
    description: 'Framework de CSS enfocado en utilidades para diseños altamente personalizados.',
    icon: <Wind className="h-6 w-6 text-cyan-400" />,
    link: 'https://tailwindcss.com/',
    tag: 'Styling'
  }
];

const ToolsSection: React.FC = () => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] }
    }
  };

  return (
    <section id="tools" className="py-24 bg-surface-secondary/10 overflow-hidden">
      <div className="container mx-auto px-4 max-w-5xl space-y-12">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center space-y-4"
        >
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-text-primary italic">
            Nuestra <span className="text-gradient">Caja de Herramientas</span>
          </h2>
          <p className="text-text-secondary max-w-2xl mx-auto">
            Utilizamos las mejores tecnologías del mercado para construir un sistema potente, 
            estable y con una experiencia de usuario de primer nivel.
          </p>
        </motion.div>

        <motion.div 
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {tools.map((tool, index) => (
            <motion.div key={index} variants={itemVariants}>
              <Card variant="glass" hoverable padding="md" className="flex flex-col h-full border-border-primary/50 group">
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-2.5 rounded-xl bg-surface-secondary border border-border-primary group-hover:scale-110 group-hover:bg-accent-blue/5 transition-all duration-300">
                      {tool.icon}
                    </div>
                    <span className="text-[10px] font-bold uppercase tracking-widest text-text-secondary/60 bg-surface-secondary/50 px-2 py-1 rounded-full border border-border-primary/30">
                      {tool.tag}
                    </span>
                  </div>
                  <CardTitle className="text-xl font-bold group-hover:text-accent-blue transition-colors">
                    {tool.name}
                  </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col justify-between gap-6">
                  <CardDescription className="text-sm leading-relaxed text-text-secondary">
                    {tool.description}
                  </CardDescription>
                  <Button
                    variant="outline"
                    size="sm"
                    fullWidth
                    rightIcon={<Github className="h-3.5 w-3.5" />}
                    onClick={() => window.open(tool.link, '_blank')}
                    className="mt-auto opacity-80 group-hover:opacity-100 group-hover:border-accent-blue/50"
                  >
                    Saber más
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};

export default ToolsSection;
