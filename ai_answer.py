import requests
import json
import time

class AIAnswerGenerator:
    def __init__(self):
        self.api_key = "eJaPmxxUzdGaLHNkNewj"
        self.api_secret = "XjyRqPzedRfIkXkKCZZe"
        self.api_url = "https://spark-api-open.xf-yun.com/v1/chat/completions"
        
    def generate_answer(self, question):
        """生成回答"""
        try:
            # 构建请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}:{self.api_secret}"
            }
            
            # 清理问题文本
            question = question.replace("*", "").strip()
            
            # 构建请求数据
            data = {
                "model": "4.0Ultra",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个问卷填写助手。请直接给出简短的答案，不要解释，不要加前缀。例如问'生活费多少'直接回答'1500元'。"
                    },
                    {
                        "role": "user",
                        "content": f"问题：{question}\n请直接给出简短答案（10字以内）："
                    }
                ],
                "temperature": 0.7,
                "top_k": 4,
                "max_tokens": 30
            }
            
            print(f"发送请求: {json.dumps(data, ensure_ascii=False, indent=2)}")
            print(f"请求头: {json.dumps(headers, ensure_ascii=False, indent=2)}")
            
            # 发送请求
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    print("响应中没有找到答案")
                    return "抱歉，我暂时无法生成合适的回答。"
            else:
                print(f"请求失败: {response.status_code} - {response.text}")
                return "抱歉，我暂时无法生成合适的回答。"
                
        except Exception as e:
            print(f"生成回答过程中出错: {str(e)}")
            return "抱歉，生成回答时发生错误。" 