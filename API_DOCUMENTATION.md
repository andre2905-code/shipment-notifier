# Shipment Notifier - API Documentation

**API Title:** Shipment Notifier - Condomínio  
**Framework:** FastAPI  
**Database:** SQLite  
**Authentication:** None (currently using Twilio credentials via environment variables)

---

## Table of Contents
1. [Overview](#overview)
2. [Database Models](#database-models)
3. [API Endpoints](#api-endpoints)
4. [Enums & Status Codes](#enums--status-codes)
5. [Environment Variables](#environment-variables)
6. [Error Handling](#error-handling)
7. [Background Tasks](#background-tasks)

---

## Overview

The Shipment Notifier API is designed to manage package deliveries in condominiums. It provides functionality for:
- Resident registration and validation via AI-powered proof of residence checks
- Package registration and tracking
- Package pickup confirmation with secure retrieval codes
- WhatsApp notifications for residents

### Key Features
- **AI-powered validation** using Google Gemini to verify proof of residence
- **WhatsApp integration** using Twilio for notifications
- **Secure package retrieval** using unique retrieval codes
- **Background task processing** for non-blocking operations

---

## Database Models

### Morador (Resident)

Represents a condominium resident.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | Integer | Primary key | Auto-increment, indexed |
| `nome` | String(100) | Resident's full name | Required |
| `whatsapp` | String(20) | WhatsApp phone number | Required |
| `bloco` | String(10) | Block/Building identifier | Required |
| `apartamento` | String(10) | Apartment number | Required |
| `status_validacao` | Enum | Validation status | Default: `PENDENTE` |
| `data_cadastro` | DateTime | Registration timestamp | Server-generated with timezone |
| `encomendas` | Relationship | Associated packages | Cascade delete |

**Unique Constraint:** `bloco` + `apartamento` combination must be unique per resident

---

### Encomenda (Package)

Represents a package delivery for a resident.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | Integer | Primary key | Auto-increment, indexed |
| `morador_id` | Integer | Foreign key to Morador | References `moradores.id` |
| `status` | Enum | Package status | Default: `AGUARDANDO` |
| `codigo_retirada` | String(64) | Unique retrieval code | Unique, randomly generated (100000-999999) |
| `data_recebimento` | DateTime | Received timestamp | Server-generated with timezone |
| `data_retirada` | DateTime | Pickup timestamp | Auto-updated on pickup |
| `morador` | Relationship | Associated resident | Back-reference to Morador |

---

## API Endpoints

### 1. Register Resident

**Endpoint:** `POST /cadastrar-morador`

**Description:** Register a new resident and automatically send a proof of residence verification request via WhatsApp.

**Status Code:** `201 Created`

**Request Body:**
```json
{
  "nome": "string",
  "whatsapp": "string",
  "bloco": "string",
  "apartamento": "string"
}
```

**Request Parameters:**
| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `nome` | String | Resident's full name | Yes |
| `whatsapp` | String | WhatsApp phone number (can include +55 prefix, dashes, or parentheses) | Yes |
| `bloco` | String | Building/block identifier | Yes |
| `apartamento` | String | Apartment number | Yes |

**Example Request:**
```bash
curl -X POST http://localhost:8000/cadastrar-morador \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Silva",
    "whatsapp": "+55 (11) 95278-6261",
    "bloco": "A",
    "apartamento": "101"
  }'
```

**Success Response:**
```json
{
  "mensagem": "Morador pré-cadastrado com sucesso!",
  "morador_id": 1,
  "status": "PENDENTE",
  "notificacao": "Solicitação de comprovante enviada via WhatsApp."
}
```

**Error Responses:**

| Status | Detail |
|--------|--------|
| `400 Bad Request` | "Já existe um morador cadastrado neste bloco e apartamento." |

**Background Task:** Sends a WhatsApp message requesting proof of residence

---

### 2. Validate Proof of Residence

**Endpoint:** `POST /validar-comprovante`

**Description:** Upload a proof of residence document (image) to be validated by AI. The AI uses Google Gemini to extract and verify the address matches the condominium's official address.

**Status Code:** `200 OK`

**Request Parameters:**
| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `morador_id` | Integer (Form) | ID of the resident | Yes |
| `comprovante` | File (Form) | Image file of proof of residence (JPG/PNG) | Yes |

**Example Request:**
```bash
curl -X POST http://localhost:8000/validar-comprovante \
  -F "morador_id=1" \
  -F "comprovante=@proof.jpg"
```

**Success Response (Approved):**
```json
{
  "status": "sucesso",
  "mensagem": "Comprovante validado automaticamente pela IA!",
  "dados_ia": {
    "endereco_encontrado": "Rua das Palmeiras, 1500, Araçatuba - SP",
    "mesmo_condominio": true,
    "motivo": "N/A"
  }
}
```

**Success Response (Rejected):**
```json
{
  "status": "negado",
  "mensagem": "O endereço não confere com os registros do condomínio.",
  "dados_ia": {
    "endereco_encontrado": "Rua Diferente, 100, Araçatuba - SP",
    "mesmo_condominio": false,
    "motivo": "Endereço não corresponde ao do condomínio"
  }
}
```

**Error Responses:**

| Status | Detail |
|--------|--------|
| `404 Not Found` | "Morador não encontrado." |
| `400 Bad Request` | "Não foi possível ler a imagem. Certifique-se de que é um arquivo válido (JPG/PNG)." |
| `502 Bad Gateway` | "Erro na comunicação com a IA: [error details]" |

**Notes:**
- Resident must be registered before validation
- Image must be a valid JPG or PNG file
- Address comparison ignores CEP differences and abbreviations (e.g., "R." vs "Rua")
- Official condominium address: "Rua das Palmeiras, 1500, Araçatuba - SP"

---

### 3. Register Package

**Endpoint:** `POST /registrar-encomenda`

**Description:** Register a new package delivery for a resident. Only residents with approved proof of residence can receive packages.

**Status Code:** `201 Created`

**Request Body:**
```json
{
  "bloco": "string",
  "apartamento": "string"
}
```

**Request Parameters:**
| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `bloco` | String | Building/block identifier | Yes |
| `apartamento` | String | Apartment number | Yes |

**Example Request:**
```bash
curl -X POST http://localhost:8000/registrar-encomenda \
  -H "Content-Type: application/json" \
  -d '{
    "bloco": "A",
    "apartamento": "101"
  }'
```

**Success Response:**
```json
{
  "mensagem": "Encomenda registrada com sucesso",
  "morador": "João Silva",
  "codigo": "456789",
  "notificacao": "Sendo enviada no WhatsApp em segundo plano..."
}
```

**Error Responses:**

| Status | Detail |
|--------|--------|
| `403 Forbidden` | "Morador não encontrado ou comprovante de residência ainda não aprovado." |

**Background Task:** Sends a WhatsApp message with the package retrieval code

**Notes:**
- Resident must have `status_validacao = APROVADO` to register packages
- Retrieval code is randomly generated (6-digit number between 100000-999999)
- Notification sent asynchronously via WhatsApp

---

### 4. Register Package Pickup

**Endpoint:** `PUT /registrar-retirada`

**Description:** Confirm package pickup by validating the retrieval code. Updates the package status to "ENTREGUE" (Delivered) and records the pickup timestamp.

**Status Code:** `200 OK`

**Request Body:**
```json
{
  "codigo_retirada": "string"
}
```

**Request Parameters:**
| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `codigo_retirada` | String | Package retrieval code | Yes |

**Example Request:**
```bash
curl -X PUT http://localhost:8000/registrar-retirada \
  -H "Content-Type: application/json" \
  -d '{
    "codigo_retirada": "456789"
  }'
```

**Success Response:**
```json
{
  "status": "sucesso",
  "mensagem": "Retirada confirmada!",
  "entregue_para": "João Silva",
  "apartamento": "101 - Bloco A",
  "horario_retirada": "14:35:42"
}
```

**Error Responses:**

| Status | Detail |
|--------|--------|
| `404 Not Found` | "Código de retirada inválido ou inexistente." |
| `400 Bad Request` | "Esta encomenda já foi retirada em [date/time]." |

**Notes:**
- Retrieval code must be exactly as provided during package registration
- Package can only be picked up once
- Timestamp is recorded in the database for audit purposes

---

## Enums & Status Codes

### StatusValidacao (Resident Validation Status)

| Value | Description |
|-------|-------------|
| `PENDENTE` | Waiting for proof of residence submission |
| `APROVADO` | Proof of residence verified and approved |
| `REJEITADO` | Proof of residence rejected (address mismatch) |

### StatusEncomenda (Package Status)

| Value | Description |
|-------|-------------|
| `AGUARDANDO` | Package received, waiting for pickup |
| `ENTREGUE` | Package picked up by resident |

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200 OK` | Request successful |
| `201 Created` | Resource successfully created |
| `400 Bad Request` | Invalid request data or duplicate entry |
| `403 Forbidden` | Access denied (resident not approved) |
| `404 Not Found` | Resource not found |
| `502 Bad Gateway` | External service error (AI/Twilio) |

---

## Environment Variables

The API requires the following environment variables (typically in a `.env` file):

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key for proof of residence validation | Yes |
| `TWILIO_ACCOUNT_SID` | Twilio account SID for WhatsApp integration | Yes |
| `TWILIO_AUTH_TOKEN` | Twilio authentication token | Yes |
| `DATABASE_URL` | SQLite database connection string | Yes |

**Example `.env`:**
```
GEMINI_API_KEY=your_gemini_api_key_here
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
DATABASE_URL=sqlite:///./condominio.db
```

---

## Error Handling

All errors follow a consistent JSON format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Scenarios

**Duplicate Resident Registration:**
- Attempting to register a resident in a block/apartment that already has a resident
- Response: `400 Bad Request` - "Já existe um morador cadastrado neste bloco e apartamento."

**Invalid Image File:**
- Uploading a non-image file or corrupted image
- Response: `400 Bad Request` - "Não foi possível ler a imagem. Certifique-se de que é um arquivo válido (JPG/PNG)."

**Unapproved Resident:**
- Attempting to register a package for a resident without approved proof of residence
- Response: `403 Forbidden` - "Morador não encontrado ou comprovante de residência ainda não aprovado."

**AI Service Error:**
- Connection or processing error with Google Gemini API
- Response: `502 Bad Gateway` - "Erro na comunicação com a IA: [error details]"

**Invalid Retrieval Code:**
- Entering a code that doesn't exist or has already been used
- Response: `404 Not Found` or `400 Bad Request` with descriptive message

---

## Background Tasks

The API uses FastAPI's `BackgroundTasks` to handle non-blocking operations:

### Task 1: Welcome & Proof Request (After Resident Registration)

**Function:** `solicitar_comprovante_whatsapp(nome, telefone)`

**Triggered:** POST `/cadastrar-morador`

**Action:** Sends a WhatsApp message:
```
Olá, *[nome]*! Bem-vindo(a) ao sistema de Encomendas do Condomínio. 🏢

Seu pré-cadastro foi realizado na portaria.
Para liberarmos o recebimento de suas encomendas e notificações por aqui, 
por favor, envie uma foto nítida do seu *comprovante de residência*.
```

---

### Task 2: Package Notification (After Package Registration)

**Function:** `notificar_morador_whatsapp(nome, telefone, codigo)`

**Triggered:** POST `/registrar-encomenda`

**Action:** Sends a WhatsApp message:
```
Olá, *[nome]*! 📦

Você tem uma nova encomenda aguardando na portaria.
Apresente este código para retirar: *[codigo]*
```

---

## Data Flow

### Registration & Validation Flow

```
1. POST /cadastrar-morador
   ↓
2. Resident created with status = PENDENTE
   ↓
3. [Background] WhatsApp sent requesting proof
   ↓
4. POST /validar-comprovante (resident uploads image)
   ↓
5. AI validates address
   ↓
6. Status updated to APROVADO or REJEITADO
```

### Package Registration & Pickup Flow

```
1. POST /registrar-encomenda (bloco, apartamento)
   ↓
2. Verify resident has status = APROVADO
   ↓
3. Create package with unique retrieval code
   ↓
4. [Background] WhatsApp sent with retrieval code
   ↓
5. PUT /registrar-retirada (codigo_retirada)
   ↓
6. Validate code and update status to ENTREGUE
```

---

## Phone Number Formatting

The API automatically normalizes WhatsApp phone numbers by:
- Removing all non-digit characters (+, -, spaces, parentheses)
- Prepending the Brazilian country code (55) if not already present
- Converting to Twilio format: `whatsapp:+55XXXXXXXXXXX`

**Examples:**
- `11952786261` → `+5511952786261`
- `(11) 95278-6261` → `+5511952786261`
- `+55 11 95278-6261` → `+5511952786261`

---

## Database Setup

The database schema is automatically created on application startup if tables don't exist:

```python
Base.metadata.create_all(bind=engine)
```

**Database Type:** SQLite  
**Foreign Key Support:** Enabled via SQLite pragma  
**Cascade Rules:** Deleting a resident cascades to delete all associated packages

---

## Running the API

To start the FastAPI server:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

**Interactive API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Example Usage Workflow

### Step 1: Register a Resident

```bash
curl -X POST http://localhost:8000/cadastrar-morador \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Maria Santos",
    "whatsapp": "+5511987654321",
    "bloco": "B",
    "apartamento": "202"
  }'
```

Response: `morador_id: 2`

### Step 2: Upload Proof of Residence

```bash
curl -X POST http://localhost:8000/validar-comprovante \
  -F "morador_id=2" \
  -F "comprovante=@utility_bill.jpg"
```

Response: Status approved with AI validation details

### Step 3: Register a Package

```bash
curl -X POST http://localhost:8000/registrar-encomenda \
  -H "Content-Type: application/json" \
  -d '{
    "bloco": "B",
    "apartamento": "202"
  }'
```

Response: `codigo: 789456`

### Step 4: Confirm Package Pickup

```bash
curl -X PUT http://localhost:8000/registrar-retirada \
  -H "Content-Type: application/json" \
  -d '{
    "codigo_retirada": "789456"
  }'
```

Response: Pickup confirmed with timestamp

---

## Version History

- **Current Version:** 1.0
- **Framework:** FastAPI
- **Database:** SQLite with SQLAlchemy ORM
- **Python Version:** 3.8+

