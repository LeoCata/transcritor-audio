import ctypes
import os
import threading
import customtkinter as ctk

from audio_pipeline import AudioRecorder, transcribe_audio, rewrite_text

# DPI awareness para Windows 11
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# Tema — estilo Claude Code
ctk.set_appearance_mode("dark")

# Paleta Claude Code
BG_MAIN = "#0d0f1a"       # fundo principal (terminal escuro)
BG_CARD = "#151726"        # fundo dos cards
BG_INPUT = "#1c1e30"       # fundo das textboxes
BG_HOVER = "#1f2235"       # hover em cards
ACCENT = "#d97757"         # laranja/terracotta Claude
ACCENT_HOVER = "#c4673f"   # hover do accent
ACCENT_MUTED = "#d9775730" # accent com transparencia
RED = "#ef4444"
RED_HOVER = "#dc2626"
GREEN = "#4ade80"
ORANGE = "#f59e0b"
TEXT_PRIMARY = "#e8eaf0"
TEXT_SECONDARY = "#9ca3b0"
TEXT_MUTED = "#5a6170"
BORDER = "#282a3a"

# Fontes
FONT_MONO = "Consolas"
FONT_UI = "Segoe UI"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Transcritor de Audio")
        self.geometry("880x750")
        self.minsize(720, 600)
        self.configure(fg_color=BG_MAIN)

        self.recorder = AudioRecorder()
        self.is_recording = False
        self.is_processing = False
        self._pulse_id = None

        self._build_ui()

    def _build_ui(self):
        # Container principal
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=32, pady=24)

        # Header — estilo terminal
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill="x", pady=(0, 6))

        # Icone Claude + titulo
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(anchor="w")

        ctk.CTkLabel(
            title_row, text="\u2728",
            font=ctk.CTkFont(size=22),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            title_row, text="transcritor",
            font=ctk.CTkFont(family=FONT_MONO, size=24, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkLabel(
            title_row, text="de audio",
            font=ctk.CTkFont(family=FONT_MONO, size=24),
            text_color=TEXT_MUTED,
        ).pack(side="left", padx=(6, 0))

        # Subtitulo
        ctk.CTkLabel(
            header,
            text="grava \u2022 transcreve \u2022 reescreve com IA local",
            font=ctk.CTkFont(family=FONT_MONO, size=12),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(4, 0))

        # Separador
        ctk.CTkFrame(main, fg_color=BORDER, height=1).pack(fill="x", pady=(14, 16))

        # Barra de configuracoes + botao gravar
        top_bar = ctk.CTkFrame(main, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 14))

        # Settings lado esquerdo
        settings = ctk.CTkFrame(top_bar, fg_color="transparent")
        settings.pack(side="left")

        ctk.CTkLabel(settings, text="modelo whisper",
                      font=ctk.CTkFont(family=FONT_MONO, size=11),
                      text_color=TEXT_MUTED).grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.whisper_model = ctk.CTkOptionMenu(
            settings, values=["small", "medium", "large-v3"],
            width=130, height=30,
            font=ctk.CTkFont(family=FONT_MONO, size=12),
            fg_color=BG_INPUT, button_color=BORDER,
            button_hover_color=TEXT_MUTED,
            dropdown_fg_color=BG_CARD,
            dropdown_hover_color=BG_HOVER,
            text_color=TEXT_PRIMARY,
        )
        self.whisper_model.set("medium")
        self.whisper_model.grid(row=1, column=0, padx=(0, 16))

        ctk.CTkLabel(settings, text="modelo ollama",
                      font=ctk.CTkFont(family=FONT_MONO, size=11),
                      text_color=TEXT_MUTED).grid(row=0, column=1, sticky="w")
        self.ollama_model = ctk.CTkOptionMenu(
            settings, values=["llama3.1:8b", "mistral:7b", "llama3.2:3b"],
            width=150, height=30,
            font=ctk.CTkFont(family=FONT_MONO, size=12),
            fg_color=BG_INPUT, button_color=BORDER,
            button_hover_color=TEXT_MUTED,
            dropdown_fg_color=BG_CARD,
            dropdown_hover_color=BG_HOVER,
            text_color=TEXT_PRIMARY,
        )
        self.ollama_model.set("llama3.1:8b")
        self.ollama_model.grid(row=1, column=1)

        # Botao gravar — estilo Claude Code
        self.record_btn = ctk.CTkButton(
            top_bar,
            text="\U0001F3A4  gravar",
            font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#ffffff",
            corner_radius=8,
            width=150,
            height=38,
            command=self._toggle_recording,
        )
        self.record_btn.pack(side="right")

        # Status
        status_frame = ctk.CTkFrame(main, fg_color="transparent", height=20)
        status_frame.pack(fill="x", pady=(0, 8))

        self.status_dot = ctk.CTkCanvas(status_frame, width=8, height=8,
                                         bg=BG_MAIN, highlightthickness=0)
        self.status_dot.create_oval(0, 0, 8, 8, fill=GREEN, outline="", tags="dot")
        self.status_dot.pack(side="left", padx=(0, 8), pady=4)

        self.status_label = ctk.CTkLabel(
            status_frame, text="pronto",
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            text_color=TEXT_MUTED,
        )
        self.status_label.pack(side="left")

        # Barra de progresso
        self.progress = ctk.CTkProgressBar(
            main, mode="indeterminate", height=2,
            progress_color=ACCENT, fg_color=BG_INPUT,
        )

        # Card transcricao original
        self.raw_text = self._build_card(main, "transcricao original", 0)

        # Card texto reescrito
        self.rewritten_text = self._build_card(main, "texto reescrito", 1)

    def _build_card(self, parent, title, index):
        """Constroi um card com header, botao copiar e textbox."""
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color=BG_CARD,
                             border_width=1, border_color=BORDER)
        card.pack(fill="both", expand=True, pady=(0, 10) if index == 0 else (0, 0))

        # Header do card
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 0))

        ctk.CTkLabel(
            header, text=title,
            font=ctk.CTkFont(family=FONT_MONO, size=12, weight="bold"),
            text_color=TEXT_SECONDARY,
        ).pack(side="left")

        # Botao copiar — icone clipboard estilo Claude Code
        textbox = ctk.CTkTextbox(
            card,
            font=ctk.CTkFont(family=FONT_MONO, size=13),
            corner_radius=6,
            fg_color=BG_INPUT,
            text_color=TEXT_PRIMARY,
            border_width=0,
            wrap="word",
            state="disabled",
        )

        copy_btn = ctk.CTkButton(
            header,
            text="\U0001F4CB",
            width=32, height=26,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            hover_color=BG_HOVER,
            text_color=TEXT_MUTED,
            corner_radius=6,
            command=lambda: self._copy_text(textbox),
        )
        copy_btn.pack(side="right")

        textbox.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        return textbox

    def _toggle_recording(self):
        if self.is_processing:
            return
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_recording()

    def _start_recording(self):
        self.is_recording = True
        self.record_btn.configure(
            text="\u23F9  parar", fg_color=RED, hover_color=RED_HOVER,
        )
        self._update_status("a gravar...", RED)
        self._set_text(self.raw_text, "")
        self._set_text(self.rewritten_text, "")
        self.recorder.start()
        self._pulse_recording()

    def _pulse_recording(self):
        if not self.is_recording:
            return
        current = self.status_dot.itemcget("dot", "fill")
        new_color = BG_MAIN if current == RED else RED
        self.status_dot.itemconfig("dot", fill=new_color)
        self._pulse_id = self.after(500, self._pulse_recording)

    def _stop_recording(self):
        self.is_recording = False
        if self._pulse_id:
            self.after_cancel(self._pulse_id)
            self._pulse_id = None

        self.record_btn.configure(
            text="\U0001F3A4  gravar", fg_color=ACCENT, hover_color=ACCENT_HOVER,
        )
        audio_path = self.recorder.stop()

        if not audio_path:
            self._update_status("nenhum audio capturado", ORANGE)
            return

        self.is_processing = True
        self.record_btn.configure(state="disabled")
        self._update_status("a transcrever...", ORANGE)
        self.progress.pack(fill="x", pady=(0, 8))
        self.progress.start()

        thread = threading.Thread(target=self._process_audio, args=(audio_path,), daemon=True)
        thread.start()

    def _process_audio(self, audio_path):
        try:
            model_size = self.whisper_model.get()
            raw = transcribe_audio(audio_path, model_size=model_size)
            self.after(0, self._set_text, self.raw_text, raw)

            if not raw.strip():
                self.after(0, self._update_status, "nenhuma fala detetada", ORANGE)
                return

            self.after(0, self._update_status, "a reescrever...", ORANGE)
            ollama_model = self.ollama_model.get()
            rewritten = rewrite_text(raw, model=ollama_model)
            self.after(0, self._set_text, self.rewritten_text, rewritten)
            self.after(0, self._update_status, "pronto", GREEN)

        except Exception as e:
            self.after(0, self._update_status, f"erro: {str(e)}", RED)
        finally:
            try:
                os.remove(audio_path)
            except OSError:
                pass
            self.after(0, self._finish_processing)

    def _finish_processing(self):
        self.is_processing = False
        self.progress.stop()
        self.progress.pack_forget()
        self.record_btn.configure(state="normal")

    def _update_status(self, text, color=GREEN):
        self.status_label.configure(text=text)
        self.status_dot.delete("all")
        self.status_dot.create_oval(0, 0, 8, 8, fill=color, outline="", tags="dot")

    def _set_text(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _copy_text(self, widget):
        widget.configure(state="normal")
        text = widget.get("1.0", "end").strip()
        widget.configure(state="disabled")
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            old_text = self.status_label.cget("text")
            self._update_status("copiado!", ACCENT)
            self.after(1500, lambda: self._update_status(old_text, GREEN))


if __name__ == "__main__":
    app = App()
    app.mainloop()
