#!/usr/bin/env python
# Script para agregar traducciones en inglés
import re

# Leer archivo
with open('locale/en/LC_MESSAGES/django.po', 'r', encoding='utf-8') as f:
    content = f.read()

# Agregar traducciones faltantes en inglés
translations = {
    'msgid "Historial de movimientos"\nmsgstr "Register movement"': 'msgid "Historial de movimientos"\nmsgstr "Movement history"',
    'msgid "Volver"\nmsgstr ""': 'msgid "Volver"\nmsgstr "Back"',
    'msgid "Todos los items"\nmsgstr ""': 'msgid "Todos los items"\nmsgstr "All items"',
    'msgid "Todos los tipos"\nmsgstr ""': 'msgid "Todos los tipos"\nmsgstr "All types"',
    'msgid "Entrada compra"\nmsgstr ""': 'msgid "Entrada compra"\nmsgstr "Purchase entry"',
    'msgid "Salida a uso"\nmsgstr ""': 'msgid "Salida a uso"\nmsgstr "Issue to use"',
    'msgid "Traslado"\nmsgstr ""': 'msgid "Traslado"\nmsgstr "Transfer"',
    'msgid "Regreso a storage"\nmsgstr ""': 'msgid "Regreso a storage"\nmsgstr "Return to storage"',
    'msgid "Ajuste"\nmsgstr ""': 'msgid "Ajuste"\nmsgstr "Adjustment"',
    'msgid "Consumo"\nmsgstr ""': 'msgid "Consumo"\nmsgstr "Consumption"',
    'msgid "Filtrar"\nmsgstr ""': 'msgid "Filtrar"\nmsgstr "Filter"',
    'msgid "Fecha"\nmsgstr ""': 'msgid "Fecha"\nmsgstr "Date"',
    'msgid "Tipo"\nmsgstr ""': 'msgid "Tipo"\nmsgstr "Type"',
    'msgid "Cant"\nmsgstr "Quantity"': 'msgid "Cant"\nmsgstr "Qty"',
    'msgid "Desde"\nmsgstr ""': 'msgid "Desde"\nmsgstr "From"',
    'msgid "Hacia"\nmsgstr ""': 'msgid "Hacia"\nmsgstr "To"',
    'msgid "Por"\nmsgstr ""': 'msgid "Por"\nmsgstr "By"',
    'msgid "Nota"\nmsgstr "Notes"': 'msgid "Nota"\nmsgstr "Note"',
    'msgid "Sin movimientos."\nmsgstr "Register movement"': 'msgid "Sin movimientos."\nmsgstr "No movements."',
    'msgid "Movimiento de inventario"\nmsgstr "Back to inventory"': 'msgid "Movimiento de inventario"\nmsgstr "Inventory movement"',
    'msgid "Agregar gasto ahora"\nmsgstr ""': 'msgid "Agregar gasto ahora"\nmsgstr "Add expense now"',
    'msgid "Sin gasto para este material"\nmsgstr ""': 'msgid "Sin gasto para este material"\nmsgstr "No expense for this material"',
    'msgid "Guardar"\nmsgstr "Save purchase"': 'msgid "Guardar"\nmsgstr "Save"',
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
"If you check 'Add expense now', upon saving we'll take you to the expense "
"form with the project already selected."'''

content = content.replace(multiline_old, multiline_new)

# Escribir archivo
with open('locale/en/LC_MESSAGES/django.po', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Archivo django.po (EN) actualizado")
