import React, { useEffect, useRef } from 'react';

const FluidBackground = () => {
    const canvasRef = useRef(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const existingScript = Array.from(document.scripts).find(
            (script) =>
                script.dataset.fluidSim === 'true' ||
                script.src.includes('/background/webgl-fluid.js')
        );

        // Make sure this canvas is the first one on the page for the script to find it
        const ensureCanvasIsFirst = () => {
            const allCanvases = document.getElementsByTagName("canvas");
            if (allCanvases[0] !== canvas) {
                // Move our canvas to be first
                canvas.parentNode.insertBefore(canvas, canvas.parentNode.firstChild);
            }
        };

        ensureCanvasIsFirst();

        if (existingScript) {
            return;
        }

        // Load the WebGL fluid simulation script
        const script = document.createElement('script');
        script.src = '/background/webgl-fluid.js';
        script.async = false; // Load synchronously to ensure proper order
        script.dataset.fluidSim = 'true';
        
        script.onload = () => {
            console.log('Fluid simulation loaded and initialized');
        };

        script.onerror = (error) => {
            console.error('Failed to load fluid simulation:', error);
        };

        document.body.appendChild(script);

        return undefined;
    }, []);

    return (
        <canvas
            ref={canvasRef}
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                zIndex: 0,
                opacity: 0.5,
                pointerEvents: 'none'
            }}
        />
    );
};

export default FluidBackground;
