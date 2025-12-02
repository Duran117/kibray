#!/bin/bash
# Script to create Django superuser in Railway deployment

echo "Creating Django superuser in Railway..."
echo "You'll need to run this command in Railway CLI:"
echo ""
echo "railway run python manage.py createsuperuser"
echo ""
echo "Or use the Railway dashboard to run shell commands."
echo ""
echo "Alternatively, you can set up environment variables and use:"
echo "railway run python manage.py createsuperuser --noinput --username admin --email admin@kibray.com"
echo ""
echo "Then set the password with:"
echo "railway run python manage.py shell -c \"from django.contrib.auth import get_user_model; User = get_user_model(); u = User.objects.get(username='admin'); u.set_password('YourSecurePassword'); u.save()\""
