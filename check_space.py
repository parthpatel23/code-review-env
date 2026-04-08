from huggingface_hub import HfApi
api = HfApi()
info = api.space_info("Parth-Patel-23/code-review-env")
print("Stage:", info.runtime.stage)
print("Raw:", info.runtime.raw)
