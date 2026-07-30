"""
Service — Chatbot (Solu) v2
Brain: HuggingFace Inference API (Mistral/LLaMA)
Memory: FAISS RAG (ICAR Crop Guides)
Ears: Groq Whisper (voice → text)
Voice: edge-tts / gTTS (text → speech)
i18n: en / kn / hi / te / mr
"""
import os
import uuid
import json
import tempfile
import asyncio
from typing import Optional, Dict, Any, List
from huggingface_hub import InferenceClient
from groq import Groq
# import whisper (Moved to lazy import to avoid torch dependency issues on some Windows setups)
from backend.config.settings import get_settings
from backend.utils.logger import logger
from backend.plugins.ai.planner.crop_planner import rag_search

settings = get_settings()

# ── Ears: Groq Whisper ────────────────────────────────────────────────────────
_groq_client = Groq(api_key=settings.GROQ_API_KEY)
_local_whisper = None

def _get_local_whisper():
    global _local_whisper
    if _local_whisper is None:
        try:
            import whisper
            _local_whisper = whisper.load_model("base")
        except Exception as e:
            logger.error(f"[chatbot] Failed to load local whisper model: {e}")
            return None
    return _local_whisper


# ── Brain: Groq (Llama 3.3) ───────────────────────────────────────────────────
def _get_groq_brain_completion(messages: List[Dict[str, str]], voice_out: bool = False):
    """
    Standard Groq Reasoning call. 
    Uses llama-3.3-70b-versatile for high reasoning capability.
    """
    model = getattr(settings, "GROQ_CHAT_MODEL", "llama-3.3-70b-versatile")
    try:
        response = _groq_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=500 if not voice_out else 150,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"[chatbot] Groq Brain error: {e}")
        return None

LANG_NAMES = {
    "en": "English", "kn": "Kannada",
    "hi": "Hindi",   "te": "Telugu",
    "ta": "Tamil",   "mr": "Marathi"
}


SOLU_SYSTEM_PROMPT = """You are Solu, AquaSol's expert agricultural digital twin assistant.

PERSONALITY & CONCISE TONE:
- Warm, practical, highly knowledgeable agronomy expert.
- Match language strictly: {lang_name}.
- CONCISE BY DEFAULT: Keep responses direct, crisp, and brief (2 to 3 sentences maximum). Avoid generic pleasantries, filler phrases, or repetitive intros.
- If the user asks for short answers, be ultra-concise (1 to 2 crisp sentences with exact metrics).

OPERATOR CAPABILITIES & ACTION TAGS (CRITICAL):
- ONLY generate an action tag if the user EXPLICITLY asks you to perform a control action (e.g., "irrigate zone 1", "turn off water", "stop irrigation", "set zone to auto").
- Do NOT generate an action tag for general questions, greetings, or when the user asks for advice or short answers!
- If a control action IS explicitly requested by the user, attach the tag ONLY at the very end of your message in this exact format:
  `[ACTION: {{"type": "irrigate"|"stop"|"set_mode", "zone_id": "<zone_id>", "duration_min": <minutes_if_irrigate>, "mode": "<manual|auto>"}}]`
- Extract the exact `zone_id` from the FARM STATE context matching the zone name/number mentioned by the user.

AGRONOMIC DATA & CONTEXT:
- Base all crop, soil, and irrigation recommendations dynamically on the real-time FARM STATE data and EXPERT MEMORY guides provided in the context.
"""

LANG_VOICE_MAP = {
    "en": "en-IN-NeerjaNeural",
    "hi": "hi-IN-MadhurNeural",
    "kn": "kn-IN-SapnaNeural",
    "te": "te-IN-ShrutiNeural",
    "ta": "ta-IN-PallaviNeural",
    "mr": "mr-IN-AarohiNeural",
}


async def transcribe_audio(audio_bytes: bytes, filename: str = "voice.webm") -> str:
    """
    STT using Groq Whisper (Cloud) with local fallback.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[-1], delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        # Try Groq Cloud Whisper first (fastest)
        try:
            with open(tmp_path, "rb") as file:
                transcription = _groq_client.audio.transcriptions.create(
                    file=(filename, file.read()),
                    model=settings.GROQ_WHISPER_MODEL,
                )
            os.unlink(tmp_path)
            return transcription.text.strip()
        except Exception as e:
            logger.warning(f"[chatbot] Groq Whisper failed, falling back to local: {e}")
            
        # Local Fallback
        def _transcribe():
            model = _get_local_whisper()
            result = model.transcribe(tmp_path)
            return result["text"]

        transcription = await asyncio.to_thread(_transcribe)
        os.unlink(tmp_path)
        return transcription.strip()
    except Exception as e:
        logger.error(f"[whisper] Transcription fatal error: {e}")
        return ""


async def chat(
    message: str,
    context: Dict[str, Any],
    lang: str = "en",
    voice_out: bool = False,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    db: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Solu v3: Groq Brain (Llama 3.3) + Agentic RAG Memory + DB i18n + Autonomous Actions.
    Returns: { reply, lang, audio_path, rag_used }
    """
    from backend.services.i18n_service import get_localized_message
    from sqlalchemy import select

    # ── 1. RAG Search (Agentic Retrieval) ─────────────────────────────────────
    # We perform a semantic search to ground the "Expert" reasoning.
    knowledge_chunks = rag_search(query=message, top_k=3)
    knowledge_text = "\n\n".join([f"[{c['crop']}]: {c['text']}" for c in knowledge_chunks])
    if not knowledge_text:
        knowledge_text = "No specific guide found. Use general best practices."

    # ── 2. Build Prompt ───────────────────────────────────────────────────────
    lang_name = LANG_NAMES.get(lang, "English")
    system = SOLU_SYSTEM_PROMPT.format(lang_name=lang_name)
    
    # Enhanced context with RAG memory
    prompt_context = f"""
    FARM STATE:
    {json.dumps(context, indent=2, default=str)}

    EXPERT MEMORY:
    {knowledge_text}
    """

    messages = [
        {"role": "system", "content": system},
    ]
    
    if conversation_history:
        messages.extend(conversation_history[-6:])
    
    messages.append({"role": "user", "content": f"CONTEXT:\n{prompt_context}\n\nUSER MESSAGE: {message}"})

    # ── 3. Groq Reasoning ────────────────────────────────────────────────────
    reply = _get_groq_brain_completion(messages, voice_out)
    
    if not reply:
        # Fallback to DB-localized error message
        reply = await get_localized_message("chatbot_error_generic", lang)

    # ── 3.5 Intercept and execute Actions ────────────────────────────────────
    import re
    action_match = re.search(r'\[ACTION:\s*({.*?})\]', reply)
    executed_notice = ""

    if action_match:
        tag_str = action_match.group(0)
        json_str = action_match.group(1)
        reply = reply.replace(tag_str, "").strip()

        if db is not None:
            try:
                action_data = json.loads(json_str)
                action_type = action_data.get("type")
                zone_id = action_data.get("zone_id")

                if zone_id and action_type in ("irrigate", "stop", "set_mode"):
                    from backend.control.controller import execute_manual_override
                    from backend.models.farm import Zone
                    
                    z_res = await db.execute(select(Zone).where(Zone.id == zone_id))
                    zone = z_res.scalar_one_or_none()
                    
                    if zone:
                        z_name = zone.name or "Zone"
                        if action_type == "irrigate":
                            duration = int(action_data.get("duration_min", 15))
                            await execute_manual_override(
                                zone_id=str(zone_id),
                                farm_id=str(zone.farm_id),
                                action="irrigate",
                                duration_min=duration,
                                reason="Executed by Solu AI Chatbot Agent",
                                db=db
                            )
                            executed_notice = f"\n\n✅ Started irrigation on {z_name} for {duration} minutes."
                        
                        elif action_type == "stop":
                            await execute_manual_override(
                                zone_id=str(zone_id),
                                farm_id=str(zone.farm_id),
                                action="stop",
                                duration_min=0,
                                reason="Stopped by Solu AI Chatbot Agent",
                                db=db
                            )
                            executed_notice = f"\n\n🛑 Stopped irrigation on {z_name}."
                        
                        elif action_type == "set_mode":
                            target_mode = action_data.get("mode", "auto")
                            zone.mode = target_mode
                            await db.commit()
                            executed_notice = f"\n\n⚙️ Configured {z_name} to {target_mode.upper()} mode."
            except Exception as e:
                logger.error(f"[chatbot] Failed to execute agentic action: {e}")

    # Append clean human-readable execution notice if an action was executed
    if executed_notice and executed_notice not in reply:
        reply += executed_notice

    # Absolute Safety Purge: Strip any residual [ACTION: ...] or raw debug strings from final reply
    reply = re.sub(r'\[ACTION:\s*({.*?})\]', '', reply).strip()
    reply = re.sub(r'\*\([^)]*Command executed:[^)]*\)\*', '', reply).strip()

    # ── 4. TTS ───────────────────────────────────────────────────────────────
    audio_path = None
    if voice_out:
        audio_path = await _generate_tts(reply, lang)

    return {
        "reply": reply, 
        "lang": lang, 
        "audio_path": audio_path,
        "rag_used": len(knowledge_chunks) > 0
    }


async def _generate_tts(text: str, lang: str) -> Optional[str]:
    """
    Multilingual TTS using hyper-realistic Microsoft Azure Neural Voices via edge-tts.
    """
    try:
        import edge_tts
        audio_dir = os.path.join(os.path.dirname(__file__), "..", "..", "static", "audio")
        os.makedirs(audio_dir, exist_ok=True)

        filename = f"solu_{uuid.uuid4().hex[:8]}.mp3"
        out_path = os.path.join(audio_dir, filename)

        # Map languages to premium Neural voices
        voice_map = {
            "en": "en-IN-NeerjaNeural",
            "hi": "hi-IN-SwaraNeural",
            "kn": "kn-IN-SapnaNeural",
            "te": "te-IN-ShrutiNeural",
            "ta": "ta-IN-PallaviNeural",
            "mr": "mr-IN-AarohiNeural"
        }
        
        voice = voice_map.get(lang, "en-IN-NeerjaNeural")
        
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(out_path)
        
        return f"/static/audio/{filename}"
    except Exception as e:
        logger.warning(f"[tts] edge-tts error: {e}")
        return None
