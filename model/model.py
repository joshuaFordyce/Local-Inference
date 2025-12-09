import asyncio
import base64
import io
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import torch
from PIL import Image
from transformers import AutoProcessor, BitsAndBytesConfig, AutoModelForVision2Seq

MODEL_ID = "HuggingFaceTB/SmolVLM-256M-Instruct"
DEFAULT_MAX_WORKERS = 1 
BASE64_PREAMBLE = "data:image/png;base64,"

class Model:
    def __init__(self, **kwargs):
        self.model = None
        self.processor = None
        self._executor = ThreadPoolExecutor(max_workers=DEFAULT_MAX_WORKERS)
        self.model_id = MODEL_ID

    def load(self):
        print(f" Loading model: {self.model_id}...")
        start_time = time.time()

        has_gpu = torch.cuda.is_available()
        # QUANTIZATION CONFIG (The VRAM Saver)

        if has_gpu:
            bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True
            )
            model_kwargs = {
                "quantization_config": bnb_config,
                "device_map": "auto"
            }
        else:
            model_kwargs = {
                "device_map": "cpu",
                "low_cpu_mem_usage": True,
                "torch_dtype": torch.float32
            }


        # 1. Load Processor (Handles both Tokenizer and Image Processor)
        self.processor = AutoProcessor.from_pretrained(self.model_id)

        # 2. Load Model with Quantization
        self.model = AutoModelForVision2Seq.from_pretrained(
            self.model_id,
            trust_remote_code=True,
            **model_kwargs
        )
        print(f"Model loaded in {time.time() - start_time:.2f}s")

    async def predict(self, model_input):
        loop = asyncio.get_running_loop()
        # Offload the blocking inference to the thread pool
        result = await loop.run_in_executor(
            self._executor,
            self._predict_sync,
            model_input
        )
        return result

    def _predict_sync(self, model_input):
        # 1. Decode Image
        b64_string = model_input.get("image_b64", "")
        if BASE64_PREAMBLE in b64_string:
            b64_string = b64_string.replace(BASE64_PREAMBLE, "")
        
        image = Image.open(io.BytesIO(base64.b64decode(b64_string))).convert("RGB")
        prompt_text = model_input.get("prompt", "Describe this image.")

        # 2. Format Prompt (Llava 1.6 expects specific formatting)
        # Note: AutoProcessor handles the <image> token placement automatically for 1.6
        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prompt_text},
                ],
            },
        ]
        text_prompt = self.processor.apply_chat_template(conversation, add_generation_prompt=True)

        # 3. Preprocess Inputs (Move to GPU)
        inputs = self.processor(images=image, text=text_prompt, return_tensors="pt").to("cuda")

        # 4. Generate
        with torch.inference_mode():
            output = self.model.generate(**inputs, max_new_tokens=200, do_sample=False)

        # 5. Decode Output
        decoded_output = self.processor.decode(output[0], skip_special_tokens=True)
        
        # Clean up the prompt from the output
        # (Naive split, can be improved depending on model output format)
        if "[/INST]" in decoded_output:
            return decoded_output.split("[/INST]")[-1].strip()
        
        return decoded_output