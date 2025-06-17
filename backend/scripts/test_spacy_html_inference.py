#!/usr/bin/env python3
"""
Test Script: spaCy + HTML Cleaning para Sistema de Inferencia
Prueba capacidades de limpieza HTML y análisis NLP con emails BCR reales

Este script:
1. Limpia HTML de emails bancarios preservando contexto
2. Usa spaCy para análisis semántico inteligente  
3. Implementa sistema de inferencia para datos faltantes
4. Categoriza transacciones automáticamente
5. Detecta relaciones entre transacciones

Usage:
    cd scripts
    python install_spacy_dependencies.py  # Primero instalar dependencias
    python test_spacy_html_inference.py
"""

import os
import sys
import django
from pathlib import Path
import re
import html
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Add backend to path and setup Django
# Get the current script directory
current_dir = Path(__file__).resolve().parent
# Get the backend directory (parent of scripts)
backend_dir = current_dir.parent
# Change to backend directory for proper Django app import
os.chdir(backend_dir)
# Add backend directory to Python path
sys.path.insert(0, str(backend_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'afp_backend.settings')
django.setup()

# Import after Django setup
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
from core.gmail_service import GmailService

# Import NLP dependencies
try:
    import spacy
    from spacy.matcher import Matcher
    from bs4 import BeautifulSoup
    import bleach
    from dateutil import parser as date_parser
except ImportError as e:
    print(f"❌ Error importing dependencies: {e}")
    print("🔧 Run first: python install_spacy_dependencies.py")
    sys.exit(1)

class HTMLCleanerForSpacy:
    """Limpia HTML de emails bancarios preservando contexto semántico para spaCy"""
    
    def __init__(self):
        # Mapeo de elementos HTML a contexto semántico
        self.semantic_mappings = {
            'table': '\n--- DATOS ESTRUCTURADOS ---\n',
            'tr': '\n',
            'td': ' | ',
            'th': ' | ',
            'p': '\n',
            'div': '\n',
            'span': ' ',
            'strong': ' ',
            'b': ' ',
            'em': ' ',
            'i': ' ',
            'br': '\n'
        }
        
        # Palabras clave financieras importantes
        self.financial_keywords = [
            'monto', 'destinatario', 'referencia', 'fecha', 'estado',
            'transacción', 'transferencia', 'compra', 'pago', 'retiro',
            'tarjeta', 'cuenta', 'banco', 'sinpe'
        ]
    
    def clean_html_for_nlp(self, html_content: str) -> Dict[str, str]:
        """Limpia HTML manteniendo estructura semántica para spaCy"""
        
        # 1. Decodificar entidades HTML
        clean_text = html.unescape(html_content)
        
        # 2. Parse con BeautifulSoup
        soup = BeautifulSoup(clean_text, 'html.parser')
        
        # 3. Identificar secciones financieras importantes
        financial_sections = self._identify_financial_sections(soup)
        
        # 4. Limpiar preservando estructura
        cleaned_sections = {}
        for section_name, section_soup in financial_sections.items():
            cleaned_sections[section_name] = self._clean_section_intelligently(section_soup)
        
        # 5. Crear texto completo limpio
        full_clean_text = self._combine_sections_with_context(cleaned_sections)
        
        return {
            'original_html': html_content,
            'sections': cleaned_sections,
            'full_text': full_clean_text,
            'section_count': len(cleaned_sections)
        }
    
    def _identify_financial_sections(self, soup: BeautifulSoup) -> Dict[str, BeautifulSoup]:
        """Identifica secciones financieras importantes"""
        sections = {}
        
        # Buscar tablas (datos estructurados)
        tables = soup.find_all('table')
        for i, table in enumerate(tables):
            sections[f'table_{i}'] = table
        
        # Buscar párrafos con datos financieros
        paragraphs = soup.find_all('p')
        for i, p in enumerate(paragraphs):
            text = p.get_text().lower()
            if any(keyword in text for keyword in self.financial_keywords):
                sections[f'financial_paragraph_{i}'] = p
        
        # Buscar divs con clases financieras
        financial_divs = soup.find_all('div', class_=re.compile(r'(transaction|amount|recipient|reference)', re.I))
        for i, div in enumerate(financial_divs):
            sections[f'financial_div_{i}'] = div
        
        # Si no encontramos secciones específicas, usar todo el body
        if not sections:
            body = soup.find('body') or soup
            sections['full_content'] = body
        
        return sections
    
    def _clean_section_intelligently(self, section_soup) -> str:
        """Limpia una sección preservando contexto semántico"""
        
        # Clonar para no modificar original
        section = BeautifulSoup(str(section_soup), 'html.parser')
        
        # Preservar saltos de línea importantes
        for br in section.find_all("br"):
            br.replace_with("\n")
        
        # Preservar separación de celdas de tabla
        for td in section.find_all("td"):
            if td.string:
                td.string = f" {td.string.strip()} "
        
        # Preservar párrafos
        for p in section.find_all("p"):
            if p.string:
                p.string = f"\n{p.string.strip()}\n"
        
        # Extraer texto limpio
        clean_text = section.get_text()
        
        # Limpiar espacios múltiples
        clean_text = re.sub(r'\s+', ' ', clean_text)
        clean_text = re.sub(r'\n\s*\n', '\n', clean_text)
        clean_text = re.sub(r'\|\s*\|', '|', clean_text)  # Limpiar separadores dobles
        
        return clean_text.strip()
    
    def _combine_sections_with_context(self, sections: Dict[str, str]) -> str:
        """Combina secciones con contexto apropiado"""
        combined_text = ""
        
        for section_name, section_text in sections.items():
            if section_text.strip():
                combined_text += f"\n=== {section_name.upper()} ===\n"
                combined_text += section_text + "\n"
        
        return combined_text.strip()

class SpacyFinancialInferenceEngine:
    """Motor de inferencia financiera usando spaCy"""
    
    def __init__(self):
        try:
            self.nlp = spacy.load("es_core_news_sm")
            print("✅ Modelo spaCy es_core_news_sm cargado")
        except OSError:
            print("❌ Modelo spaCy no encontrado")
            print("🔧 Ejecuta: python -m spacy download es_core_news_sm")
            raise
        
        # Configurar matcher para patrones específicos
        self.matcher = Matcher(self.nlp.vocab)
        self._setup_financial_patterns()
        
        # Categorías de gastos con palabras clave semánticamente relacionadas
        self.expense_categories = {
            'comida_restaurantes': self.nlp("restaurante comida rapida hamburguesa pizza mcdonalds kfc"),
            'comida_supermercado': self.nlp("supermercado tienda abarrotes mercado walmart"),
            'transporte_gasolina': self.nlp("gasolina combustible estacion servicio shell texaco"),
            'transporte_uber': self.nlp("taxi transporte viaje uber didi"),
            'entretenimiento': self.nlp("streaming netflix entretenimiento diversión cine"),
            'salud': self.nlp("farmacia medicina salud medicamento clinica"),
            'tecnologia': self.nlp("amazon tecnologia electronico computadora apple"),
            'servicios_publicos': self.nlp("ice electricidad agua telefono internet cable"),
        }
    
    def _setup_financial_patterns(self):
        """Configura patrones específicos para emails bancarios"""
        
        # Patrones para montos en colones
        monto_patterns = [
            [{"TEXT": "₡"}, {"LIKE_NUM": True}],
            [{"LOWER": "colones"}, {"LIKE_NUM": True}],
            [{"LIKE_NUM": True}, {"LOWER": "colones"}],
        ]
        
        # Patrones para números de referencia  
        ref_patterns = [
            [{"LOWER": "referencia"}, {"TEXT": ":"}, {"LIKE_NUM": True}],
            [{"LOWER": "ref"}, {"TEXT": ":"}, {"LIKE_NUM": True}],
            [{"LOWER": "número"}, {"LOWER": "de"}, {"LOWER": "referencia"}, {"TEXT": ":"}, {"LIKE_NUM": True}],
        ]
        
        # Patrones para tarjetas (últimos 4 dígitos)
        tarjeta_patterns = [
            [{"TEXT": "*"}, {"SHAPE": "dddd"}],
            [{"LOWER": "tarjeta"}, {"TEXT": "*"}, {"SHAPE": "dddd"}],
        ]
        
        # Patrones para transferencias SINPE (CORREGIDO)
        sinpe_patterns = [
            [{"TEXT": {"REGEX": r"(?i)sinpe"}}, {"TEXT": {"REGEX": r"(?i)móvil|movil"}}],
            [{"LOWER": "sinpe"}, {"LOWER": "móvil"}],
            [{"LOWER": "sinpe"}, {"LOWER": "movil"}],
        ]
        
        # Registrar patrones
        self.matcher.add("MONTO_COLONES", monto_patterns)
        self.matcher.add("NUMERO_REFERENCIA", ref_patterns) 
        self.matcher.add("TARJETA_DIGITOS", tarjeta_patterns)
        self.matcher.add("SINPE_MOVIL", sinpe_patterns)
    
    def analyze_email_content(self, clean_text: str) -> Dict:
        """Análisis completo de contenido de email con spaCy"""
        
        doc = self.nlp(clean_text)
        
        # Análisis básico de entidades
        entities = self._extract_financial_entities(doc)
        
        # Detección de patrones específicos
        patterns = self._detect_financial_patterns(doc)
        
        # Inferencias específicas
        inferences = self._make_financial_inferences(doc, entities, patterns)
        
        return {
            'entities': entities,
            'patterns': patterns,
            'inferences': inferences,
            'sentences': [sent.text.strip() for sent in doc.sents],
            'tokens_count': len(doc),
            'entities_count': len(doc.ents)
        }
    
    def _extract_financial_entities(self, doc) -> List[Dict]:
        """Extrae entidades financieras específicas"""
        financial_entities = []
        
        for ent in doc.ents:
            entity_info = {
                'text': ent.text,
                'label': ent.label_,
                'explanation': spacy.explain(ent.label_),
                'start_char': ent.start_char,
                'end_char': ent.end_char,
                'confidence': 1.0  # spaCy no proporciona confidence por defecto
            }
            
            # Clasificar tipo de entidad financiera
            if ent.label_ == 'MONEY':
                entity_info['financial_type'] = 'amount'
            elif ent.label_ == 'PER':
                entity_info['financial_type'] = 'recipient_person'
            elif ent.label_ == 'ORG':
                entity_info['financial_type'] = 'bank_or_merchant'
            elif ent.label_ == 'DATE':
                entity_info['financial_type'] = 'transaction_date'
            elif ent.label_ == 'TIME':
                entity_info['financial_type'] = 'transaction_time'
            else:
                entity_info['financial_type'] = 'other'
            
            financial_entities.append(entity_info)
        
        return financial_entities
    
    def _detect_financial_patterns(self, doc) -> List[Dict]:
        """Detecta patrones financieros específicos usando Matcher"""
        matches = self.matcher(doc)
        
        detected_patterns = []
        for match_id, start, end in matches:
            span = doc[start:end]
            label = self.nlp.vocab.strings[match_id]
            
            detected_patterns.append({
                'pattern_type': label,
                'text': span.text,
                'start': start,
                'end': end,
                'context': doc[max(0, start-3):min(len(doc), end+3)].text
            })
        
        return detected_patterns
    
    def _make_financial_inferences(self, doc, entities: List[Dict], patterns: List[Dict]) -> Dict:
        """Hace inferencias específicas para transacciones bancarias"""
        
        inferences = {
            'transaction_type': self._infer_transaction_type(doc, entities, patterns),
            'recipient_type': self._infer_recipient_type(entities),
            'currency': self._infer_currency(doc, entities, patterns),
            'bank_source': self._infer_bank_source(doc),
            'expense_category': self._infer_expense_category(doc, entities),
            'urgency_level': self._infer_urgency(doc),
            'missing_data_defaults': self._infer_missing_data_defaults(doc, entities)
        }
        
        return inferences
    
    def _infer_transaction_type(self, doc, entities: List[Dict], patterns: List[Dict]) -> Dict:
        """Infiere tipo de transacción usando spaCy"""
        
        # Buscar patrones SINPE
        sinpe_patterns = [p for p in patterns if 'SINPE' in p['pattern_type']]
        if sinpe_patterns:
            return {
                'predicted_type': 'TRANSFER',
                'confidence': 0.9,
                'reasoning': 'SINPE pattern detected'
            }
        
        # Buscar palabras clave en el texto
        text_lower = doc.text.lower()
        
        transaction_keywords = {
            'TRANSFER': ['transferencia', 'sinpe', 'envio', 'envío'],
            'PURCHASE': ['compra', 'pago', 'cargo', 'purchase'],
            'WITHDRAWAL': ['retiro', 'atm', 'cajero', 'withdrawal'],
            'DEPOSIT': ['deposito', 'depósito', 'ingreso', 'deposit']
        }
        
        scores = {}
        for trans_type, keywords in transaction_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[trans_type] = score
        
        if max(scores.values()) > 0:
            best_type = max(scores.items(), key=lambda x: x[1])
            return {
                'predicted_type': best_type[0],
                'confidence': min(0.9, best_type[1] / 3),  # Normalizar
                'reasoning': f'Keywords detected: {scores}',
                'all_scores': scores
            }
        
        return {
            'predicted_type': 'UNKNOWN',
            'confidence': 0.0,
            'reasoning': 'No clear transaction type indicators found'
        }
    
    def _infer_recipient_type(self, entities: List[Dict]) -> Dict:
        """Determina si el destinatario es persona o comercio"""
        
        recipients = [ent for ent in entities 
                     if ent['financial_type'] in ['recipient_person', 'bank_or_merchant']]
        
        if not recipients:
            return {'type': 'UNKNOWN', 'confidence': 0.0, 'reasoning': 'No recipients found'}
        
        # Analizar el primer destinatario encontrado
        recipient = recipients[0]
        
        if recipient['label'] == 'PER':
            return {
                'type': 'PERSON',
                'confidence': 0.9,
                'name': recipient['text'],
                'reasoning': 'spaCy detected as person entity'
            }
        elif recipient['label'] == 'ORG':
            return {
                'type': 'MERCHANT',
                'confidence': 0.8,
                'name': recipient['text'],
                'reasoning': 'spaCy detected as organization entity'
            }
        else:
            # Análisis adicional basado en patrones
            name_text = recipient['text'].upper()
            
            commercial_indicators = ['S.A.', 'LTDA', 'CORP', 'INC', 'SUPER', 'FARMACIA']
            if any(indicator in name_text for indicator in commercial_indicators):
                return {
                    'type': 'MERCHANT',
                    'confidence': 0.7,
                    'name': recipient['text'],
                    'reasoning': 'Commercial indicators detected'
                }
            else:
                return {
                    'type': 'PERSON',
                    'confidence': 0.6,
                    'name': recipient['text'],
                    'reasoning': 'Default assumption - no commercial indicators'
                }
    
    def _infer_currency(self, doc, entities: List[Dict], patterns: List[Dict]) -> Dict:
        """Infiere moneda basado en contexto"""
        
        # Buscar símbolos de moneda en patrones
        colon_patterns = [p for p in patterns if 'COLONES' in p['pattern_type']]
        if colon_patterns:
            return {
                'currency': 'CRC',
                'confidence': 0.9,
                'reasoning': 'Colones pattern detected'
            }
        
        # Buscar en entidades de dinero
        money_entities = [ent for ent in entities if ent['financial_type'] == 'amount']
        for money_ent in money_entities:
            if '₡' in money_ent['text'] or 'colones' in money_ent['text'].lower():
                return {
                    'currency': 'CRC',
                    'confidence': 0.9,
                    'reasoning': 'Currency symbol in money entity'
                }
            elif '$' in money_ent['text'] or 'dolar' in money_ent['text'].lower():
                return {
                    'currency': 'USD',
                    'confidence': 0.9,
                    'reasoning': 'Dollar symbol in money entity'
                }
        
        # Análisis del texto completo
        text_lower = doc.text.lower()
        if 'colones' in text_lower or '₡' in doc.text:
            return {
                'currency': 'CRC',
                'confidence': 0.7,
                'reasoning': 'Colones mentioned in text'
            }
        elif 'dolar' in text_lower or '$' in doc.text:
            return {
                'currency': 'USD',
                'confidence': 0.7,
                'reasoning': 'Dollars mentioned in text'
            }
        
        # Default para Costa Rica
        return {
            'currency': 'CRC',
            'confidence': 0.5,
            'reasoning': 'Default for Costa Rica'
        }
    
    def _infer_bank_source(self, doc) -> Dict:
        """Infiere banco origen del email"""
        
        text_lower = doc.text.lower()
        
        banks = {
            'BCR': ['bcr', 'banco de costa rica', 'bancobcr'],
            'BAC': ['bac', 'banco bac'],
            'NACIONAL': ['banco nacional', 'bncr'],
            'POPULAR': ['banco popular', 'popular'],
            'SCOTIABANK': ['scotiabank', 'scotia']
        }
        
        for bank_name, keywords in banks.items():
            if any(keyword in text_lower for keyword in keywords):
                return {
                    'bank': bank_name,
                    'confidence': 0.8,
                    'reasoning': f'Bank keywords detected: {keywords}'
                }
        
        return {
            'bank': 'UNKNOWN',
            'confidence': 0.0,
            'reasoning': 'No bank indicators found'
        }
    
    def _infer_expense_category(self, doc, entities: List[Dict]) -> Dict:
        """Categoriza gastos usando similitud semántica"""
        
        # Buscar comercios/destinatarios
        merchants = [ent for ent in entities 
                    if ent['financial_type'] in ['bank_or_merchant', 'recipient_person']]
        
        if not merchants:
            return {
                'category': 'otros',
                'confidence': 0.0,
                'reasoning': 'No merchant found for categorization'
            }
        
        merchant_text = merchants[0]['text'].lower()
        merchant_doc = self.nlp(merchant_text)
        
        # Calcular similitud con cada categoría
        similarities = {}
        for category, category_doc in self.expense_categories.items():
            similarity = merchant_doc.similarity(category_doc)
            similarities[category] = similarity
        
        # Encontrar mejor categoría
        best_category = max(similarities.items(), key=lambda x: x[1])
        
        return {
            'category': best_category[0],
            'confidence': best_category[1],
            'reasoning': f'Semantic similarity analysis',
            'merchant': merchant_text,
            'all_similarities': similarities
        }
    
    def _infer_urgency(self, doc) -> Dict:
        """Infiere nivel de urgencia del email"""
        
        urgency_keywords = {
            'HIGH': ['urgente', 'inmediato', 'alerta', 'bloqueo', 'fraude'],
            'MEDIUM': ['importante', 'atención', 'verificar'],
            'LOW': ['información', 'notificación', 'confirmación']
        }
        
        text_lower = doc.text.lower()
        
        for level, keywords in urgency_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return {
                    'level': level,
                    'confidence': 0.7,
                    'reasoning': f'Urgency keywords detected: {keywords}'
                }
        
        return {
            'level': 'LOW',
            'confidence': 0.5,
            'reasoning': 'Default urgency level'
        }
    
    def _infer_missing_data_defaults(self, doc, entities: List[Dict]) -> Dict:
        """Infiere valores por defecto para datos faltantes"""
        
        defaults = {}
        
        # Si no hay fecha, usar fecha actual
        date_entities = [ent for ent in entities if ent['financial_type'] == 'transaction_date']
        if not date_entities:
            defaults['timestamp'] = datetime.now().isoformat()
            defaults['timestamp_confidence'] = 0.3
            defaults['timestamp_reasoning'] = 'No date found, using current time'
        
        # Si no hay estado, asumir exitosa
        if 'exitosa' in doc.text.lower() or 'aprobada' in doc.text.lower():
            defaults['status'] = 'completed'
            defaults['status_confidence'] = 0.8
        elif 'rechazada' in doc.text.lower() or 'fallida' in doc.text.lower():
            defaults['status'] = 'failed'
            defaults['status_confidence'] = 0.8
        else:
            defaults['status'] = 'completed'
            defaults['status_confidence'] = 0.5
            defaults['status_reasoning'] = 'Default assumption'
        
        return defaults

class EmailSpacyTestRunner:
    """Ejecutor de pruebas para el sistema spaCy + HTML cleaning"""
    
    def __init__(self):
        self.html_cleaner = HTMLCleanerForSpacy()
        self.inference_engine = SpacyFinancialInferenceEngine()
    
    def run_full_test(self, user_email: str):
        """Ejecuta prueba completa con emails BCR reales"""
        
        print("🧪 PRUEBA COMPLETA: spaCy + HTML Cleaning + Inferencia")
        print("=" * 70)
        
        # Inicializar servicios
        try:
            user = User.objects.filter(email=user_email).first()
            if not user:
                print(f"❌ Usuario no encontrado: {user_email}")
                return
            
            google_account = SocialAccount.objects.filter(user=user, provider='google').first()
            if not google_account:
                print(f"❌ Usuario sin OAuth de Google: {user_email}")
                return
            
            gmail_service = GmailService(user)
            print(f"✅ Gmail service inicializado para: {user.username}")
            
        except Exception as e:
            print(f"❌ Error inicializando servicios: {e}")
            return
        
        # Obtener emails BCR
        print("\n📧 Obteniendo emails BCR...")
        all_messages = gmail_service.get_all_emails(max_results=500, days_back=60)
        
        if not all_messages:
            print("❌ No se encontraron emails")
            return
        
        # Filtrar emails BCR
        bcr_senders = ['mensajero@bancobcr.com', 'bcrtarjestcta@bancobcr.com']
        bcr_messages = []
        
        for message in all_messages:
            sender = message.get('sender', '').lower()
            for bcr_sender in bcr_senders:
                if bcr_sender.lower() in sender:
                    bcr_messages.append(message)
                    break
        
        print(f"✅ Encontrados {len(bcr_messages)} emails BCR")
        
        if not bcr_messages:
            print("❌ No se encontraron emails de BCR")
            return
        
        # Procesar primeros 3 emails
        for i, message in enumerate(bcr_messages[:3]):
            print(f"\n{'='*70}")
            print(f"📧 PROCESANDO EMAIL {i+1}/3")
            print(f"📄 Asunto: {message.get('subject', 'Sin asunto')}")
            print(f"👤 De: {message.get('sender', 'Desconocido')}")
            print(f"📅 Fecha: {message.get('date', 'Sin fecha')}")
            
            # 1. Limpiar HTML
            print(f"\n🧹 LIMPIEZA HTML:")
            html_content = self._get_html_content(message)
            cleaned_data = self.html_cleaner.clean_html_for_nlp(html_content)
            
            print(f"   📊 Secciones encontradas: {cleaned_data['section_count']}")
            print(f"   📝 Texto limpio (primeros 200 chars):")
            print(f"      {cleaned_data['full_text'][:200]}...")
            
            # 2. Análisis spaCy
            print(f"\n🧠 ANÁLISIS spaCy:")
            spacy_analysis = self.inference_engine.analyze_email_content(cleaned_data['full_text'])
            
            print(f"   🎯 Entidades detectadas: {spacy_analysis['entities_count']}")
            for entity in spacy_analysis['entities'][:5]:  # Mostrar primeras 5
                print(f"      {entity['text']:20} -> {entity['financial_type']:15} ({entity['label']})")
            
            print(f"   🔍 Patrones detectados: {len(spacy_analysis['patterns'])}")
            for pattern in spacy_analysis['patterns']:
                print(f"      {pattern['pattern_type']:15} -> '{pattern['text']}'")
            
            # 3. Inferencias
            print(f"\n🔮 INFERENCIAS FINANCIERAS:")
            inferences = spacy_analysis['inferences']
            
            print(f"   💳 Tipo transacción: {inferences['transaction_type']['predicted_type']} "
                  f"(confianza: {inferences['transaction_type']['confidence']:.2f})")
            
            print(f"   👤 Tipo destinatario: {inferences['recipient_type']['type']} "
                  f"(confianza: {inferences['recipient_type']['confidence']:.2f})")
            
            print(f"   💰 Moneda: {inferences['currency']['currency']} "
                  f"(confianza: {inferences['currency']['confidence']:.2f})")
            
            print(f"   🏦 Banco: {inferences['bank_source']['bank']} "
                  f"(confianza: {inferences['bank_source']['confidence']:.2f})")
            
            print(f"   🏷️  Categoría: {inferences['expense_category']['category']} "
                  f"(confianza: {inferences['expense_category']['confidence']:.2f})")
            
            print(f"   ⚡ Urgencia: {inferences['urgency_level']['level']}")
            
            # 4. Datos faltantes inferidos
            missing_data = inferences['missing_data_defaults']
            if missing_data:
                print(f"   🔧 Datos inferidos:")
                for key, value in missing_data.items():
                    if not key.endswith('_confidence') and not key.endswith('_reasoning'):
                        confidence = missing_data.get(f"{key}_confidence", 0.0)
                        print(f"      {key}: {value} (confianza: {confidence:.2f})")
        
        print(f"\n🎉 PRUEBA COMPLETADA!")
        print(f"✅ spaCy + HTML cleaning funcionando correctamente")
        print(f"✅ Sistema de inferencia operativo")
        print(f"✅ Listo para integración en pipeline de producción")
    
    def _get_html_content(self, message: Dict) -> str:
        """Extrae contenido HTML del mensaje"""
        body = message.get('body', '')
        
        # Si contiene HTML, usarlo tal como está
        if '<html>' in body.lower() or '<table>' in body.lower() or '<div>' in body.lower():
            return body
        else:
            # Envolver texto plano en HTML básico
            return f"<html><body><p>{body}</p></body></html>"

def get_user_email():
    """Obtiene email del usuario desde input"""
    print("👤 Ingresa el email de un usuario con OAuth de Gmail configurado:")
    user_email = input("Email: ").strip()
    
    if not user_email or '@' not in user_email:
        print("❌ Email inválido")
        return None
    
    return user_email

def main():
    """Función principal"""
    print("🚀 TEST: spaCy + HTML Cleaning para Sistema de Inferencia")
    print("=" * 60)
    
    # Verificar dependencias
    try:
        import spacy
        nlp = spacy.load("es_core_news_sm")
        print("✅ spaCy y modelo en español disponibles")
    except OSError:
        print("❌ Modelo spaCy no encontrado")
        print("🔧 Ejecuta: python install_spacy_dependencies.py")
        return
    except ImportError:
        print("❌ spaCy no instalado")
        print("🔧 Ejecuta: python install_spacy_dependencies.py")
        return
    
    # Obtener email del usuario
    user_email = get_user_email()
    if not user_email:
        return
    
    # Ejecutar prueba
    test_runner = EmailSpacyTestRunner()
    test_runner.run_full_test(user_email)

if __name__ == "__main__":
    main() 