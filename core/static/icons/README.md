# PWA Icons - Placeholder Notice

## Current Status
Los archivos de íconos en este directorio son **placeholders temporales**.

## Generar Íconos Finales

### Opción 1: Usando el Generador Web (Recomendado)
1. Abre en tu navegador: `generate-icons.html`
2. Se generarán automáticamente todos los tamaños
3. Descarga cada ícono (o todos con el botón ZIP)
4. Guarda los archivos PNG en esta carpeta
5. Reemplaza los placeholders

### Opción 2: Usando Herramientas Online
1. Ve a: https://realfavicongenerator.net/ o https://www.pwabuilder.com/
2. Sube el archivo `icon.svg`
3. Genera los tamaños: 72, 96, 128, 144, 152, 192, 384, 512
4. Descarga y guarda en esta carpeta

### Opción 3: Usando ImageMagick (Terminal)
```bash
cd /Users/jesus/Documents/kibray/core/static/icons/

# Convertir SVG a PNG en diferentes tamaños
for size in 72 96 128 144 152 192 384 512; do
  convert icon.svg -resize ${size}x${size} icon-${size}x${size}.png
done
```

## Tamaños Requeridos
- icon-72x72.png
- icon-96x96.png
- icon-128x128.png
- icon-144x144.png
- icon-152x152.png
- icon-192x192.png (Android)
- icon-384x384.png
- icon-512x512.png (Android maskable)

## Notas
- El ícono base es `icon.svg` (letra K + brocha de pintura)
- Colores: Azul #1e3a8a (fondo), Blanco (letra K), Amarillo #fbbf24 (brocha)
- El sistema PWA funcionará con placeholders, pero se recomienda generar íconos finales
