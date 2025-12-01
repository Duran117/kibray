/**
 * PhotoAnnotator - Sistema de anotación de fotos con Fabric.js
 * 
 * Permite dibujar, anotar y marcar sobre imágenes con las siguientes herramientas:
 * - Dibujo libre (brush)
 * - Flechas
 * - Rectángulos
 * - Círculos
 * - Texto
 * - Colores y grosores personalizables
 * 
 * Uso:
 * const annotator = new PhotoAnnotator('canvasId', imageUrl, existingAnnotations);
 * annotator.init();
 * const annotations = annotator.getAnnotations(); // Para guardar
 */

class PhotoAnnotator {
    constructor(canvasId, imageUrl, existingAnnotations = null) {
        this.canvasId = canvasId;
        this.imageUrl = imageUrl;
        this.existingAnnotations = existingAnnotations;
        this.canvas = null;
        this.currentTool = 'brush';
        this.currentColor = '#ff0000';
        this.brushWidth = 3;
        this.isDrawing = false;
        this.startX = 0;
        this.startY = 0;
        this.currentShape = null;
    }

    /**
     * Inicializar el canvas y cargar la imagen
     */
    async init() {
        const canvasElement = document.getElementById(this.canvasId);
        if (!canvasElement) {
            console.error(`Canvas element ${this.canvasId} not found`);
            return false;
        }

        // Inicializar Fabric.js canvas
        this.canvas = new fabric.Canvas(this.canvasId, {
            isDrawingMode: true,
            backgroundColor: '#f0f0f0'
        });

        // Configurar brush inicial
        this.canvas.freeDrawingBrush.color = this.currentColor;
        this.canvas.freeDrawingBrush.width = this.brushWidth;

        // Cargar imagen de fondo
        await this.loadImage();

        // Cargar anotaciones existentes si las hay
        if (this.existingAnnotations) {
            this.loadAnnotations(this.existingAnnotations);
        }

        // Event listeners para dibujo de formas
        this.setupShapeDrawing();

        return true;
    }

    /**
     * Cargar imagen en el canvas
     */
    loadImage() {
        return new Promise((resolve, reject) => {
            fabric.Image.fromURL(this.imageUrl, (img) => {
                if (!img) {
                    reject(new Error('Failed to load image'));
                    return;
                }

                // Calcular dimensiones manteniendo aspect ratio
                const maxWidth = 800;
                const maxHeight = 600;
                const scale = Math.min(
                    maxWidth / img.width,
                    maxHeight / img.height,
                    1 // No agrandar
                );

                img.scale(scale);
                
                // Ajustar tamaño del canvas a la imagen
                this.canvas.setDimensions({
                    width: img.width * scale,
                    height: img.height * scale
                });

                // Establecer como background
                this.canvas.setBackgroundImage(img, this.canvas.renderAll.bind(this.canvas), {
                    scaleX: scale,
                    scaleY: scale
                });

                resolve();
            }, { crossOrigin: 'anonymous' });
        });
    }

    /**
     * Configurar herramientas de dibujo
     */
    setupShapeDrawing() {
        this.canvas.on('mouse:down', (options) => {
            if (this.currentTool === 'brush') return;

            this.isDrawing = true;
            const pointer = this.canvas.getPointer(options.e);
            this.startX = pointer.x;
            this.startY = pointer.y;

            // Crear forma según herramienta
            switch (this.currentTool) {
                case 'arrow':
                    this.currentShape = this.createArrow(this.startX, this.startY, this.startX, this.startY);
                    break;
                case 'rectangle':
                    this.currentShape = new fabric.Rect({
                        left: this.startX,
                        top: this.startY,
                        width: 0,
                        height: 0,
                        fill: 'transparent',
                        stroke: this.currentColor,
                        strokeWidth: this.brushWidth
                    });
                    break;
                case 'circle':
                    this.currentShape = new fabric.Circle({
                        left: this.startX,
                        top: this.startY,
                        radius: 0,
                        fill: 'transparent',
                        stroke: this.currentColor,
                        strokeWidth: this.brushWidth
                    });
                    break;
            }

            if (this.currentShape) {
                this.canvas.add(this.currentShape);
            }
        });

        this.canvas.on('mouse:move', (options) => {
            if (!this.isDrawing || this.currentTool === 'brush') return;

            const pointer = this.canvas.getPointer(options.e);

            switch (this.currentTool) {
                case 'arrow':
                    this.updateArrow(this.currentShape, this.startX, this.startY, pointer.x, pointer.y);
                    break;
                case 'rectangle':
                    this.currentShape.set({
                        width: pointer.x - this.startX,
                        height: pointer.y - this.startY
                    });
                    break;
                case 'circle':
                    const radius = Math.sqrt(
                        Math.pow(pointer.x - this.startX, 2) + 
                        Math.pow(pointer.y - this.startY, 2)
                    );
                    this.currentShape.set({ radius: radius });
                    break;
            }

            this.canvas.renderAll();
        });

        this.canvas.on('mouse:up', () => {
            this.isDrawing = false;
            this.currentShape = null;
        });
    }

    /**
     * Crear flecha
     */
    createArrow(x1, y1, x2, y2) {
        const line = new fabric.Line([x1, y1, x2, y2], {
            stroke: this.currentColor,
            strokeWidth: this.brushWidth,
            selectable: true
        });

        const angle = Math.atan2(y2 - y1, x2 - x1);
        const arrowLength = 15;
        const arrowAngle = Math.PI / 6;

        const arrowPoint1 = new fabric.Line([
            x2,
            y2,
            x2 - arrowLength * Math.cos(angle - arrowAngle),
            y2 - arrowLength * Math.sin(angle - arrowAngle)
        ], {
            stroke: this.currentColor,
            strokeWidth: this.brushWidth,
            selectable: false
        });

        const arrowPoint2 = new fabric.Line([
            x2,
            y2,
            x2 - arrowLength * Math.cos(angle + arrowAngle),
            y2 - arrowLength * Math.sin(angle + arrowAngle)
        ], {
            stroke: this.currentColor,
            strokeWidth: this.brushWidth,
            selectable: false
        });

        const arrow = new fabric.Group([line, arrowPoint1, arrowPoint2], {
            selectable: true
        });

        return arrow;
    }

    /**
     * Actualizar posición de flecha
     */
    updateArrow(arrow, x1, y1, x2, y2) {
        if (!arrow || !arrow._objects) return;

        const line = arrow._objects[0];
        const arrowPoint1 = arrow._objects[1];
        const arrowPoint2 = arrow._objects[2];

        line.set({ x2: x2 - x1, y2: y2 - y1 });

        const angle = Math.atan2(y2 - y1, x2 - x1);
        const arrowLength = 15;
        const arrowAngle = Math.PI / 6;

        arrowPoint1.set({
            x2: (x2 - x1) - arrowLength * Math.cos(angle - arrowAngle),
            y2: (y2 - y1) - arrowLength * Math.sin(angle - arrowAngle)
        });

        arrowPoint2.set({
            x2: (x2 - x1) - arrowLength * Math.cos(angle + arrowAngle),
            y2: (y2 - y1) - arrowLength * Math.sin(angle + arrowAngle)
        });
    }

    /**
     * Cambiar herramienta activa
     */
    setTool(tool) {
        this.currentTool = tool;
        this.canvas.isDrawingMode = (tool === 'brush');
        
        if (tool === 'select') {
            this.canvas.selection = true;
            this.canvas.forEachObject(obj => {
                obj.selectable = true;
            });
        } else {
            this.canvas.selection = false;
        }
    }

    /**
     * Cambiar color
     */
    setColor(color) {
        this.currentColor = color;
        this.canvas.freeDrawingBrush.color = color;
    }

    /**
     * Cambiar grosor de línea
     */
    setBrushWidth(width) {
        this.brushWidth = width;
        this.canvas.freeDrawingBrush.width = width;
    }

    /**
     * Agregar texto
     */
    addText(text = 'Texto') {
        const textObj = new fabric.IText(text, {
            left: 100,
            top: 100,
            fontFamily: 'Arial',
            fontSize: 20,
            fill: this.currentColor
        });
        this.canvas.add(textObj);
        this.canvas.setActiveObject(textObj);
        textObj.enterEditing();
    }

    /**
     * Deshacer última acción
     */
    undo() {
        const objects = this.canvas.getObjects();
        if (objects.length > 0) {
            const lastObject = objects[objects.length - 1];
            this.canvas.remove(lastObject);
            this.canvas.renderAll();
        }
    }

    /**
     * Limpiar todo
     */
    clear() {
        this.canvas.getObjects().forEach(obj => {
            if (obj !== this.canvas.backgroundImage) {
                this.canvas.remove(obj);
            }
        });
        this.canvas.renderAll();
    }

    /**
     * Eliminar objeto seleccionado
     */
    deleteSelected() {
        const activeObject = this.canvas.getActiveObject();
        if (activeObject) {
            this.canvas.remove(activeObject);
            this.canvas.renderAll();
        }
    }

    /**
     * Obtener anotaciones como JSON
     */
    getAnnotations() {
        return JSON.stringify(this.canvas.toJSON());
    }

    /**
     * Cargar anotaciones desde JSON
     */
    loadAnnotations(jsonString) {
        try {
            const data = typeof jsonString === 'string' ? JSON.parse(jsonString) : jsonString;
            this.canvas.loadFromJSON(data, () => {
                this.canvas.renderAll();
            });
        } catch (error) {
            console.error('Error loading annotations:', error);
        }
    }

    /**
     * Exportar imagen con anotaciones
     */
    exportImage(format = 'png') {
        return this.canvas.toDataURL({
            format: format,
            quality: 0.9
        });
    }

    /**
     * Redimensionar canvas
     */
    resize(width, height) {
        this.canvas.setDimensions({
            width: width,
            height: height
        });
        this.canvas.renderAll();
    }
}

// Exportar para uso global
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PhotoAnnotator;
} else {
    window.PhotoAnnotator = PhotoAnnotator;
}
