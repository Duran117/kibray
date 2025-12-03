#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para agregar traducciones faltantes del Strategic Planner al español
"""

translations = {
    # Main Title
    "Strategic Ritual": "Ritual Estratégico",
    
    # Phase Names
    "Prime": "Activación",
    "Gratitude": "Gratitud",
    "Habits": "Hábitos",
    "Vision": "Visión",
    "80/20 Sort": "Clasificación 80/20",
    "The Frog": "La Rana",
    
    # Priming Exercise (Step 0)
    "Tony Robbins' Triad: Physiology, Focus, Language": "La Tríada de Tony Robbins: Fisiología, Enfoque, Lenguaje",
    "Priming Exercise": "Ejercicio de Activación",
    "Stand up. Take 3 deep breaths.": "Ponte de pie. Respira profundo 3 veces.",
    "Roll your shoulders back.": "Echa los hombros hacia atrás.",
    "Smile.": "Sonríe.",
    "Your physiology affects your psychology.": "Tu fisiología afecta tu psicología.",
    "I've completed my priming": "He completado mi activación",
    "Current Energy Level:": "Nivel de Energía Actual:",
    
    # Gratitude (Step 1)
    "3 Things I'm Grateful For": "3 Cosas por las que Estoy Agradecido",
    "Gratitude shifts your focus from scarcity to abundance.": "La gratitud cambia tu enfoque de la escasez a la abundancia.",
    "1. I'm grateful for...": "1. Estoy agradecido por...",
    "Example: My health, my family, this opportunity...": "Ejemplo: Mi salud, mi familia, esta oportunidad...",
    "2. I'm grateful for...": "2. Estoy agradecido por...",
    "Example: The roof over my head, my skills...": "Ejemplo: El techo sobre mi cabeza, mis habilidades...",
    "3. I'm grateful for...": "3. Estoy agradecido por...",
    "Example: The challenges that make me stronger...": "Ejemplo: Los desafíos que me hacen más fuerte...",
    "Today's Intention/Focus:": "Intención/Enfoque de Hoy:",
    "Example: Be present, create value, lead with clarity...": "Ejemplo: Estar presente, crear valor, liderar con claridad...",
    
    # Habits (Step 2)
    "Daily Habits Check-In": "Revisión de Hábitos Diarios",
    "Which habits are you committing to today?": "¿A qué hábitos te comprometes hoy?",
    "No habits yet?": "¿Aún no tienes hábitos?",
    "Create your first habit": "Crea tu primer hábito",
    
    # Vision (Step 3)
    "Vision Anchor": "Ancla de Visión",
    "Remember WHY you're doing this. Connect with your deeper purpose.": "Recuerda POR QUÉ haces esto. Conéctate con tu propósito profundo.",
    "No life visions yet?": "¿Aún no tienes visiones de vida?",
    "Create your North Star goals": "Crea tus metas estrella del norte",
    
    # Brain Dump (Step 4)
    "Capture everything, then apply the 80/20 rule": "Captura todo, luego aplica la regla 80/20",
    "Write down everything that's on your mind. Don't filter yet.": "Escribe todo lo que tengas en mente. No filtres todavía.",
    "Everything you think you need to do today...": "Todo lo que crees que necesitas hacer hoy...",
    
    # 80/20 Sort (Step 5)
    "80/20 Sort: What Really Matters?": "Clasificación 80/20: ¿Qué Realmente Importa?",
    "Drag items to the right column if they advance a Life Vision goal.": "Arrastra elementos a la columna derecha si avanzan una meta de Visión de Vida.",
    "The 80/20 Rule: Only 20%% of actions create 80%% of results. Limit yourself to 5 high-impact items.": "La Regla 80/20: Solo el 20%% de las acciones crean el 80%% de los resultados. Limítate a 5 elementos de alto impacto.",
    "Noise / Busy Work": "Ruido / Trabajo Ocupado",
    "High Impact (Max 5)": "Alto Impacto (Máx 5)",
    
    # Choose Frog (Step 6)
    "Eat That Frog - Do the hardest thing first": "Come esa Rana - Haz lo más difícil primero",
    "Choose Your Frog": "Elige Tu Rana",
    "Which ONE high-impact action will you tackle FIRST today?": "¿Qué UNA acción de alto impacto atacarás PRIMERO hoy?",
    
    # Battle Plan (Step 7)
    "Battle Plan for Your Frog": "Plan de Batalla para Tu Rana",
    "Break it down into micro-steps and time-block them.": "Divídelo en micro-pasos y asígnales bloques de tiempo.",
    "Add Micro-Step": "Agregar Micro-Paso",
    "Time Block for Frog:": "Bloque de Tiempo para la Rana:",
    "Start Time:": "Hora de Inicio:",
    "End Time:": "Hora de Fin:",
    
    # Validation Messages
    "No visions yet. Skip this step for now.": "Aún no hay visiones. Omite este paso por ahora.",
    "Maximum 5 high-impact items allowed! Focus on what truly matters.": "¡Máximo 5 elementos de alto impacto permitidos! Concéntrate en lo que realmente importa.",
    "No high-impact items to choose from. Go back and sort your tasks.": "No hay elementos de alto impacto para elegir. Regresa y clasifica tus tareas.",
    "Micro-step description...": "Descripción del micro-paso...",
    
    # Completion
    "Complete Ritual": "Completar Ritual",
    "Ritual completed! Your strategic day is planned.": "¡Ritual completado! Tu día estratégico está planeado.",
    "Error completing ritual. Please try again.": "Error al completar el ritual. Por favor, inténtalo de nuevo.",
    
    # Navigation
    "Previous Step": "Paso Anterior",
    "Next Step": "Siguiente Paso",
    "Back": "Atrás",
    "Continue": "Continuar",
    
    # Dashboard & Quick Actions
    "Strategic Planner": "Planificador Estratégico",
    "Kickstart your day with the Strategic Planner or Focus Wizard": "Inicia tu día con el Planificador Estratégico o el Asistente de Enfoque",
    "Start Daily Ritual": "Iniciar Ritual Diario",
    "View Today's Plan": "Ver Plan de Hoy",
    
    # Related Focus Wizard strings
    "Pareto (80/20) + Eat That Frog Daily Planning": "Planificación Diaria Pareto (80/20) + Come esa Rana",
    "80/20 Filter": "Filtro 80/20",
    "Step 2: The 80/20 Filter": "Paso 2: El Filtro 80/20",
    "Your tasks are now on your calendar. Time to eat that frog!": "¡Tus tareas ahora están en tu calendario. Es hora de comerte esa rana!",
}

def update_po_file():
    """Update the Spanish .po file with translations"""
    po_file_path = "locale/es/LC_MESSAGES/django.po"
    
    try:
        with open(po_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        original_content = content
        updates_made = 0
        
        for english, spanish in translations.items():
            # Escape special characters for regex
            english_escaped = english.replace('"', '\\"').replace('%', '%%')
            
            # Pattern to find msgid followed by empty msgstr
            import re
            
            # Look for the pattern: msgid "text"\nmsgstr ""
            pattern = f'msgid "{re.escape(english_escaped)}"\nmsgstr ""'
            replacement = f'msgid "{english_escaped}"\nmsgstr "{spanish}"'
            
            if pattern in content:
                content = content.replace(pattern, replacement)
                updates_made += 1
                print(f"✓ Updated: {english[:50]}...")
        
        if updates_made > 0:
            with open(po_file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"\n✅ Updated {updates_made} translations in {po_file_path}")
            print("\n🔄 Now run: python manage.py compilemessages")
            return True
        else:
            print("⚠️ No empty translations found to update")
            return False
            
    except FileNotFoundError:
        print(f"❌ File not found: {po_file_path}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Updating Strategic Planner translations to Spanish...\n")
    success = update_po_file()
    
    if success:
        print("\n📋 Summary:")
        print(f"   Total translations defined: {len(translations)}")
        print("   Strategic Planner module now has Spanish translations!")
        print("\n🚀 Next steps:")
        print("   1. python manage.py compilemessages")
        print("   2. Restart server")
        print("   3. Test /strategic-planner/ in Spanish")
