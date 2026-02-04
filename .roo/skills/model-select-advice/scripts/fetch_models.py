import urllib.request, json, re, yaml, datetime

def fetch_and_format():
    url = 'https://openrouter.ai/api/v1/models'
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
        
        core7_pattern = re.compile(r'gpt|claude|gemini|deepseek|qwen|kimi|grok', re.I)
        
        # Current date for filtering (6 months ago)
        now = datetime.datetime.now()
        six_months_ago = now - datetime.timedelta(days=180)
        
        filtered = []
        for m in data['data']:
            # Core 7 filter
            if not core7_pattern.search(m['id']):
                continue
            
            # Date filter (OpenRouter uses 'created' timestamp)
            created_ts = m.get('created')
            if created_ts:
                created_date = datetime.datetime.fromtimestamp(created_ts)
                if created_date < six_months_ago:
                    continue
            
            filtered.append(m)
        
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
                "context_window": m.get('context_length', 0),
                "created": datetime.datetime.fromtimestamp(m.get('created', 0)).strftime('%Y-%m-%d') if m.get('created') else "Unknown",
                "introduce": m.get('description', "No description available.")
            }
            output_data.append(model_info)
            
        print(yaml.dump(output_data, allow_unicode=True, sort_keys=False))
        
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fetch_and_format()
