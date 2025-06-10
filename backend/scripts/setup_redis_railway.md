# 🔴 Configuración de Redis en Railway para AFP Project

## 📋 PASO 1: Crear Redis Instance en Railway

### **En Railway Dashboard:**
1. Ve a tu proyecto AFP existente en Railway
2. Presiona `Cmd+K` (Mac) o `Ctrl+K` (Windows/Linux)
3. Busca "Redis" en el menú
4. Selecciona "Add Redis"
5. Railway desplegará automáticamente Redis usando `bitnami/redis:7.2.5`

### **Variables de Entorno Automáticas:**
Railway creará estas variables automáticamente:
```bash
REDISHOST=containers-us-west-xxx.railway.app
REDISUSER=default
REDISPORT=6379
REDISPASSWORD=tu_password_generado
REDIS_URL=redis://default:tu_password@containers-us-west-xxx.railway.app:6379
```

## 📋 PASO 2: Conectar Redis a tu Backend Django

### **1. Actualizar Settings de Django:**
```python
# backend/afp_backend/settings.py

# Redis Configuration for Celery
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Celery Configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# Cache Configuration (Opcional - para performance)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session Backend (Opcional - para sesiones)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

### **2. Variables de Entorno en Railway:**
En tu servicio Django en Railway, ve a Variables y agrega:
```bash
# Railway conectará automáticamente estas variables desde tu Redis service
REDIS_URL=${REDIS.REDIS_URL}
```

### **3. Opcional - Cache Dependencies:**
Si quieres usar Redis para cache también:
```bash
# En requirements.txt
django-redis==5.4.0
```

## 📋 PASO 3: Testing Local vs Railway

### **Desarrollo Local:**
```python
# settings.py - Development
if DEBUG:
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
else:
    # Railway/Production
    CELERY_BROKER_URL = os.environ.get('REDIS_URL')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')
```

### **Para Testing Local (si quieres):**
```bash
# Instalar Redis localmente (opcional)
# Mac:
brew install redis
brew services start redis

# Ubuntu:
sudo apt install redis-server
sudo systemctl start redis

# Docker (recomendado):
docker run -d -p 6379:6379 redis:7.2.5
```

## 📋 PASO 4: Verificar Conexión

### **Script de Testing:**
```python
# scripts/test_redis_connection.py
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afp_backend.settings')
django.setup()

def test_redis_connection():
    import redis
    from django.core.cache import cache
    
    print("🔴 Testing Redis Connection...")
    
    try:
        # Test direct Redis connection
        redis_client = redis.from_url(settings.CELERY_BROKER_URL)
        redis_client.ping()
        print("✅ Direct Redis connection: SUCCESS")
        
        # Test Django cache
        cache.set('test_key', 'AFP Project Test', 30)
        result = cache.get('test_key')
        print(f"✅ Django Redis cache: {result}")
        
        # Test Celery connection
        from celery import current_app
        inspector = current_app.control.inspect()
        print("✅ Celery Redis broker: CONNECTED")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

if __name__ == "__main__":
    test_redis_connection()
```

## 📋 PASO 5: Monitoreo en Railway

### **Railway Dashboard:**
- Ve a tu Redis service
- Pestaña "Metrics": CPU, Memory, Network usage
- Pestaña "Logs": Ver logs de Redis
- Pestaña "Variables": Ver conexión details

### **Redis Commands para Debug:**
```bash
# Conectarse desde Railway console (si habilitado)
redis-cli -h $REDISHOST -p $REDISPORT -a $REDISPASSWORD

# Ver todas las keys
KEYS *

# Ver info del servidor
INFO

# Ver memoria usage
MEMORY USAGE

# Limpiar base de datos (¡CUIDADO!)
FLUSHDB
```

## 🚀 ARQUITECTURA FINAL

```mermaid
graph TD
    A[Django Backend] --> B[Redis on Railway]
    B --> C[Celery Workers]
    C --> D[Email Processing]
    C --> E[Bank Templates]
    C --> F[User Feedback]
    
    B --> G[Session Cache]
    B --> H[Template Cache]
    B --> I[API Response Cache]
```

## 📊 COSTOS RAILWAY

### **Redis Pricing:**
- **Starter**: $5/mes - 256MB RAM, ideal para desarrollo
- **Pro**: $20/mes - 1GB RAM, mejor para producción
- **Enterprise**: Contactar - Multi-GB RAM

### **Usage-Based Components:**
- CPU Time: ~$0.01/hour active usage
- Network: ~$0.10/GB outbound
- Storage: Incluido en plan base

### **Estimación AFP Project:**
- Redis Starter: $5/mes
- Django Backend: ~$7-15/mes (usage-based)
- **Total estimado: ~$12-20/mes** vs $340/mes en Render

## ⚠️ CONSIDERACIONES IMPORTANTES

### **Seguridad:**
- Railway Redis viene con authentication por defecto
- Conexiones internas son privadas (no expuestas públicamente)
- Usar REDIS_URL completa con password

### **Performance:**
- Redis in-memory = súper rápido para queues
- Persistencia habilitada por defecto
- Máximo 16 databases por Redis instance

### **Limitaciones:**
- Redis Starter: 256MB RAM limit
- Para 1000+ usuarios concurrentes, considerar Pro plan
- Backup manual (Railway no incluye auto-backup)

## 🎯 SIGUIENTE PASO

Una vez tengas Redis funcionando:
1. Configurar Celery Workers específicos
2. Implementar Gmail API integration  
3. Crear primeros templates de bancos
4. Setup user feedback loops

¿Todo claro? ¿Procedemos a configurar Redis en Railway? 