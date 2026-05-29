import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

try:
    from openai import OpenAI
except ImportError:
    import openai
    OpenAI = None


def load_openai_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY must be set in the environment.")
    return api_key


def get_openai_client(api_key: Optional[str] = None):
    api_key = api_key or load_openai_api_key()
    if OpenAI is not None:
        return OpenAI(api_key=api_key)

    import openai
    openai.api_key = api_key
    return openai


def transcribe_with_whisper(audio_file_path: str, prompt: Optional[str] = None, model: str = "whisper-1") -> str:
    """Transcribe an audio file using OpenAI Whisper.

    Args:
        audio_file_path: Path to the audio file to transcribe.
        prompt: Optional prompt to help guide Whisper.
        model: The Whisper transcription model name.

    Returns:
        The transcribed text.
    """
    audio_path = Path(audio_file_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    client = get_openai_client()
    with audio_path.open("rb") as audio_file:
        result = client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            prompt=prompt,
        )

    return result.get("text", "")


def extract_response_text(response) -> str:
    """Extract generated text from an OpenAI responses API result."""
    try:
        data = response.parse(to=dict)
    except Exception:
        try:
            data = response.json()
        except Exception:
            data = response

    if isinstance(data, str):
        return data

    if isinstance(data, list):
        # Some SDK responses may serialize directly to a simple list of text items.
        return "\n".join(str(item) for item in data if item is not None)

    if not isinstance(data, dict):
        raise TypeError(f"Unexpected response parse type: {type(data)}")

    output = data.get("output") or data.get("choices")
    if isinstance(output, list) and output:
        first = output[0]
        if isinstance(first, dict):
            # Responses API style
            content = first.get("content")
            if isinstance(content, list):
                text_parts = [item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "output_text"]
                if text_parts:
                    return "".join(text_parts)
            # Fall back to first message text
            return first.get("text", "") or first.get("output_text", "")
        return str(first)

    if isinstance(output, str):
        return output

    raise ValueError("Unable to extract text from response")


def generate_story_text(
    prompt: str,
    prd_file_path: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.8,
    max_output_tokens: int = 1000,
) -> str:
    """Generate story text from a prompt and PRD reference without speaking the PRD directly."""
    prd_path = Path(prd_file_path)
    if not prd_path.exists():
        raise FileNotFoundError(f"PRD file not found: {prd_file_path}")

    story_instructions = (
        "You are creating an audiobook story for a 4-year-old named Meera. "
        "The story should be warm, gentle, and imaginative, with clear narration and natural pacing. "
        "Write it as a polished audiobook story without explicit stage directions such as 'pause for a moment' "
        "or 'the narrator says'. Keep the text smooth, flowing, and ready for direct narration. "
        "Do not read the PRD file aloud. Instead, use it as a style and requirements reference. "
        "Write the story using the prompt below as the main direction. "
    )
    story_prompt = f"{story_instructions}\nPrompt: {prompt}"

    client = get_openai_client()
    response = client.responses.create(
        model=model,
        input=story_prompt,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )

    story_text = extract_response_text(response)
    if not story_text:
        raise ValueError("No story text generated from the model.")
    return story_text


def synthesize_text_to_speech(
    text: str,
    output_file_path: str,
    model: str = "gpt-4o-mini-tts",
    voice: str = "alloy",
    response_format: str = "mp3",
    instructions: Optional[str] = None,
    speed: float = 1.0,
) -> Path:
    """Generate speech audio from text using OpenAI TTS.

    Args:
        text: The text to synthesize.
        output_file_path: Path to write the generated audio file.
        model: The TTS model to use.
        voice: The voice style to use.
        response_format: Audio format to write.
        instructions: Optional voice direction for the TTS model.
        speed: Speech speed multiplier.

    Returns:
        Path to the written audio file.
    """
    client = get_openai_client()
    if instructions is None:
        instructions = (
            "Speak the text in a warm, calm, and expressive storyteller voice. "
            "Use gentle pacing and natural pauses, without adding explicit narration cues or stage directions. "
            "Keep the output smooth and polished so it sounds like a finished audiobook narration."
        )

    response = client.audio.speech.create(
        input=text,
        model=model,
        voice=voice,
        instructions=instructions,
        response_format=response_format,
        speed=speed,
    )

    output_path = Path(output_file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(response, 'write_to_file'):
        response.write_to_file(output_path)
    elif hasattr(response, 'content'):
        output_path.write_bytes(response.content)
    elif hasattr(response, 'read'):
        output_path.write_bytes(response.read())
    else:
        raise TypeError(f'Unexpected TTS response type: {type(response)}')
    return output_path


def convert_story_to_audio(
    story_text: str,
    output_file_path: str,
    tts_model: str = "gpt-4o-mini-tts",
    voice: str = "alloy",
    response_format: str = "mp3",
    instructions: Optional[str] = None,
    speed: float = 1.0,
) -> Path:
    """Convert generated story text into an audio file."""
    return synthesize_text_to_speech(
        text=story_text,
        output_file_path=output_file_path,
        model=tts_model,
        voice=voice,
        response_format=response_format,
        instructions=instructions,
        speed=speed,
    )


def generate_audiobook_audio(
    prd_file_path: str,
    prompt: str,
    output_file_path: Optional[str] = None,
    generate_audio: bool = True,
    model: Optional[str] = None,
    story_model: str = "gpt-4o-mini",
    tts_model: str = "gpt-4o-mini-tts",
    voice: str = "alloy",
    response_format: str = "mp3",
    instructions: Optional[str] = None,
    speed: float = 1.0,
    temperature: float = 0.8,
    max_output_tokens: int = 1000,
) -> dict:
    """Generate audiobook story text and optionally synthesize it into an audio file.

    Args:
        prd_file_path: Path to the PRD reference file.
        prompt: Prompt used to generate the story text.
        output_file_path: Path to write audio if generate_audio is True.
        generate_audio: If False, only story text is returned.
        model: Optional alias for the TTS model. If provided, it overrides `tts_model`.
        story_model: Model to use for story generation.
        tts_model: Model to use for text-to-speech.

    Returns:
        A dict containing 'story_text' and 'audio_file_path' (or None).
    """
    prd_path = Path(prd_file_path)
    if not prd_path.exists():
        raise FileNotFoundError(f"PRD file not found: {prd_file_path}")

    if model is not None:
        tts_model = model

    story_text = generate_story_text(
        prompt=prompt,
        prd_file_path=prd_file_path,
        model=story_model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )

    audio_file_path = None
    if generate_audio:
        if not output_file_path:
            raise ValueError("output_file_path is required when generate_audio=True")
        audio_file_path = convert_story_to_audio(
            story_text=story_text,
            output_file_path=output_file_path,
            tts_model=tts_model,
            voice=voice,
            response_format=response_format,
            instructions=instructions,
            speed=speed,
        )

    return {
        "story_text": story_text,
        "audio_file_path": audio_file_path,
    }
