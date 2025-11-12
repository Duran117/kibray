#!/usr/bin/env python
# Script para arreglar traducciones en django.po
import re

# Leer archivo
with open('locale/es/LC_MESSAGES/django.po', 'r', encoding='utf-8') as f:
    content = f.read()

# Reparar msgstr duplicado en línea 157
content = content.replace('msgstr "Fecha"\nmsgstr ""', 'msgstr "Fecha"')

# Agregar traducciones faltantes
translations = {
    'msgid "Tipo"\nmsgstr ""': 'msgid "Tipo"\nmsgstr "Tipo"',
    'msgid "Cant"\nmsgstr "Cantidad"': 'msgid "Cant"\nmsgstr "Cant"',
    'msgid "Desde"\nmsgstr ""': 'msgid "Desde"\nmsgstr "Desde"',
    'msgid "Hacia"\nmsgstr ""': 'msgid "Hacia"\nmsgstr "Hacia"',
    'msgid "Por"\nmsgstr ""': 'msgid "Por"\nmsgstr "Por"',
    'msgid "Nota"\nmsgstr "Notas"': 'msgid "Nota"\nmsgstr "Nota"',
    'msgid "Sin movimientos."\nmsgstr "Registrar movimiento"': 'msgid "Sin movimientos."\nmsgstr "Sin movimientos."',
    'msgid "Movimiento de inventario"\nmsgstr "Volver al inventario"': 'msgid "Movimiento de inventario"\nmsgstr "Movimiento de inventario"',
    'msgid "Agregar gasto ahora"\nmsgstr ""': 'msgid "Agregar gasto ahora"\nmsgstr "Agregar gasto ahora"',
    'msgid "Sin gasto para este material"\nmsgstr ""': 'msgid "Sin gasto para este material"\nmsgstr "Sin gasto para este material"',
    'msgid "Guardar"\nmsgstr "Guardar compra"': 'msgid "Guardar"\nmsgstr "Guardar"',
}

for old, new in translations.items():
    content = content.replace(old, new)

# Arreglar la traducción multilinea
multiline_old = '''msgid ""
"Si marcas 'Agregar gasto ahora', al guardar te llevamos al formulario de "
"gastos con el proyecto ya seleccionado."
msgstr ""'''

multiline_new = '''msgid ""
"Si marcas 'Agregar gasto ahora', al guardar te llevamos al formulario de "
"gastos con el proyecto ya seleccionado."
msgstr ""
"Si marcas 'Agregar gasto ahora', al guardar te llevamos al formulario de "
"gastos con el proyecto ya seleccionado."'''

content = content.replace(multiline_old, multiline_new)

# Escribir archivo
with open('locale/es/LC_MESSAGES/django.po', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Archivo django.po (ES) reparado")
