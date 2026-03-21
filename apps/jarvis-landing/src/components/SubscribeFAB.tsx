import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { GraduationCap, Users, Sparkles, ExternalLink } from "lucide-react";
import confetti from 'canvas-confetti';

const SubscribeFAB: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  const handleClick = () => {
    // Trigger confetti
    const duration = 5 * 1000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 9999 };

    const randomInRange = (min: number, max: number) => Math.random() * (max - min) + min;

    const interval: any = setInterval(function() {
      const timeLeft = animationEnd - Date.now();

      if (timeLeft <= 0) {
        return clearInterval(interval);
      }

      const particleCount = 50 * (timeLeft / duration);
      confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } });
      confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } });
    }, 250);

    setIsOpen(true);
  };

  return (
    <>
      <div className="fixed bottom-8 right-8 z-[100]">
        <Button 
          onClick={handleClick}
          className="animate-pulse-epic h-16 px-8 rounded-full bg-blue-600 hover:bg-blue-700 text-white font-bold text-lg shadow-[0_0_20px_rgba(59,130,246,0.5)] border-none group transition-all duration-300"
        >
          ¡Suscríbete! 🚀
          <Sparkles className="ml-2 h-5 w-5 transition-transform group-hover:rotate-12" />
        </Button>
      </div>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="bg-slate-950 border-2 border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.5)] text-slate-50 max-w-md sm:rounded-2xl overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-blue-500 to-transparent" />
          
          <DialogHeader className="pt-6">
            <div className="mx-auto w-16 h-16 rounded-full bg-blue-600/20 flex items-center justify-center mb-4 border border-blue-500/30">
              <Sparkles className="w-8 h-8 text-blue-400" />
            </div>
            <DialogTitle className="text-2xl font-black text-center text-blue-100">
              ¡Bienvenido a la élite de SmartCoderLabs! 🚀💻
            </DialogTitle>
            <DialogDescription className="text-blue-200/70 text-center text-lg mt-2">
              Gracias por apoyar el proyecto J.A.R.V.I.S.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-6">
            <p className="text-slate-300 text-center px-4">
              Estás a un paso de dominar el arte del código con la mejor tecnología.
            </p>
            
            <div className="grid grid-cols-1 gap-3 px-2">
              <a 
                href="https://smartcoderlabs.com/cursos" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center justify-between p-4 rounded-xl bg-blue-900/20 border border-blue-500/20 hover:border-blue-500/50 hover:bg-blue-900/40 transition-all group"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                    <GraduationCap className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="font-bold text-blue-100">Nuestros Cursos</div>
                    <div className="text-xs text-blue-300/60">Aprende de los mejores</div>
                  </div>
                </div>
                <ExternalLink className="w-4 h-4 text-blue-500/40 group-hover:text-blue-400 transition-colors" />
              </a>

              <a 
                href="https://discord.gg/smartcoderlabs" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center justify-between p-4 rounded-xl bg-slate-900/40 border border-blue-500/10 hover:border-blue-500/40 hover:bg-slate-800/60 transition-all group"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                    <Users className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="font-bold text-slate-100">SmartCoderLabs Community</div>
                    <div className="text-xs text-slate-400">Únete a la legión</div>
                  </div>
                </div>
                <ExternalLink className="w-4 h-4 text-slate-500/40 group-hover:text-slate-400 transition-colors" />
              </a>
            </div>
          </div>

          <div className="pb-6 text-center">
            <Button 
              onClick={() => setIsOpen(false)}
              variant="outline" 
              className="border-blue-500/30 text-blue-400 hover:bg-blue-500/10 hover:text-blue-300"
            >
              Cerrar y seguir explorando
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default SubscribeFAB;
