/**
 * Matrix-style animated particles background.
 */
(function() {
    const canvas = document.getElementById('matrixCanvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    let animationId;
    
    // Set canvas size
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // Particle system
    const particles = [];
    const particleCount = 100;
    const neonCyan = '#00ffff';
    
    class Particle {
        constructor() {
            this.reset();
        }
        
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.speed = Math.random() * 2 + 1;
            this.size = Math.random() * 2 + 1;
            this.opacity = Math.random() * 0.5 + 0.2;
            this.life = Math.random() * 100 + 50;
        }
        
        update() {
            this.y += this.speed;
            this.life--;
            
            if (this.y > canvas.height || this.life <= 0) {
                this.reset();
                this.y = 0;
            }
        }
        
        draw() {
            ctx.fillStyle = neonCyan;
            ctx.globalAlpha = this.opacity;
            ctx.fillRect(this.x, this.y, this.size, this.size * 3);
            
            // Glow effect
            ctx.shadowBlur = 10;
            ctx.shadowColor = neonCyan;
            ctx.fillRect(this.x, this.y, this.size, this.size * 3);
            ctx.shadowBlur = 0;
        }
    }
    
    // Initialize particles
    for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
    }
    
    // Animation loop
    function animate() {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        particles.forEach(particle => {
            particle.update();
            particle.draw();
        });
        
        animationId = requestAnimationFrame(animate);
    }
    
    // Start animation
    animate();
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        if (animationId) {
            cancelAnimationFrame(animationId);
        }
    });
})();

