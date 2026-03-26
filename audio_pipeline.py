import os
import sys
import tempfile

# Adicionar DLLs NVIDIA ao PATH antes de importar qualquer coisa
_nvidia_path = os.path.join(sys.prefix, "Lib", "site-packages", "nvidia")
if os.path.isdir(_nvidia_path):
    for dirpath, dirnames, filenames in os.walk(_nvidia_path):
        if dirpath.endswith("bin"):
            os.add_dll_directory(dirpath)
            os.environ["PATH"] = dirpath + os.pathsep + os.environ.get("PATH", "")

import numpy as np
import sounddevice as sd
from scipy.io import wavfile
import requests

SAMPLE_RATE = 16000
CHANNELS = 1

# Singleton para o modelo Whisper (carregado uma vez)
_whisper_model = None
_whisper_model_size = None


class AudioRecorder:
    def __init__(self):
        self.frames = []
        self.stream = None
        self.recording = False

    def _callback(self, indata, frames, time, status):
        if self.recording:
            self.frames.append(indata.copy())

    def start(self):
        self.frames = []
        self.recording = True
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            callback=self._callback,
        )
        self.stream.start()

    def stop(self):
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        if not self.frames:
            return None

        audio = np.concatenate(self.frames, axis=0)
        temp_path = os.path.join(tempfile.gettempdir(), "transcritor_audio.wav")
        audio_int16 = (audio * 32767).astype(np.int16)
        wavfile.write(temp_path, SAMPLE_RATE, audio_int16)
        return temp_path


def transcribe_audio(audio_path, model_size="medium"):
    global _whisper_model, _whisper_model_size

    from faster_whisper import WhisperModel

    if _whisper_model is None or _whisper_model_size != model_size:
        try:
            _whisper_model = WhisperModel(
                model_size, device="cuda", compute_type="float16"
            )
        except Exception:
            _whisper_model = WhisperModel(
                model_size, device="cpu", compute_type="int8"
            )
        _whisper_model_size = model_size

    segments, _ = _whisper_model.transcribe(audio_path, language="pt", beam_size=5)
    text = " ".join(segment.text.strip() for segment in segments)
    return text


def rewrite_text(raw_text, model="llama3.1:8b"):
    prompt = f"""Voce e um assistente que reescreve textos transcritos de audio. O texto abaixo foi transcrito automaticamente de uma gravacao de voz e pode conter erros, repeticoes, frases incompletas ou falta de pontuacao.

Sua tarefa:
- Corrigir erros gramaticais e de pontuacao
- Remover repeticoes e palavras de preenchimento (tipo "eh", "ne", "entao", "assim")
- Reorganizar frases para ficarem mais claras e coesas
- Manter o significado original e o tom do falante
- Manter o texto em portugues
- NAO adicionar informacoes que nao estejam no texto original
- NAO resumir excessivamente -- mantenha o conteudo completo
- Responda APENAS com o texto reescrito, sem explicacoes

Texto transcrito:
\"\"\"
{raw_text}
\"\"\"

Texto reescrito:"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.ConnectionError:
        return "[ERRO] Ollama nao esta em execucao. Inicie o Ollama e tente novamente."
    except requests.Timeout:
        return "[ERRO] Tempo limite excedido. O texto pode ser demasiado longo."
    except Exception as e:
        return f"[ERRO] {str(e)}"
