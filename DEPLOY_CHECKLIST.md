# Checklist de Deploy - Suite Business

**Versión:** 1.0  
**Última actualización:** 2026-01-09

Este checklist debe seguirse en orden para desplegar Suite Business en producción.

---

## 📋 PRE-DEPLOY

### 1. Verificar código
- [ ] `python manage.py check --deploy` pasa sin errores críticos
- [ ] Todas las migraciones están creadas
- [ ] No hay código de debug activo
- [ ] No hay prints o console.logs visibles
- [ ] Tests pasan (si existen)

### 2. Variables de entorno necesarias

Crear archivo `.env` en el servidor con:

```bash
# Entorno
DJANGO_ENV=production
DEBUG=False

# Seguridad
SECRET_KEY=<generar con: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# Base de datos
DATABASE_URL=postgresql://usuario:password@host:puerto/nombre_db

# Email (opcional pero recomendado)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-password-app
DEFAULT_FROM_EMAIL=noreply@tu-dominio.com

# SSL (si usas HTTPS)
SECURE_SSL_REDIRECT=True
```

### 3. Preparar servidor
- [ ] Python 3.10+ instalado
- [ ] PostgreSQL instalado y corriendo (o base de datos elegida)
- [ ] Servidor web configurado (Nginx, Apache, etc.)
- [ ] Certificado SSL configurado (si usas HTTPS)
- [ ] Usuario del sistema creado (no root)

---

## 🚀 DEPLOY

### 1. Clonar/actualizar código
```bash
cd /ruta/del/proyecto
git pull origin main  # o tu rama de producción
```

### 2. Activar entorno virtual
```bash
source venv/bin/activate
```

### 3. Instalar/actualizar dependencias
```bash
pip install -r requirements/production.txt
```

### 4. Configurar variables de entorno
```bash
# Copiar .env.example a .env y completar
cp .env.example .env
nano .env  # Editar con valores reales
```

### 5. Ejecutar migraciones
```bash
python manage.py migrate
```

**⚠️ IMPORTANTE:** Si hay migraciones que modifican datos, hacer backup primero:
```bash
# Backup de base de datos
pg_dump nombre_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 6. Recolectar archivos estáticos
```bash
python manage.py collectstatic --noinput
```

### 7. Crear directorio de logs
```bash
mkdir -p logs
chmod 755 logs
```

### 8. Verificar permisos
```bash
# Archivos estáticos
chmod -R 755 staticfiles/

# Media (si aplica)
chmod -R 755 media/

# Logs
chmod -R 755 logs/
```

### 9. Reiniciar servidor de aplicación
```bash
# Si usas Gunicorn
sudo systemctl restart gunicorn

# Si usas uWSGI
sudo systemctl restart uwsgi

# O el método que uses
```

### 10. Verificar servidor web
```bash
# Si usas Nginx
sudo nginx -t
sudo systemctl restart nginx

# Si usas Apache
sudo apache2ctl configtest
sudo systemctl restart apache2
```

---

## ✅ POST-DEPLOY

### 1. Verificaciones básicas
- [ ] La aplicación carga sin errores
- [ ] Login funciona
- [ ] Dashboard carga correctamente
- [ ] Archivos estáticos se cargan (CSS, JS, imágenes)
- [ ] No hay errores 500 en logs

### 2. Verificaciones de seguridad
- [ ] HTTPS funciona (si configurado)
- [ ] Cookies seguras activas (inspeccionar en navegador)
- [ ] Headers de seguridad presentes
- [ ] No se muestran tracebacks de errores

### 3. Verificaciones funcionales
- [ ] Crear empresa funciona
- [ ] Crear usuario funciona
- [ ] Login funciona
- [ ] Dashboard muestra datos
- [ ] Operaciones se pueden crear
- [ ] Reportes funcionan

### 4. Monitoreo
- [ ] Logs se están escribiendo correctamente
- [ ] No hay errores críticos en logs
- [ ] Performance es aceptable

---

## 🔄 ROLLBACK (si algo sale mal)

### 1. Detener servidor
```bash
sudo systemctl stop gunicorn  # o tu servidor
```

### 2. Restaurar código
```bash
git checkout <commit-anterior>
```

### 3. Restaurar base de datos (si aplica)
```bash
psql nombre_db < backup_YYYYMMDD_HHMMSS.sql
```

### 4. Recolectar estáticos
```bash
python manage.py collectstatic --noinput
```

### 5. Reiniciar servidor
```bash
sudo systemctl start gunicorn
```

---

## 📝 NOTAS IMPORTANTES

### Migraciones críticas
Si una migración modifica datos importantes:
1. Hacer backup completo
2. Probar en staging primero
3. Ejecutar en horario de bajo tráfico
4. Tener plan de rollback listo

### Variables sensibles
- **NUNCA** commitear `.env` al repositorio
- **NUNCA** compartir `SECRET_KEY` públicamente
- Rotar `SECRET_KEY` periódicamente

### Performance
- Monitorear uso de memoria
- Monitorear queries lentas
- Configurar cache si es necesario

### Backup
- Configurar backups automáticos de base de datos
- Guardar backups en lugar seguro
- Probar restauración periódicamente

---

## 🆘 TROUBLESHOOTING

### Error: "No module named 'X'"
```bash
pip install -r requirements/production.txt
```

### Error: "Database connection failed"
- Verificar `DATABASE_URL` en `.env`
- Verificar que PostgreSQL esté corriendo
- Verificar permisos de usuario de base de datos

### Error: "Static files not found"
```bash
python manage.py collectstatic --noinput
# Verificar que STATIC_ROOT esté configurado
# Verificar permisos de staticfiles/
```

### Error: "Permission denied"
```bash
# Verificar permisos de archivos y directorios
chmod -R 755 staticfiles/ media/ logs/
```

### Error: "SECRET_KEY not set"
- Verificar que `.env` existe
- Verificar que `SECRET_KEY` está en `.env`
- Verificar que `DJANGO_ENV=production`

---

## 📞 CONTACTO

Si algo no funciona después de seguir este checklist:
1. Revisar logs en `logs/django.log` y `logs/security.log`
2. Verificar configuración de servidor web
3. Verificar variables de entorno
4. Contactar al equipo técnico

---

**Última revisión:** 2026-01-09  
**Próxima revisión:** Después de cada deploy importante

