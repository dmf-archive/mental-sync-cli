import pytest
import asyncio
from msc.oracle import Oracle, create_adapter

# 本地转发器配置
BASE_URL = "http://localhost:8317"
API_KEY = "123456"
MODEL_ID = "gemini-2.5-flash-lite"

@pytest.mark.asyncio
async def test_integration_local_proxy_heterogeneous_formats():
    """
    实地测试：验证 Oracle 能够通过不同的适配器格式与同一个本地转发器通信。
    转发器支持：openai, anthropic, gemini 格式。
    """
    
    # 1. 创建不同格式的适配器，但都指向同一个本地转发器
    # 注意：实际转发器可能需要不同的后缀路径，这里根据通用惯例设置
    
    # OpenAI 格式
    p_openai = create_adapter(
        "openai", 
        name="local-openai", 
        model=MODEL_ID, 
        api_key=API_KEY, 
        base_url=f"{BASE_URL}/v1"
    )
    
    # Anthropic 格式
    p_anthropic = create_adapter(
        "anthropic", 
        name="local-anthropic", 
        model=MODEL_ID, 
        api_key=API_KEY, 
        base_url=BASE_URL # Anthropic 适配器内部会处理路径
    )
    
    # Gemini 格式
    p_gemini = create_adapter(
        "gemini", 
        name="local-gemini", 
        model=MODEL_ID, 
        api_key=API_KEY, 
        base_url=BASE_URL
    )
    
    # 2. 封装进 Oracle
    oracle = Oracle(providers=[p_openai, p_anthropic, p_gemini])
    
    print(f"\n[Integration Test] Testing with model: {MODEL_ID}")
    
    # 3. 逐一验证生成能力
    test_prompt = "Respond with exactly the word 'ACK' if you receive this."
    
    # 测试 OpenAI 路由
    print("-> Testing OpenAI format...")
    res_oa = await p_openai.generate(test_prompt)
    print(f"OpenAI Response: {res_oa}")
    assert "ACK" in res_oa.upper()
    
    # 测试 Anthropic 路由
    print("-> Testing Anthropic format...")
    res_ant = await p_anthropic.generate(test_prompt)
    print(f"Anthropic Response: {res_ant}")
    assert "ACK" in res_ant.upper()
    
    # 测试 Gemini 路由
    print("-> Testing Gemini format...")
    res_gem = await p_gemini.generate(test_prompt)
    print(f"Gemini Response: {res_gem}")
    assert "ACK" in res_gem.upper()

@pytest.mark.asyncio
async def test_integration_failover_with_real_proxy():
    """
    实地测试：验证故障转移逻辑。
    构造一个必然失败的适配器（错误的 URL）放在首位，验证是否能自动切换到正常的。
    """
    # 错误的适配器
    p_bad = create_adapter(
        "openai", 
        name="bad-proxy", 
        model=MODEL_ID, 
        api_key="wrong", 
        base_url="http://localhost:9999/v1" 
    )
    
    # 正确的适配器
    p_good = create_adapter(
        "openai", 
        name="good-proxy", 
        model=MODEL_ID, 
        api_key=API_KEY, 
        base_url=f"{BASE_URL}/v1"
    )
    
    oracle = Oracle(providers=[p_bad, p_good])
    
    print("\n[Integration Test] Testing Failover...")
    # 应该跳过 p_bad，由 p_good 返回结果
    response = await oracle.generate(MODEL_ID, "Say 'FAILOVER_SUCCESS'")
    print(f"Failover Response: {response}")
    assert "FAILOVER_SUCCESS" in response.upper()

if __name__ == "__main__":
    # 允许手动运行此脚本进行实地验证
    async def run_manual_tests():
        try:
            await test_integration_local_proxy_heterogeneous_formats()
            await test_integration_failover_with_real_proxy()
            print("\n[SUCCESS] All integration tests passed!")
        except Exception as e:
            print(f"\n[FAILURE] Integration test failed: {e}")
            
    asyncio.run(run_manual_tests())
