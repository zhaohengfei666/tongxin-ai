import os
import requests

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


# ============================================================
# 1. 项目路径
# ============================================================

# 当前 shumei.py 所在目录
BASE_DIR = Path(__file__).resolve().parent

# 前端网页路径
INDEX_FILE = BASE_DIR / "index.html"

# 如果以后有图片、CSS、JS等单独文件，可以放在 static 文件夹
STATIC_DIR = BASE_DIR / "static"


# ============================================================
# 2. 创建 FastAPI
# ============================================================

app = FastAPI(
    title="童心AI实验室",
    description="儿童AI成长陪伴平台",
    version="2.0"
)


# ============================================================
# 3. CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 4. 静态资源
# ============================================================

# 如果项目里存在 static 文件夹，就自动挂载
#
# 例如：
#
# static/
# ├── images/
# ├── css/
# └── js/
#
# 网页中可以通过：
# /static/images/xxx.png
#
# 访问

if STATIC_DIR.exists():

    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static"
    )


# ============================================================
# 5. 豆包 API 配置
# ============================================================

# 从服务器环境变量读取 API Key
#
# Linux:
#
# export ARK_API_KEY="你的API KEY"
#
# Windows PowerShell:
#
# $env:ARK_API_KEY="你的API KEY"

ARK_API_KEY = os.getenv("ARK_API_KEY")


# 豆包 Responses API
DOUBAO_URL = (
    "https://ark.cn-beijing.volces.com/"
    "api/v3/responses"
)


# 你现在使用的模型
DOUBAO_MODEL = "doubao-seed-evolving"


# ============================================================
# 6. 首页
# ============================================================

@app.get("/")
def home():

    """
    用户打开服务器网址时，
    直接返回 index.html
    """

    if not INDEX_FILE.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "没有找到 index.html。"
                "请确认 index.html 和 shumei.py "
                "放在同一个文件夹。"
            )
        )

    return FileResponse(
        path=str(INDEX_FILE),
        media_type="text/html"
    )


# ============================================================
# 7. 健康检查接口
# ============================================================

@app.get("/api/health")
def health():

    """
    用来检查后端是否正常运行。
    """

    return {

        "status": "success",

        "message": "童心AI后端运行正常",

        "ai_model": DOUBAO_MODEL,

        "index_exists": INDEX_FILE.exists(),

        "api_key_configured": bool(ARK_API_KEY)

    }


# ============================================================
# 8. 儿童任务
# ============================================================

@app.get("/api/tasks")
def get_tasks():

    return {

        "tasks": [

            {
                "id": 1,
                "name": "和小智聊聊今天",
                "description":
                    "分享今天发生的事情和自己的心情"
            },

            {
                "id": 2,
                "name": "完成一个成长挑战",
                "description":
                    "完成学习、生活习惯或安全主题的小挑战"
            },

            {
                "id": 3,
                "name": "看看家人的留言",
                "description":
                    "查看家长发送的鼓励、提醒和陪伴内容"
            }

        ]

    }


# ============================================================
# 9. AI请求数据格式
# ============================================================

class AIRequest(BaseModel):

    text: str


# ============================================================
# 10. 提取豆包返回文字
# ============================================================

def get_output_text(data):

    """
    从豆包 Responses API 返回结果中
    提取最终文字。
    """

    # 某些接口直接返回 output_text
    if data.get("output_text"):

        return data["output_text"]


    # Responses API 常见结构
    output = data.get("output", [])

    texts = []


    for item in output:

        if item.get("type") == "message":

            content = item.get(
                "content",
                []
            )


            for part in content:

                if part.get("type") == "output_text":

                    text = part.get("text")

                    if text:

                        texts.append(text)


    return "\n".join(texts)


# ============================================================
# 11. 豆包 AI 分析接口
# ============================================================

@app.post("/api/ai/analyze")
def analyze_ai(data: AIRequest):

    """
    前端调用：

    POST /api/ai/analyze

    JSON:

    {
        "text": "需要发送给豆包的内容"
    }
    """


    # --------------------------------------------------------
    # 检查 API Key
    # --------------------------------------------------------

    if not ARK_API_KEY:

        print(
            "错误：ARK_API_KEY 未设置"
        )

        raise HTTPException(

            status_code=500,

            detail=(
                "服务器没有检测到 ARK_API_KEY。"
                "请在服务器环境变量中配置豆包 API Key。"
            )

        )


    # --------------------------------------------------------
    # 用户输入
    # --------------------------------------------------------

    prompt = data.text


    if not prompt.strip():

        raise HTTPException(
            status_code=400,
            detail="输入内容不能为空"
        )


    # --------------------------------------------------------
    # 请求头
    # --------------------------------------------------------

    headers = {

        "Authorization":
            f"Bearer {ARK_API_KEY}",

        "Content-Type":
            "application/json"

    }


    # --------------------------------------------------------
    # 请求体
    # --------------------------------------------------------

    body = {

        "model":
            DOUBAO_MODEL,

        "input":
            prompt

    }


    # --------------------------------------------------------
    # 调试信息
    # --------------------------------------------------------

    print("=" * 60)

    print("准备调用豆包 API")

    print(
        "Model:",
        DOUBAO_MODEL
    )

    print(
        "输入长度:",
        len(prompt)
    )

    print(
        "输入内容:",
        prompt[:200]
    )

    print("=" * 60)


    # --------------------------------------------------------
    # 请求豆包
    # --------------------------------------------------------

    try:

        response = requests.post(

            DOUBAO_URL,

            headers=headers,

            json=body,

            timeout=60

        )


    except requests.exceptions.Timeout:

        print(
            "豆包 API 请求超时"
        )

        raise HTTPException(

            status_code=504,

            detail="豆包AI请求超时，请稍后重试"

        )


    except requests.exceptions.RequestException as e:

        print(
            "连接豆包失败:",
            str(e)
        )

        raise HTTPException(

            status_code=500,

            detail=(
                "连接豆包失败："
                +
                str(e)
            )

        )


    # --------------------------------------------------------
    # 输出豆包状态
    # --------------------------------------------------------

    print(
        "豆包返回状态码:",
        response.status_code
    )


    print(
        "豆包返回内容:",
        response.text[:500]
    )


    # --------------------------------------------------------
    # 非200
    # --------------------------------------------------------

    if response.status_code != 200:

        print(
            "豆包返回错误"
        )

        raise HTTPException(

            status_code=response.status_code,

            detail=(
                "豆包 API 错误："
                +
                response.text
            )

        )


    # --------------------------------------------------------
    # JSON解析
    # --------------------------------------------------------

    try:

        result = response.json()

    except ValueError:

        raise HTTPException(

            status_code=500,

            detail="豆包返回内容不是有效 JSON"

        )


    # --------------------------------------------------------
    # 提取回答
    # --------------------------------------------------------

    answer = get_output_text(
        result
    )


    if not answer:

        print(
            "警告：没有提取到豆包文字"
        )

        return {

            "success":
                False,

            "result":
                (
                    "豆包已经返回数据，"
                    "但暂时没有提取到文字。"
                )

        }


    # --------------------------------------------------------
    # 正常返回
    # --------------------------------------------------------

    print(
        "成功获取豆包回复:",
        answer[:200]
    )


    return {

        "success":
            True,

        "model":
            DOUBAO_MODEL,

        "result":
            answer

    }


# ============================================================
# 12. 404情况下仍返回前端网页（可选）
# ============================================================

@app.get("/{full_path:path}")
def frontend_fallback(full_path: str):

    """
    防止某些前端访问路径出现404。

    /api/ 开头的请求不会走这里，
    因为前面的 API 路由会优先匹配。

    如果未来改成前端路由模式，
    这个功能也能继续使用。
    """

    # 如果是某个真实文件
    possible_file = (
        BASE_DIR
        /
        full_path
    )


    if (
        possible_file.exists()
        and
        possible_file.is_file()
    ):

        return FileResponse(
            str(possible_file)
        )


    # 其他路径返回 index.html
    if INDEX_FILE.exists():

        return FileResponse(

            path=str(INDEX_FILE),

            media_type="text/html"

        )


    raise HTTPException(

        status_code=404,

        detail="页面不存在"

    )


# ============================================================
# 13. 本地直接运行
# ============================================================

if __name__ == "__main__":

    import uvicorn

    port = int(
        os.getenv(
            "PORT",
            "8000"
        )
    )

    uvicorn.run(

        "shumei:app",

        host="0.0.0.0",

        port=port,

        reload=False

    )