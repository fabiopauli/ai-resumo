# Ferramenta de Análise de Documentos Jurídicos

Esta ferramenta processa documentos jurídicos (PDFs) utilizando APIs de IA (Google Gemini ou OpenAI) para gerar resumos de argumentos jurídicos. Foi projetada para auxiliar profissionais do direito, extraindo e analisando automaticamente o conteúdo de recursos jurídicos.

## Funcionalidades

- Extrai texto de arquivos PDF
- Identifica números de processo em documentos jurídicos
- Processamento em duas etapas:
  - Análise inicial com modelo de IA
  - Análise refinada para melhorar a saída
- Salvamento automático dos resultados das análises inicial e aprimorada

## Versões Disponíveis

Este projeto possui duas versões principais:

### 1. Versão Google Gemini (`main.py`)
- Utiliza a API do Google Gemini para processamento de texto
- Requer uma chave de API do Google Gemini

### 2. Versão OpenAI (`main-openai.py`)
- Utiliza a API da OpenAI para processamento de texto
- Requer credenciais da OpenAI (organização e projeto)

## Requisitos

- Python 3.7+
- Pacotes Python necessários (veja `requirements.txt`)
- Acesso à API do Google Gemini OU OpenAI

## Instalação

1. Clone este repositório:
   ```
   git clone <url-do-repositório>
   cd <diretório-do-repositório>
   ```

2. Instale os pacotes necessários:
   ```
   pip install -r requirements.txt
   ```

3. Crie um arquivo `.env` no diretório raiz do projeto com suas credenciais:

   Para a versão Google Gemini:
   ```
   GEMINI_API_KEY=sua-chave-api
   ```

   Para a versão OpenAI:
   ```
   OPENAI_ORGANIZATION=sua-organizacao
   OPENAI_PROJECT=seu-projeto
   ```

## Uso

1. Coloque seus arquivos PDF na pasta `docs` (será criada se não existir)
2. Execute o script desejado:
   
   Para a versão Google Gemini:
   ```
   python main.py
   ```
   
   Para a versão OpenAI:
   ```
   python main-openai.py
   ```
   
3. Os resultados da análise serão salvos na pasta `responses`

## Saída

Para cada arquivo PDF processado, a ferramenta gera:
- Um arquivo de análise inicial: `[número_processo/nome_arquivo]_[timestamp].txt`
- Um arquivo de análise aprimorada: `[número_processo/nome_arquivo]_improved_[timestamp].txt`

Onde:
- `número_processo` é o número do processo jurídico extraído (se encontrado)
- `nome_arquivo` é o nome original do arquivo PDF (usado se nenhum número de processo for encontrado)
- `timestamp` está no formato `AAAAMMDD_HHMMSS`

## Estrutura de Arquivos

```
projeto/
├── main.py              # Script principal (Google Gemini)
├── main-openai.py       # Script alternativo (OpenAI)
├── .env                 # Variáveis de ambiente
├── requirements.txt     # Pacotes necessários
├── docs/                # Coloque os arquivos PDF aqui
└── responses/           # As análises geradas são salvas aqui
```

## Como Funciona

1. **Extração de Texto do PDF**: A ferramenta lê cada arquivo PDF e extrai todo o texto.
2. **Detecção do Número do Processo**: Identifica números de processo jurídico no formato NNNNNNN-NN.AAAA.N.NN.NNNN.
3. **Análise Inicial**: Usa o modelo de IA para identificar e resumir os principais argumentos jurídicos.
4. **Análise Aprimorada**: Usa um modelo mais poderoso para refinar a análise inicial, melhorando a clareza e a legibilidade.
5. **Geração de Saída**: Ambas as análises são salvas como arquivos de texto com nomenclatura apropriada.

## Personalização

Você pode modificar os prompts no código para ajustar como a IA analisa os documentos. Os prompts atuais são projetados para analisar recursos judiciais em português do Brasil.