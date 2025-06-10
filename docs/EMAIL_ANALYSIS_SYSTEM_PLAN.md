# 🚀 SMART EMAIL PROCESSING SYSTEM - PLAN DE IMPLEMENTACIÓN

## 📋 **RESUMEN EJECUTIVO**

Sistema inteligente de procesamiento de emails bancarios que utiliza múltiples estrategias (Regex, HTML Parsing, LLM) para extraer transacciones con alta precisión y eficiencia de costos.

**Objetivo**: 90%+ accuracy, <$0.02 promedio por email, procesamiento en tiempo real

---

## 🏗️ **ARQUITECTURA DEL SISTEMA**

### **Core Pipeline Architecture**

```python
class SmartEmailProcessor:
    """
    Multi-tier processing engine que decide la estrategia óptima
    basado en el contexto del email y banco
    """
    
    def process_email(self, email_data) -> ProcessingResult:
        # Phase 1: Email Classification
        classification = self.classify_email(email_data)
        
        # Phase 2: Strategy Selection
        strategy = self.select_processing_strategy(classification)
        
        # Phase 3: Data Extraction
        result = strategy.extract(email_data)
        
        # Phase 4: Validation & Learning
        validated_result = self.validate_and_learn(result, email_data)
        
        return validated_result
```

### **🎯 Multi-Tier Processing Strategies**

| Tier | Use Case | Strategy | Accuracy | Speed | Cost |
|------|----------|----------|----------|-------|------|
| **Tier 1** | Known Bank + Known Template | Regex optimizado | 95% | <100ms | $0 |
| **Tier 2** | Known Bank + Unknown Template | HTML Structure + Regex | 88% | <500ms | <$0.01 |
| **Tier 3** | Unknown Bank + Transaction Likely | LLM-assisted Regex Generation | 85% | <2s | <$0.05 |
| **Tier 4** | Discovery Mode | Full LLM Structured Extraction | 80% | <5s | <$0.10 |

---

## 🔧 **COMPONENTES DEL SISTEMA**

### **1. Email Classification Engine**

**Responsabilidad**: Determinar qué sabemos sobre cada email

```python
class EmailClassificationEngine:
    """Determina banco, template y probabilidad de transacción"""
    
    def classify_email(self, email) -> EmailClassification:
        return EmailClassification(
            bank_id=self.identify_bank(email),
            bank_confidence=self.calculate_bank_confidence(email),
            template_candidates=self.find_template_matches(email),
            template_confidence=self.calculate_template_confidence(email),
            transaction_likelihood=self.calculate_transaction_probability(email),
            processing_priority=self.calculate_priority(email)
        )
    
    def identify_bank(self, email):
        # Multi-step bank identification
        sender_match = self.match_by_sender(email.sender)
        domain_match = self.match_by_domain(email.sender)
        content_match = self.match_by_content_signatures(email.body)
        
        return self.consolidate_bank_matches([sender_match, domain_match, content_match])
```

**Features**:
- ✅ Identification por sender/domain
- ✅ Content signature matching
- ✅ Confidence scoring
- ✅ Priority queue management

### **2. Secure Template Management System**

**Responsabilidad**: Crear, actualizar y gestionar templates de extracción de forma SEGURA

```python
class SecureTemplateManager:
    """Maneja creación segura de templates - NO EJECUTA CÓDIGO LLM"""
    
    def find_or_create_template(self, email, bank) -> Template:
        # Try existing templates first
        existing_templates = self.find_matching_templates(email, bank)
        
        if existing_templates:
            best_template = self.score_and_select_best(existing_templates, email)
            if best_template.confidence > 0.8:
                return best_template
        
        # Generate new template SECURELY
        return self.generate_secure_template(email, bank)
    
    def generate_secure_template(self, email, bank) -> Template:
        # LLM generates CONFIGURATION, not executable code
        template_config = self.llm_generate_parsing_config(email, bank)
        
        # WE create the safe parser based on LLM configuration
        safe_parser = self.create_safe_parser_from_config(template_config)
        
        # Validate parser with test data
        validation_score = self.validate_parser_safely(safe_parser, email)
        
        if validation_score > 0.7:
            template = self.create_template_from_parser(safe_parser, bank)
            self.queue_for_human_review(template)  # Security review
            return template
        else:
            # Fallback to regex-only approach
            return self.create_regex_fallback_template(email, bank)
    
    def llm_generate_parsing_config(self, email, bank):
        """LLM generates CSS selectors and patterns, NOT Python code"""
        prompt = f"""
        Analyze this {bank.name} email HTML structure and return ONLY CSS selectors:
        
        HTML: {email.html[:2000]}
        
        Return JSON with CSS selectors:
        {{
            "amount_selector": "css_selector_for_amount",
            "merchant_selector": "css_selector_for_merchant", 
            "date_selector": "css_selector_for_date",
            "reference_selector": "css_selector_for_reference",
            "validation_patterns": {{
                "amount_regex": "regex_for_amount_validation",
                "date_format": "expected_date_format"
            }}
        }}
        """
        
        return self.llm_client.structured_json_response(prompt)
    
    def create_safe_parser_from_config(self, config):
        """Create controlled parser from LLM config - WE control execution"""
        def secure_parser(html_content):
            soup = BeautifulSoup(html_content, 'html.parser')
            result = {}
            
            # Safely use LLM-provided selectors
            try:
                amount_elem = soup.select_one(config.get('amount_selector', ''))
                if amount_elem:
                    result['amount'] = self.safe_extract_amount(amount_elem.get_text())
                
                merchant_elem = soup.select_one(config.get('merchant_selector', ''))
                if merchant_elem:
                    result['merchant'] = self.safe_extract_text(merchant_elem.get_text())
                
                date_elem = soup.select_one(config.get('date_selector', ''))
                if date_elem:
                    result['date'] = self.safe_extract_date(date_elem.get_text())
                
            except Exception as e:
                # Log error but don't crash
                result['parsing_error'] = str(e)
                result['confidence'] = 0.0
                
            return result
        
        return secure_parser
```

**Security Features**:
- ✅ LLM generates CONFIGURATION only, never executable code
- ✅ Static CSS selector validation before execution
- ✅ Sandboxed parsing with controlled BeautifulSoup execution
- ✅ Comprehensive error handling and logging
- ✅ Human security review for all LLM-generated templates
- ✅ No dynamic code execution or eval() functions

### **3. Multi-Strategy Extraction Engine**

#### **Tier 1: High-Confidence Regex Strategy**
```python
class Tier1RegexStrategy:
    """Para bancos y templates conocidos (ej: BCR)"""
    
    def extract(self, email_data):
        template = self.get_proven_template(email_data.bank, email_data.subject)
        
        result = RegexExtractor(template).extract(email_data.body)
        result.confidence = 0.95  # High confidence for known templates
        result.processing_time = 50  # ms
        result.cost = 0  # No API calls
        
        return result
```

#### **Tier 2: LLM-Assisted HTML Structure + Regex Hybrid**
```python
class Tier2SecureHybridStrategy:
    """Para bancos conocidos con templates nuevos - SECURE IMPLEMENTATION"""
    
    def extract(self, email_data):
        # 1. Get or generate secure HTML parsing config
        parsing_config = self.get_or_generate_html_config(email_data.bank, email_data)
        
        # 2. Execute SECURE HTML extraction using our controlled parser
        html_result = self.secure_html_extractor.extract(email_data.html, parsing_config)
        
        if html_result.confidence > 0.8:
            return html_result
        
        # 3. Fallback to regex with template fuzzy matching
        fuzzy_template = self.find_similar_template(email_data)
        regex_result = RegexExtractor(fuzzy_template).extract(email_data.body)
        
        return self.combine_results(html_result, regex_result)
```

#### **Tier 3: LLM-Assisted Strategy**
```python
class Tier3LLMAssistedStrategy:
    """Para bancos desconocidos con alta probabilidad de transacción"""
    
    def extract(self, email_data):
        # Use LLM to understand structure first
        structure_analysis = self.llm_analyze_structure(email_data.body)
        
        # Generate targeted regex based on structure
        targeted_regex = self.generate_targeted_regex(structure_analysis)
        
        # Extract with generated regex
        result = RegexExtractor(targeted_regex).extract(email_data.body)
        result.cost = 0.01  # Small LLM call
        
        return result
```

#### **Tier 4: Full LLM Strategy**
```python
class Tier4FullLLMStrategy:
    """Discovery mode para casos completamente desconocidos"""
    
    def extract(self, email_data):
        # Direct structured extraction with LLM
        extraction_prompt = self.build_extraction_prompt(email_data)
        
        llm_result = OpenAIExtractor().structured_extract(
            prompt=extraction_prompt,
            email_content=email_data.body
        )
        
        llm_result.cost = 0.05  # Full LLM call
        llm_result.queue_for_template_generation = True
        
        return llm_result
```

### **4. Validation & Learning System**

```python
class ValidationEngine:
    """Valida resultados y aprende de errores"""
    
    def validate_and_learn(self, result, email_data):
        # Automatic validation rules
        auto_validation = self.run_business_rules(result)
        
        # Statistical validation (outlier detection)
        statistical_validation = self.statistical_validation(result, email_data.bank)
        
        # Cross-validation with similar transactions
        similarity_validation = self.validate_against_similar(result)
        
        final_result = self.consolidate_validations([
            auto_validation, 
            statistical_validation, 
            similarity_validation
        ])
        
        # Learning feedback loop
        if final_result.confidence < 0.8:
            self.queue_for_human_review(final_result, email_data)
        
        if final_result.confidence > 0.9:
            self.reinforce_template(result.template_used, email_data)
        
        return final_result
```

**Validation Rules**:
- ✅ Business logic validation (amounts, dates, formats)
- ✅ Statistical outlier detection
- ✅ Cross-validation with historical data
- ✅ Human review queue for low confidence
- ✅ Template reinforcement learning

### **5. Performance & Cost Monitoring**

```python
class ProcessingMetrics:
    """Monitorea performance, costos y accuracy del sistema"""
    
    def track_processing_result(self, result, email_data):
        metrics = {
            'strategy_used': result.strategy.__class__.__name__,
            'processing_time_ms': result.processing_time,
            'confidence_score': result.confidence,
            'api_cost': result.cost,
            'bank': email_data.bank,
            'success': result.success,
            'needs_review': result.needs_human_review
        }
        
        # Store metrics for optimization
        ProcessingMetric.objects.create(**metrics)
        
        # Real-time dashboard updates
        self.update_dashboard_metrics(metrics)
```

---

## 📅 **ROADMAP DE IMPLEMENTACIÓN**

### **Phase 1: Core Pipeline (Semana 1-2)**
**Objetivo**: Sistema básico funcionando con BCR

**Deliverables**:
- [ ] `EmailClassificationEngine` - banco identification
- [ ] `TemplateManager` básico - CRUD templates
- [ ] `Tier1RegexStrategy` - solo BCR templates conocidos
- [ ] `ValidationEngine` básico - business rules
- [ ] Tests unitarios para componentes core

**Success Criteria**:
- ✅ Procesar emails del BCR con 90%+ accuracy
- ✅ Templates básicos funcionando
- ✅ Pipeline end-to-end operativo

### **Phase 2: Secure Multi-Strategy System (Semana 3-4)**
**Objetivo**: Sistema híbrido SEGURO con múltiples estrategias

**Deliverables**:
- [ ] `Tier2SecureHybridStrategy` - SECURE HTML structure parsing
- [ ] `SecureHTMLParser` - parser HTML controlado y seguro
- [ ] `SecureLLMClient` - LLM integration con controles de seguridad
- [ ] `TemplateSecurityValidator` - validación de templates LLM
- [ ] `SecurityAuditLogger` - logging de todas las operaciones LLM
- [ ] `TransactionReview` system - human review queue
- [ ] Security monitoring dashboard

**Success Criteria**:
- ✅ Manejar bancos conocidos con templates desconocidos DE FORMA SEGURA
- ✅ HTML parsing funcionando con controles de seguridad
- ✅ Template auto-generation con validación de seguridad
- ✅ Zero code execution vulnerabilities
- ✅ Comprehensive security audit trail

### **Phase 3: Advanced AI Features (Semana 5-6)**
**Objetivo**: Estrategias LLM y discovery mode

**Deliverables**:
- [ ] `Tier3LLMAssistedStrategy` - LLM para analysis
- [ ] `Tier4FullLLMStrategy` - discovery mode completo
- [ ] Advanced validation rules - statistical analysis
- [ ] Machine learning optimization - strategy selection
- [ ] Cost optimization algorithms

**Success Criteria**:
- ✅ Manejar bancos completamente desconocidos
- ✅ Sistema aprende y mejora automáticamente
- ✅ Costos promedio <$0.02 por email

### **Phase 4: Production Hardening (Semana 7-8)**
**Objetivo**: Sistema listo para producción

**Deliverables**:
- [ ] Error handling y recovery robusto
- [ ] Scaling optimizations - caching, queues
- [ ] Security audit - PCI compliance considerations
- [ ] User feedback integration - correction loops
- [ ] Documentation completa y deployment guides

**Success Criteria**:
- ✅ Sistema puede manejar 1000+ emails/hora
- ✅ 99.9% uptime
- ✅ Feedback loop completamente funcional

---

## 📊 **MÉTRICAS DE ÉXITO**

### **Performance Targets**

| Metric | Target Value | Current Status |
|--------|--------------|----------------|
| **Overall Accuracy** | 90%+ | TBD |
| **Average Cost per Email** | <$0.02 | TBD |
| **Processing Time (Tier 1)** | <100ms | TBD |
| **Processing Time (Average)** | <1s | TBD |
| **Template Auto-Generation Success** | 80%+ | TBD |
| **Human Review Rate** | <20% | TBD |

### **Cost Breakdown Estimates**

```
Monthly Processing (10,000 emails):
- Tier 1 (60%): 6,000 emails × $0 = $0
- Tier 2 (25%): 2,500 emails × $0.01 = $25
- Tier 3 (10%): 1,000 emails × $0.05 = $50
- Tier 4 (5%): 500 emails × $0.10 = $50

Total Monthly Cost: $125 for 10,000 emails = $0.0125 per email
```

---

## 🛡️ **CONSIDERACIONES DE SEGURIDAD**

### **🚨 Principios de Seguridad Aplicados**

**NUNCA ejecutamos código Python generado por LLM en producción**

#### **1. LLM Input/Output Control**
```python
class SecureLLMClient:
    """Cliente LLM con controles de seguridad estrictos"""
    
    def __init__(self):
        self.max_input_length = 5000  # Limit input size
        self.allowed_output_keys = ['amount_selector', 'merchant_selector', 'date_selector']
        
    def structured_json_response(self, prompt):
        # 1. Validate and sanitize input
        clean_prompt = self.sanitize_prompt(prompt)
        
        # 2. Get LLM response
        response = self.llm_client.chat_completion(clean_prompt)
        
        # 3. Validate response format
        parsed_response = self.validate_json_response(response)
        
        # 4. Sanitize CSS selectors
        sanitized_config = self.sanitize_css_selectors(parsed_response)
        
        return sanitized_config
    
    def sanitize_css_selectors(self, config):
        """Validate CSS selectors for safety"""
        safe_config = {}
        
        for key, selector in config.items():
            if key in self.allowed_output_keys:
                # Remove dangerous characters
                clean_selector = re.sub(r'[<>(){}[\];]', '', selector)
                # Validate selector format
                if self.is_valid_css_selector(clean_selector):
                    safe_config[key] = clean_selector
        
        return safe_config
```

#### **2. Execution Sandboxing**
```python
class SecureHTMLParser:
    """HTML parser que ejecuta selectores de forma controlada"""
    
    def __init__(self):
        # Whitelist of allowed BeautifulSoup methods
        self.allowed_methods = ['select_one', 'select', 'get_text', 'get']
        
    def secure_extract(self, html_content, parsing_config):
        """Execute parsing with strict controls"""
        try:
            # 1. Parse HTML safely
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 2. Execute selectors with timeout
            with timeout(seconds=5):  # Prevent infinite loops
                result = self.execute_selectors_safely(soup, parsing_config)
            
            # 3. Validate extracted data
            validated_result = self.validate_extracted_data(result)
            
            return validated_result
            
        except Exception as e:
            # Log security incidents
            self.log_security_event(f"Parsing failed: {e}", parsing_config)
            return {'error': 'Parsing failed', 'confidence': 0.0}
    
    def execute_selectors_safely(self, soup, config):
        """Execute CSS selectors with validation"""
        result = {}
        
        for field, selector in config.items():
            try:
                # Validate selector before execution
                if not self.is_safe_selector(selector):
                    continue
                
                # Execute with BeautifulSoup (safe)
                element = soup.select_one(selector)
                if element:
                    # Extract text safely
                    text_content = element.get_text(strip=True)
                    # Validate and clean extracted data
                    result[field] = self.clean_extracted_value(text_content)
                    
            except Exception as e:
                # Continue with other fields if one fails
                self.log_selector_error(field, selector, e)
                continue
        
        return result
```

#### **3. Template Validation Pipeline**
```python
class TemplateSecurityValidator:
    """Valida templates antes de usar en producción"""
    
    def validate_template_security(self, template_config):
        """Comprehensive security validation"""
        validation_results = {
            'css_selectors_safe': self.validate_css_selectors(template_config),
            'no_code_injection': self.check_code_injection_patterns(template_config),
            'regex_patterns_safe': self.validate_regex_patterns(template_config),
            'output_format_valid': self.validate_output_format(template_config)
        }
        
        return all(validation_results.values())
    
    def validate_css_selectors(self, config):
        """Validate CSS selectors don't contain dangerous patterns"""
        dangerous_patterns = [
            r'javascript:',
            r'data:',
            r'<script',
            r'eval\(',
            r'expression\(',
        ]
        
        for selector in config.values():
            if isinstance(selector, str):
                for pattern in dangerous_patterns:
                    if re.search(pattern, selector, re.IGNORECASE):
                        return False
        
        return True
```

#### **4. Audit & Monitoring**
```python
class SecurityAuditLogger:
    """Log de seguridad para todas las operaciones LLM"""
    
    def log_llm_interaction(self, operation, input_data, output_data, user_id):
        SecurityLog.objects.create(
            operation=operation,
            input_hash=hashlib.sha256(str(input_data).encode()).hexdigest(),
            output_data=output_data,
            user_id=user_id,
            timestamp=timezone.now(),
            risk_level=self.assess_risk_level(operation, output_data)
        )
    
    def detect_anomalies(self):
        """Detect suspicious LLM-generated patterns"""
        recent_templates = SecurityLog.objects.filter(
            operation='template_generation',
            timestamp__gte=timezone.now() - timedelta(hours=24)
        )
        
        # Check for suspicious patterns
        for log in recent_templates:
            if self.is_suspicious_template(log.output_data):
                self.alert_security_team(log)
```

---

## 🔧 **ARQUITECTURA TÉCNICA**

### **Database Schema Updates**

```python
# New models needed for secure email processing
class ProcessingStrategy(models.Model):
    name = models.CharField(max_length=50)
    tier = models.IntegerField()
    success_rate = models.FloatField()
    average_cost = models.FloatField()
    average_processing_time = models.FloatField()

class ProcessingResult(models.Model):
    email_queue = models.ForeignKey(EmailQueue, on_delete=models.CASCADE)
    strategy_used = models.ForeignKey(ProcessingStrategy, on_delete=models.CASCADE)
    confidence_score = models.FloatField()
    processing_time_ms = models.FloatField()
    api_cost = models.FloatField()
    needs_human_review = models.BooleanField()

class SecureHTMLTemplate(models.Model):
    """Secure HTML parsing templates - NO EXECUTABLE CODE"""
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)
    template_name = models.CharField(max_length=100)
    
    # LLM-generated CSS selectors (SAFE)
    amount_selector = models.TextField(help_text="CSS selector for amount")
    merchant_selector = models.TextField(help_text="CSS selector for merchant")
    date_selector = models.TextField(help_text="CSS selector for date")
    reference_selector = models.TextField(blank=True, help_text="CSS selector for reference")
    
    # Validation patterns
    amount_regex = models.TextField(help_text="Regex for amount validation")
    date_format = models.CharField(max_length=50, help_text="Expected date format")
    
    # Security metadata
    security_validated = models.BooleanField(default=False)
    human_reviewed = models.BooleanField(default=False)
    security_score = models.FloatField(default=0.0)
    
    # Performance tracking
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    confidence_score = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SecurityLog(models.Model):
    """Audit log for all LLM interactions"""
    operation = models.CharField(max_length=50)  # 'template_generation', 'parsing', etc.
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    input_hash = models.CharField(max_length=64)  # SHA256 of input data
    output_data = models.JSONField()
    risk_level = models.CharField(max_length=20, choices=[
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'), 
        ('high', 'High Risk'),
        ('critical', 'Critical Risk')
    ])
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['operation', 'timestamp']),
            models.Index(fields=['risk_level', 'timestamp']),
        ]
```

### **API Endpoints**

```python
# New API endpoints needed
/api/email-processing/
    POST /process-email/          # Process single email
    POST /bulk-process/           # Process multiple emails
    GET  /processing-status/{id}/ # Check processing status

/api/templates/
    GET    /templates/            # List templates
    POST   /templates/generate/   # Generate new template
    PUT    /templates/{id}/       # Update template
    DELETE /templates/{id}/       # Delete template

/api/validation/
    GET  /review-queue/           # Get items needing review
    POST /validate-transaction/   # Submit validation
    POST /correct-transaction/    # Submit correction

/api/metrics/
    GET /processing-metrics/      # Get performance metrics
    GET /cost-analysis/           # Get cost breakdown
    GET /accuracy-reports/        # Get accuracy reports
```

---

## 🚀 **GETTING STARTED**

### **Prerequisites**
- Django backend con modelos existentes (Bank, EmailPattern, Transaction)
- Gmail API integration funcionando
- OpenAI API key para LLM features
- Redis para caching y queues

### **Development Setup**
```bash
# 1. Install new dependencies (with security focus)
pip install beautifulsoup4 lxml openai anthropic bleach html5lib

# 2. Run migrations for new secure models
python manage.py makemigrations
python manage.py migrate

# 3. Create secure test templates
python manage.py shell
>>> from scripts.create_secure_test_templates import create_secure_bcr_templates
>>> create_secure_bcr_templates()

# 4. Run security-focused tests
python manage.py test email_processing.security_tests
python manage.py test email_processing.parsing_tests

# 5. Run security audit
python manage.py run_security_audit
```

### **Testing Strategy**
1. **Security Tests**: Validación de todas las medidas de seguridad
2. **Unit Tests**: Cada componente individual con focus en seguridad
3. **Integration Tests**: Pipeline completo end-to-end con audit trail
4. **Performance Tests**: Load testing con 1000+ emails
5. **Penetration Tests**: Intentos de code injection y bypass de seguridad
6. **Cost Tests**: Validar que costos están dentro de targets
7. **LLM Output Validation Tests**: Verificar que outputs son siempre seguros

---

## 📚 **NEXT STEPS**

1. **Security Review** de este plan con equipo de seguridad
2. **Preparar ambiente de desarrollo SEGURO** con dependencias validadas
3. **Crear branch** `feature/secure-email-processing`
4. **Implementar Security Framework** antes de cualquier LLM integration
5. **Setup Security Testing Environment** aislado de producción
6. **Comenzar Phase 1** con EmailClassificationEngine y controles de seguridad
7. **Setup testing data** con emails reales del BCR en ambiente seguro

### **🚨 Security Checklist Before Implementation**

- [ ] **Code Review Process**: Todo código que maneja LLM output debe ser revieweado
- [ ] **Security Testing Environment**: Ambiente aislado para testing de templates
- [ ] **Audit Trail Setup**: Logging completo de todas las operaciones LLM
- [ ] **Input Validation Framework**: Validación estricta de todos los inputs
- [ ] **Output Sanitization**: Limpieza de todos los outputs LLM
- [ ] **Access Controls**: Permisos restrictivos para template management
- [ ] **Incident Response Plan**: Plan para manejar security incidents
- [ ] **Regular Security Audits**: Revisión periódica de templates y logs

---

---

## 🔄 **CHANGELOG**

### **v2.0 - Secure Implementation (Diciembre 2024)**
- ✅ **SECURITY FIRST**: Eliminado code execution de LLM outputs
- ✅ **Secure HTML Parsing**: LLM genera selectores CSS, no código Python
- ✅ **Comprehensive Security Framework**: Validation, sandboxing, audit trails
- ✅ **Security Testing**: Penetration testing y validation de outputs
- ✅ **Audit Trail**: Logging completo de todas las operaciones LLM

### **v1.0 - Initial Plan (Diciembre 2024)**
- ❌ **DEPRECATED**: Propuesta original con code execution (INSEGURO)

---

*Documento actualizado: Diciembre 2024*
*Versión: 2.0 - SECURE IMPLEMENTATION*
*Owner: AFP Development Team*
*Security Review: REQUIRED* 