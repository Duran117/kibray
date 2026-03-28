"""
One-time script to rename Spanish chat channels to English.
Run with: python manage.py shell < rename_chat_channels.py
"""
from core.models import ChatChannel

# Update Grupo -> Group
updated_grupo = ChatChannel.objects.filter(name="Grupo").update(name="Group")
print(f"Updated {updated_grupo} 'Grupo' channels to 'Group'")

# Update Directo -> Direct
updated_directo = ChatChannel.objects.filter(name="Directo").update(name="Direct")
print(f"Updated {updated_directo} 'Directo' channels to 'Direct'")

print("Done!")
