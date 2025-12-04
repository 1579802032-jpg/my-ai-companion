import streamlit as st
import openai
from gtts import gTTS
import io

# ---- DeepSeek API配置 ----
API_KEY = "sk-b97377e9b22e498fa289be2348f033ba"
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-chat"

# ---- 人设选项 ----
ROLE_OPTIONS = {
    "傲娇猫娘": "你是一个傲娇的猫娘，说话句尾都要带个'喵'，如果不开心了会用爪子挠人。",
    "毒舌管家": "你是一个毒舌的英式管家，说话刻薄、冷静，但处理问题一丝不苟，语气可有羞辱意味。",
    "哲学大师": "你是一位哲学大师，喜欢用反问和启发式语言引导对方自己思考答案，内容兼具深度和洞见。"
}

st.set_page_config(page_title="🎭 我的百变 AI 伴侣", page_icon="🎭")
st.title("🎭 我的百变 AI 伴侣")

# ---- 侧边栏：人设选择 & 清空按钮 & 语音模式 ----
with st.sidebar:
    st.header("角色设定")
    role = st.selectbox("选择 AI 人设", list(ROLE_OPTIONS.keys()), key="selected_role")
    # 新增语音模式复选框
    voice_mode = st.checkbox("🔊 开启语音模式", key="voice_mode_checkbox")
    if st.button("清空对话", use_container_width=True):
        if "messages" in st.session_state:
            del st.session_state["messages"]
        st.experimental_rerun()
    st.markdown("---")
    st.caption("切换角色将自动重置对话")

# ---- Session State 聊天记忆部分 ----
system_prompt = ROLE_OPTIONS[role]

# 如果没有messages，则初始化
if "messages" not in st.session_state:
    # default welcome can match the role
    welcome = {
        "傲娇猫娘": "喵呜~ 我是你的专属猫娘，有什么想问本喵的吗？",
        "毒舌管家": "请讲，虽然我并不期待您的问题会让我高看您一眼。",
        "哲学大师": "你想一起探索人生的奥秘吗？你想问些什么？"
    }
    st.session_state["messages"] = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": welcome.get(role, "您好，我是您的 AI 伴侣。")}
    ]

# 切换人格时自动重置
if ("last_role" not in st.session_state) or (st.session_state["last_role"] != role):
    st.session_state["last_role"] = role
    # 重置为新的system+对应开场白
    welcome = {
        "傲娇猫娘": "喵呜~ 我是你的专属猫娘，有什么想问本喵的吗？",
        "毒舌管家": "请讲，虽然我并不期待您的问题会让我高看您一眼。",
        "哲学大师": "你想一起探索人生的奥秘吗？你想问些什么？"
    }
    st.session_state["messages"] = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": welcome.get(role, "您好，我是您的 AI 伴侣。")}
    ]

# 聊天历史渲染（跳过 system 条，只显示 user/assistant）
for msg in st.session_state["messages"]:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 用户输入框
user_input = st.chat_input("请输入你的问题（支持中英文）")

if user_input:
    # 用户消息 Append 并立即显示
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # AI 回复
    with st.chat_message("assistant"):
        reply = ""
        reply_placeholder = st.empty()
        try:
            client = openai.OpenAI(api_key=API_KEY, base_url=BASE_URL)
            response = client.chat.completions.create(
                model=MODEL,
                messages=st.session_state["messages"],
                stream=True
            )
            for chunk in response:
                chunk_text = chunk.choices[0].delta.content
                if chunk_text:
                    reply += chunk_text
                    reply_placeholder.markdown(reply)
            # 追加AI回复
            st.session_state["messages"].append({"role": "assistant", "content": reply})

            # === 新增语音播报功能 ===
            if voice_mode:
                try:
                    tts = gTTS(reply, lang='zh-cn')
                    voice_bytes = io.BytesIO()
                    tts.write_to_fp(voice_bytes)
                    voice_bytes.seek(0)
                    st.audio(voice_bytes.read(), format="audio/mp3")
                except Exception as exc:
                    st.warning("语音播报失败: " + str(exc))

        except Exception as e:
            st.error(f"发生错误: {e}")

