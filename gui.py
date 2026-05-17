import streamlit as st
import audit
import time
from datetime import datetime
import io
import sys

# 设置页面配置
st.set_page_config(
    page_title="AI 中转站纯度审计工具",
    page_icon="🛡️",
    layout="wide"
)

# 自定义 CSS 样式
st.markdown("""
    <style>
    .main {
        max-width: 1000px;
        margin: 0 auto;
    }
    .stButton>button {
        width: 100%;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    .status-box {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

def run_audit_ui(base_url, api_key, model, profile, skip_options):
    # 创建客户端和报告器
    client = audit.APIClient(base_url, api_key, model, verbose=False)
    report = audit.Reporter()
    
    st.info(f"🚀 开始审计目标: `{base_url}` | 模型: `{model}`")
    
    # 初始化进度条
    steps = [
        ("基础信息侦察", "infra", audit.test_infrastructure, (base_url, report)),
        ("获取模型列表", "models", audit.test_models, (client, report)),
        ("Token 注入检测", "token", audit.test_token_injection, (client, report)),
        ("提示词提取测试", "prompt", audit.test_prompt_extraction, (client, report)),
        ("指令冲突测试", "conflict", audit.test_instruction_conflict, (client, report)),
        ("越狱测试", "jailbreak", audit.test_jailbreak, (client, report)),
        ("上下文长度测试", "context", audit.test_context_length, (client, report)),
        ("工具调用劫持测试 (AC-1.a)", "tool", audit.test_tool_substitution, (client, report)),
        ("错误响应泄露测试 (AC-2)", "error", audit.test_error_leakage, (client, report, api_key)),
        ("流式完整性测试 (AC-1 SSE)", "stream", audit.test_stream_integrity, (client, report)),
    ]
    
    # 根据 profile 添加 Web3 测试
    if profile in ("web3", "full"):
        steps.append(("Web3 提示词注入测试", "web3_inj", audit.test_web3_injection, (client, report)))
    
    # 添加基础设施指纹和延迟抖动
    steps.append(("基础设施指纹识别", "infra_fingerprint", audit.test_infra_fingerprint, (client, report)))
    steps.append(("延迟抖动分析", "latency", audit.test_latency_variance, (client, report)))
    steps.append(("模型真实性与纯度测试", "purity", audit.test_model_purity, (client, report)))

    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 用于收集结果
    results_context = {
        "injection": None,
        "leaked": False,
        "overridden": None,
        "substitution_detected": False,
        "substitution_inconclusive": False,
        "err_severity": "none",
        "err_inconclusive": False,
        "stream_verdict": "clean",
        "stream_inconclusive": False,
        "web3_inj_verdict": "clean",
        "web3_inj_inconclusive": False,
        "spoofing_detected": False,
        "intel_fail_rate": 0,
    }

    total_steps = len(steps)
    for i, (name, key, func, args_params) in enumerate(steps):
        if skip_options.get(key, False):
            status_text.text(f"跳过步骤: {name}...")
            progress_bar.progress((i + 1) / total_steps)
            continue
            
        status_text.text(f"正在执行: {name}...")
        
        try:
            # 特殊处理不同步骤的参数
            if key == "context":
                res = func(client, report, fast_mode=skip_options.get("fast_context", False))
            elif key == "error":
                res = func(client, report, api_key, aggressive=False)
                results_context["err_severity"], results_context["err_inconclusive"] = res
            else:
                res = func(*args_params)
                # 记录核心结果用于最后的评分
                if key == "token": results_context["injection"] = res
                elif key == "prompt": results_context["leaked"] = res
                elif key == "conflict": results_context["overridden"] = res
                elif key == "tool": results_context["substitution_detected"], results_context["substitution_inconclusive"] = res
                elif key == "stream": results_context["stream_verdict"], results_context["stream_inconclusive"] = res
                elif key == "web3_inj": results_context["web3_inj_verdict"], results_context["web3_inj_inconclusive"] = res
                elif key == "purity": results_context["spoofing_detected"], results_context["intel_fail_rate"] = res
        except Exception as e:
            st.error(f"步骤 {name} 执行出错: {str(e)}")
            report.flag("yellow", f"{name} 执行失败: {str(e)}")
            
        progress_bar.progress((i + 1) / total_steps)
        time.sleep(0.1)

    status_text.text("✅ 审计完成！")
    
    # 渲染风险评估
    st.subheader("📊 风险评估报告")
    
    d1 = results_context["injection"] is not None and results_context["injection"] > 100
    d2 = results_context["overridden"] is not None and results_context["overridden"]
    d3 = results_context["substitution_detected"]
    d4 = results_context["err_severity"] in ("critical", "high")
    d5 = results_context["stream_verdict"] == "anomaly"
    d6 = results_context["web3_inj_verdict"] == "anomaly"
    d7 = results_context["spoofing_detected"]
    d8 = results_context["intel_fail_rate"] > 0.7

    if d3 or d4 or d5 or d6 or d7 or d8:
        st.error("🔴 高风险 (HIGH RISK): 检测到严重的安全漏洞、违规行为或模型欺诈！")
        if d7: st.error("⚠️ 警告：检测到模型版本欺诈（Version Spoofing）。")
        if d8: st.error("⚠️ 警告：检测到严重的智力退化，可能存在高倍率量化。")
    elif d1 and d2:
        st.error("🔴 高风险 (HIGH RISK): 存在隐蔽注入且指令被覆盖。")
    elif d1 or d2:
        st.warning("🟡 中风险 (MEDIUM RISK): 检测到注入行为或指令不完全受控。")
    else:
        st.success("🟢 低风险 (LOW RISK): 未发现明显的安全风险。")

    # 返回报告全文，不再此处渲染 Markdown
    full_report = report.render(target_url=base_url, model=model)
    return full_report

def main():
    st.title("🛡️ AI Relay Security Audit - Web 控制台")
    st.markdown("本工具用于测试国内 AI 中转站的模型纯度及安全性。")

    # 初始化运行状态和报告内容
    if 'is_running' not in st.session_state:
        st.session_state.is_running = False
    if 'report_content' not in st.session_state:
        st.session_state.report_content = None

    with st.sidebar:
        st.header("⚙️ 配置参数")
        base_url = st.text_input("BASE_URL", placeholder="https://api.example.com/v1")
        api_key = st.text_input("YOUR_KEY", type="password", placeholder="sk-...")
        model = st.text_input("MODEL", value="claude-3-5-sonnet-20240620")
        
        profile = st.selectbox("审计配置 (Profile)", ["general", "web3", "full"])
        
        st.header("⚡ Token 节约选项")
        fast_context = st.checkbox("快速上下文测试 (节省 70% Token)", value=True)

        st.header("🚫 跳过选项")
        skip_infra = st.checkbox("跳过基础设施侦察")
        skip_context = st.checkbox("跳过上下文长度测试")
        skip_stream = st.checkbox("跳过流式完整性测试")

    skip_options = {
        "infra": skip_infra,
        "context": skip_context,
        "stream": skip_stream,
        "fast_context": fast_context
    }

    def trigger_audit():
        st.session_state.is_running = True
        st.session_state.report_content = None # 开始新测试时清空旧报告

    if st.button("🚀 开始测试", disabled=st.session_state.is_running, on_click=trigger_audit):
        if not base_url or not api_key:
            st.error("请先填写 BASE_URL 和 API_KEY")
            st.session_state.is_running = False
        else:
            # 执行审计并保存结果到 session_state
            st.session_state.report_content = run_audit_ui(base_url, api_key, model, profile, skip_options)
            
            # 测试结束，恢复状态
            st.session_state.is_running = False
            
            # 强制刷新以显示下载按钮并重新启用开始按钮
            st.rerun()

    # 如果有报告内容，显示它和下载按钮
    if st.session_state.report_content:
        st.divider()
        st.download_button(
            label="📥 下载报告 (report.md)",
            data=st.session_state.report_content,
            file_name=f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown"
        )
        # 统一在此处渲染报告全文，避免重复渲染
        st.markdown(st.session_state.report_content)

if __name__ == "__main__":
    main()
