# Transcritor de Audio

Aplicacao desktop que grava audio do microfone, transcreve automaticamente com Whisper e reescreve o texto de forma mais coesa usando IA local (Ollama).

Tudo funciona offline e de forma gratuita.

## Requisitos

- **Windows 10/11**
- **Python 3.12** — [Download](https://www.python.org/downloads/)
- **Ollama** — [Download](https://ollama.com/download)
- **GPU NVIDIA** (opcional, mas recomendado para maior velocidade)

## Instalacao

### 1. Instalar Python 3.12

Descarrega e instala o Python 3.12 a partir de [python.org](https://www.python.org/downloads/).

> Durante a instalacao, marca a opcao **"Add Python to PATH"**.

### 2. Instalar Ollama

Descarrega e instala o Ollama a partir de [ollama.com](https://ollama.com/download).

Depois de instalar, abre um terminal e descarrega o modelo de IA:

```bash
ollama pull llama3.1:8b
```

> Este modelo ocupa cerca de 4.7GB. Podes usar modelos mais leves como `llama3.2:3b` (2GB) se tiveres pouca RAM.

### 3. Configurar o projeto

Abre um terminal na pasta do projeto e corre:

```bash
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

> O ultimo comando so e necessario se tiveres GPU NVIDIA. Sem GPU, o programa funciona na mesma (apenas mais lento).

## Como usar

### Opcao 1 — Duplo clique (recomendado)

Faz duplo clique no ficheiro `Transcritor.bat`. Ele ativa o ambiente virtual e abre o programa automaticamente.

> Na primeira vez, se o ambiente virtual nao existir, o `.bat` cria-o e instala tudo sozinho.

### Opcao 2 — Terminal

```bash
venv\Scripts\activate
python app.py
```

## Utilizar o programa

1. Seleciona o **modelo Whisper** (small, medium ou large-v3)
2. Seleciona o **modelo Ollama** (llama3.1:8b, mistral:7b ou llama3.2:3b)
3. Clica em **Gravar** e fala para o microfone
4. Clica em **Parar** quando terminares
5. Aguarda a transcricao e a reescrita
6. Usa o botao de copiar para copiar o texto

## Modelos Whisper

| Modelo | RAM necessaria | Velocidade | Qualidade |
|--------|---------------|------------|-----------|
| small | ~2GB | Rapido | Boa |
| medium | ~5GB | Medio | Muito boa |
| large-v3 | ~10GB | Lento | Excelente |

## Resolucao de problemas

### Erro: "cublas64_12.dll is not found"

Instala as bibliotecas CUDA dentro do venv:

```bash
venv\Scripts\activate
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

Se o erro persistir, o programa usa CPU automaticamente (mais lento mas funciona).

### Erro: "Ollama nao esta em execucao"

Certifica-te que o Ollama esta a correr. Abre um terminal e corre:

```bash
ollama serve
```

### Erro ao ativar venv no PowerShell

Se aparecer um erro de "ExecutionPolicy", corre primeiro:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### O programa demora muito a iniciar pela primeira vez

Na primeira utilizacao, o Whisper descarrega o modelo (~1-3GB dependendo do tamanho escolhido). Isto so acontece uma vez.
