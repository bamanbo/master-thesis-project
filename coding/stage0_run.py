def call_model(provider, model, prompt, temperature, max_retries=50):
    """Returns (raw_text, resolved_model_id, thinking_tokens)"""

    delay = 2.0 
    for attempt in range(max_retries):
        try:
            if provider == "gemini":
                from google import genai
                from google.genai import types
                client = genai.Client()
                r = client.models.generate_content(
                    model = model,
                    contents = prompt,
                    config = types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=300,
                        thinking_config=types.ThinkingConfig(thinking_level="low"),
                    ),
                )
                thinking = getattr(r.usage_metadata, "thoughts_token_count", None)
                return r.text, getattr(r, "model_version", model), thinking

            # if provider == "anthropic":
            #     from anthropic import Anthropic


            