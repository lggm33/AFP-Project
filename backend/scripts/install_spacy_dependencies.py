#!/usr/bin/env python3
"""
Script para instalar dependencias necesarias para spaCy + HTML cleaning
"""

import subprocess
import sys
import os

def install_package(package):
    """Instala un paquete usando pip"""
    try:
        print(f"📦 Instalando {package}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print(f"✅ {package} instalado exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando {package}: {e}")
        return False

def download_spacy_model():
    """Descarga el modelo de spaCy en español"""
    try:
        print("🧠 Descargando modelo de spaCy en español...")
        subprocess.check_call([sys.executable, '-m', 'spacy', 'download', 'es_core_news_sm'])
        print("✅ Modelo es_core_news_sm descargado exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error descargando modelo de spaCy: {e}")
        print("💡 Intenta manualmente: python -m spacy download es_core_news_sm")
        return False

def main():
    """Función principal de instalación"""
    print("🚀 INSTALACIÓN DE DEPENDENCIAS SPACY + HTML CLEANING")
    print("=" * 60)
    
    # Lista de dependencias necesarias
    dependencies = [
        'spacy>=3.7.0',           # spaCy core
        'beautifulsoup4>=4.12.0', # HTML parsing
        'lxml>=4.9.0',            # XML/HTML parser (más rápido)
        'html5lib>=1.1',          # HTML5 parser
        'bleach>=6.0.0',          # HTML sanitization
        'python-dateutil>=2.8.0', # Date parsing
        'regex>=2023.0.0',        # Advanced regex support
    ]
    
    print("📋 Dependencias a instalar:")
    for dep in dependencies:
        print(f"   - {dep}")
    
    print("\n🔧 Iniciando instalación...")
    
    # Instalar dependencias
    failed_packages = []
    for package in dependencies:
        if not install_package(package):
            failed_packages.append(package)
    
    # Descargar modelo de spaCy
    if 'spacy' not in [pkg.split('>=')[0] for pkg in failed_packages]:
        if not download_spacy_model():
            failed_packages.append('es_core_news_sm')
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE INSTALACIÓN:")
    
    if not failed_packages:
        print("🎉 ¡Todas las dependencias instaladas exitosamente!")
        print("\n✅ Listo para usar:")
        print("   - spaCy con modelo en español")
        print("   - BeautifulSoup para parsing HTML")
        print("   - Herramientas de limpieza y sanitización")
        print("\n🚀 Puedes ejecutar ahora:")
        print("   python test_spacy_html_inference.py")
    else:
        print(f"⚠️  {len(failed_packages)} dependencias fallaron:")
        for pkg in failed_packages:
            print(f"   ❌ {pkg}")
        print("\n💡 Intenta instalar manualmente:")
        for pkg in failed_packages:
            print(f"   pip install {pkg}")

if __name__ == "__main__":
    main() 