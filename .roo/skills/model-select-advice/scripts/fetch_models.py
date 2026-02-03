import urllib.request, json, re, yaml

def fetch_and_format():
    url = 'https://openrouter.ai/api/v1/models'
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
        
        core7_pattern = re.compile(r'gpt|claude|gemini|deepseek|qwen|kimi|grok', re.I)
        filtered = [m for m in data['data'] if core7_pattern.search(m['id'])]
        
        # Sort by input price
        sorted_models = sorted(filtered, key=lambda x: float(x['pricing'].get('prompt', 0)))
        
        output_data = []
        for m in sorted_models:
            p = m['pricing']
            # Convert to $/1M tokens
            i_p = float(p.get('prompt', 0)) * 1000000
            o_p = float(p.get('completion', 0)) * 1000000
            
            model_info = {
                "id": m['id'],
                "name": m['name'],
                "pricing": {
                    "input_1m": round(i_p, 4),
                    "output_1m": round(o_p, 4)
                },
                "introduce": m.get('description', "No description available.")
            }
            output_data.append(model_info)
            
        print(yaml.dump(output_data, allow_unicode=True, sort_keys=False))
        
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fetch_and_format()
