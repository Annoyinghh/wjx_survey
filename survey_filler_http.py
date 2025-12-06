"""
基于 HTTP 请求的问卷填写器
不依赖 Selenium，适合云端部署
使用 requests 直接模拟表单提交
"""
import requests
from bs4 import BeautifulSoup
import re
import json
import random
import time
import hashlib
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode
import os


class SurveyFillerHTTP:
    def __init__(self):
        self.session = requests.Session()
        
        # 随机选择 User-Agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        ]
        
        self.headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
        self.session.headers.update(self.headers)
        
        self.use_ai = False
        self.weights = {}
        self.ai_generator = None
        
        # 尝试导入 AI 生成器
        try:
            from ai_answer import AIAnswerGenerator
            self.ai_generator = AIAnswerGenerator()
        except ImportError:
            print("AI 答案生成器未安装，将使用默认答案")

    def fill_survey(self, url, weights=None):
        """填写并提交问卷"""
        try:
            print(f"开始填写问卷: {url}")
            if weights:
                self.weights = weights
            print(f"权重设置: {json.dumps(self.weights, ensure_ascii=False, indent=2)}")
            
            # 1. 获取问卷页面
            response = self.session.get(url, timeout=30)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"获取问卷页面失败: HTTP {response.status_code}")
                return False
            
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # 2. 解析问卷结构
            questions = self._parse_questions(soup)
            if not questions:
                print("未找到问题")
                return False
            
            print(f"找到 {len(questions)} 个问题")
            
            # 3. 生成答案
            answers = self._generate_answers(questions)
            print(f"生成了 {len(answers)} 个答案")
            
            # 4. 构建提交数据
            submit_data = self._build_submit_data(soup, html, url, answers)
            
            # 5. 提交问卷
            result = self._submit_survey(url, submit_data)
            
            return result
            
        except Exception as e:
            print(f"填写问卷时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _parse_questions(self, soup):
        """解析问卷中的所有问题"""
        questions = []
        
        question_elements = soup.find_all('div', class_='field')
        
        for element in question_elements:
            try:
                question_id = element.get('id', '')
                if not question_id:
                    continue
                
                # 提取题号
                match = re.search(r'div(\d+)', question_id)
                if not match:
                    continue
                
                question_index = int(match.group(1))
                
                # 获取问题文本
                label_elem = element.find(class_='field-label')
                question_text = label_elem.get_text(strip=True) if label_elem else ""
                
                # 判断问题类型
                question_type = self._get_question_type(element)
                
                # 获取选项
                options = self._get_options(element, question_type)
                
                questions.append({
                    "id": question_id,
                    "index": question_index,
                    "text": question_text,
                    "type": question_type,
                    "options": options
                })
                
            except Exception as e:
                print(f"解析问题时出错: {e}")
                continue
        
        return questions

    def _get_question_type(self, element):
        """判断问题类型"""
        if element.find(class_='ui-radio'):
            return "单选题"
        elif element.find(class_='ui-checkbox'):
            return "多选题"
        elif element.find(class_='ui-input-text') or element.find('textarea'):
            return "填空题"
        elif element.find(class_='ui-listview'):
            return "排序题"
        elif element.find(class_='matrix-rating'):
            if element.get('total'):
                return "比重题"
            return "矩阵评分题"
        elif element.find(class_='scale-rating'):
            return "量表题"
        else:
            return "未知类型"

    def _get_options(self, element, question_type):
        """获取问题选项"""
        options = []
        
        try:
            if question_type == "单选题":
                option_elements = element.find_all(class_='ui-radio')
                for i, opt in enumerate(option_elements):
                    text = opt.get_text(strip=True)
                    options.append({
                        "index": i,
                        "text": text,
                        "value": str(i + 1)
                    })
                    
            elif question_type == "多选题":
                option_elements = element.find_all(class_='ui-checkbox')
                for i, opt in enumerate(option_elements):
                    text = opt.get_text(strip=True)
                    options.append({
                        "index": i,
                        "text": text,
                        "value": str(i + 1)
                    })
                    
            elif question_type == "排序题":
                option_elements = element.find_all(class_='ui-li-static')
                for i, opt in enumerate(option_elements):
                    text = opt.get_text(strip=True)
                    options.append({
                        "index": i,
                        "text": text,
                        "value": str(i + 1)
                    })
                    
            elif question_type in ["矩阵评分题", "量表题"]:
                rate_elements = element.find_all(class_='rate-off')
                options = list(range(1, len(rate_elements) + 1))
                
            elif question_type == "比重题":
                rows = element.find_all('tr', id=lambda x: x and x.startswith('drv'))
                for i, row in enumerate(rows):
                    title_td = row.find('td', class_='title')
                    if title_td:
                        options.append({
                            "index": i,
                            "text": title_td.get_text(strip=True)
                        })
                        
        except Exception as e:
            print(f"获取选项时出错: {e}")
            
        return options

    def _generate_answers(self, questions):
        """为所有问题生成答案"""
        answers = {}
        
        for question in questions:
            try:
                q_id = question['id']
                q_index = question['index']
                q_type = question['type']
                q_text = question['text']
                options = question['options']
                
                print(f"处理第{q_index}题: {q_text[:30]}... 类型: {q_type}")
                
                if q_type == "单选题":
                    answer = self._generate_single_choice_answer(q_id, options)
                elif q_type == "多选题":
                    answer = self._generate_multi_choice_answer(q_id, options)
                elif q_type == "填空题":
                    answer = self._generate_text_answer(q_text)
                elif q_type == "排序题":
                    answer = self._generate_sort_answer(options)
                elif q_type == "比重题":
                    answer = self._generate_weight_answer(q_id, options)
                elif q_type == "矩阵评分题":
                    answer = self._generate_matrix_answer(q_id, options)
                elif q_type == "量表题":
                    answer = self._generate_scale_answer(q_id, options)
                else:
                    answer = ""
                
                answers[q_index] = answer
                print(f"  答案: {answer}")
                
            except Exception as e:
                print(f"生成答案时出错: {e}")
                continue
        
        return answers

    def _generate_single_choice_answer(self, question_id, options):
        """生成单选题答案"""
        if not options:
            return "1"
        
        # 检查是否有权重设置
        option_weights = self.weights.get(question_id, {})
        
        if option_weights:
            # 根据权重选择
            valid_options = []
            valid_weights = []
            
            for i, opt in enumerate(options):
                weight = option_weights.get(str(i), 1)
                if weight > 0:
                    valid_options.append(opt)
                    valid_weights.append(weight)
            
            if valid_options:
                total_weight = sum(valid_weights)
                rand_val = random.uniform(0, total_weight)
                cumulative = 0
                
                for opt, weight in zip(valid_options, valid_weights):
                    cumulative += weight
                    if rand_val <= cumulative:
                        return opt['value']
        
        # 随机选择
        selected = random.choice(options)
        return selected['value']

    def _generate_multi_choice_answer(self, question_id, options):
        """生成多选题答案"""
        if not options:
            return "1"
        
        # 检查是否有权重设置
        option_weights = self.weights.get(question_id, {})
        
        selected_values = []
        max_selections = min(len(options), random.randint(2, 4))
        
        if option_weights:
            # 根据权重选择
            available_options = list(enumerate(options))
            
            for _ in range(max_selections):
                if not available_options:
                    break
                
                weights = [option_weights.get(str(i), 1) for i, _ in available_options]
                total_weight = sum(weights)
                
                if total_weight <= 0:
                    break
                
                rand_val = random.uniform(0, total_weight)
                cumulative = 0
                
                for idx, (i, opt) in enumerate(available_options):
                    cumulative += weights[idx]
                    if rand_val <= cumulative:
                        selected_values.append(opt['value'])
                        available_options.pop(idx)
                        break
        else:
            # 随机选择
            selected_options = random.sample(options, max_selections)
            selected_values = [opt['value'] for opt in selected_options]
        
        # 问卷星多选题格式: 用 | 分隔
        return '|'.join(sorted(selected_values, key=int))

    def _generate_text_answer(self, question_text):
        """生成填空题答案"""
        if self.use_ai and self.ai_generator:
            try:
                return self.ai_generator.generate_answer(question_text)
            except:
                pass
        
        # 默认答案
        default_answers = [
            "无",
            "暂无",
            "没有特别的想法",
            "一切正常",
            "满意",
        ]
        return random.choice(default_answers)

    def _generate_sort_answer(self, options):
        """生成排序题答案"""
        if not options:
            return "1"
        
        # 随机排序
        indices = list(range(1, len(options) + 1))
        random.shuffle(indices)
        return '|'.join(map(str, indices))

    def _generate_weight_answer(self, question_id, options):
        """生成比重题答案"""
        n = len(options)
        if n == 0:
            return ""
        
        total = 100
        
        # 检查是否有权重设置（指定最重要的选项）
        max_index = self.weights.get(question_id, 0)
        
        # 最重要的选项占 55-65%
        max_weight = random.randint(55, 65)
        remaining = total - max_weight
        
        # 分配剩余权重
        weights = [0] * n
        weights[max_index] = max_weight
        
        other_indices = [i for i in range(n) if i != max_index]
        
        if other_indices:
            # 为其他选项分配权重
            for i, idx in enumerate(other_indices[:-1]):
                max_possible = remaining - (len(other_indices) - i - 1) * 5
                w = random.randint(5, min(max_possible, 25))
                weights[idx] = w
                remaining -= w
            
            # 最后一个选项获得剩余权重
            weights[other_indices[-1]] = remaining
        
        return '|'.join(map(str, weights))

    def _generate_matrix_answer(self, question_id, options):
        """生成矩阵评分题答案"""
        if not options:
            return "5"
        
        # 获取权重设置
        weights = self.weights.get(question_id, {"negative": 0.3, "positive": 0.7})
        negative_weight = weights.get("negative", 0.3)
        
        max_score = max(options) if isinstance(options, list) else 5
        mid_point = max_score // 2
        
        if random.random() < negative_weight:
            # 负向评分
            return str(random.randint(1, mid_point))
        else:
            # 正向评分
            return str(random.randint(mid_point + 1, max_score))

    def _generate_scale_answer(self, question_id, options):
        """生成量表题答案"""
        return self._generate_matrix_answer(question_id, options)

    def _build_submit_data(self, soup, html, url, answers):
        """构建提交数据"""
        submit_data = {}
        
        try:
            # 清理 URL
            clean_url = url.split('#')[0]
            parsed_url = urlparse(clean_url)
            
            # 提取隐藏字段
            hidden_inputs = soup.find_all('input', type='hidden')
            for inp in hidden_inputs:
                name = inp.get('name')
                value = inp.get('value', '')
                if name:
                    submit_data[name] = value
            
            # 从 JavaScript 提取关键参数
            js_params = self._extract_js_params(html)
            
            # 构建答案字符串
            # 问卷星格式: 题号$答案;题号$答案;...
            # 用分号分隔，不是用 }
            answer_parts = []
            for q_index, answer in sorted(answers.items()):
                # 确保答案是字符串格式
                answer_str = str(answer) if answer else ''
                # 提取题号（去掉"div"前缀，只保留数字）
                q_num = q_index.replace('div', '') if isinstance(q_index, str) else str(q_index)
                answer_parts.append(f"{q_num}${answer_str}")
            
            submitdata = ';'.join(answer_parts)
            
            print(f"答案格式检查: 第一个答案={answer_parts[0] if answer_parts else 'N/A'}")
            
            # 填写时间（秒）
            ktimes = random.randint(60, 180)
            current_time = int(time.time() * 1000)
            starttime = current_time - ktimes * 1000
            
            # 生成jqsign（如果没有从页面提取到）
            jqsign = js_params.get('jqsign', '')
            if not jqsign:
                # 尝试生成一个有效的jqsign
                jqsign = self._generate_jqsign(submitdata, str(ktimes))
            
            # 问卷星需要的核心参数
            submit_data = {
                'submitdata': submitdata,
                'ktimes': str(ktimes),
                'starttime': str(starttime),
                'source': js_params.get('source', 'directphone'),
                'hlv': js_params.get('hlv', '1'),
                'jqnonce': js_params.get('jqnonce', self._generate_jqnonce()),
                'jqsign': jqsign,
                'rn': js_params.get('rn', ''),
                'timestamp': str(int(time.time() * 1000)),
            }
            
            # 移除空值
            submit_data = {k: v for k, v in submit_data.items() if v}
            
            print(f"提交数据: {json.dumps(submit_data, ensure_ascii=False, indent=2)}")
            print(f"答案数据: {submitdata[:200]}...")
            
        except Exception as e:
            print(f"构建提交数据时出错: {e}")
            import traceback
            traceback.print_exc()
        
        return submit_data

    def _extract_js_params(self, html):
        """从 JavaScript 中提取参数"""
        params = {}
        
        patterns = [
            (r'ktimes\s*[=:]\s*["\']?(\d+)', 'ktimes'),
            (r'starttime\s*[=:]\s*["\']?(\d+)', 'starttime'),
            (r'jqnonce\s*[=:]\s*["\']?([a-zA-Z0-9]+)', 'jqnonce'),
            (r'rn\s*[=:]\s*["\']?([^"\';\s,\)]+)', 'rn'),
            (r'hlv\s*[=:]\s*["\']?(\d+)', 'hlv'),
            (r'jqsign\s*[=:]\s*["\']?([a-zA-Z0-9]+)', 'jqsign'),  # 只匹配字母数字
            (r'source\s*[=:]\s*["\']?([^"\';\s,\)]+)', 'source'),
            (r'"dataList"\s*:\s*(\[[^\]]*\])', 'dataList'),
            (r'activityId\s*[=:]\s*["\']?(\d+)', 'activityId'),
            (r'surveyId\s*[=:]\s*["\']?(\d+)', 'surveyId'),
            (r'qid\s*[=:]\s*["\']?(\d+)', 'qid'),
            (r'id\s*[=:]\s*["\']?(\d+)', 'id'),
        ]
        
        for pattern, key in patterns:
            match = re.search(pattern, html)
            if match:
                params[key] = match.group(1)
                if key != 'dataList':  # dataList太长，不打印
                    print(f"提取到参数 {key}: {params[key][:50] if len(params[key]) > 50 else params[key]}")
        
        return params

    def _generate_jqnonce(self):
        """生成 jqnonce 参数"""
        # 简单的随机字符串
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
        return ''.join(random.choice(chars) for _ in range(16))
    
    def _generate_jqsign(self, submitdata, ktimes):
        """生成 jqsign 参数（问卷星的签名）"""
        try:
            # 问卷星的jqsign可能是多种算法的组合
            # 尝试不同的组合方式
            
            # 方法1: submitdata + ktimes 的 MD5
            sign_str = f"{submitdata}{ktimes}"
            sign_hash = hashlib.md5(sign_str.encode()).hexdigest()
            
            # 方法2: 也可以尝试只用 submitdata
            # sign_hash = hashlib.md5(submitdata.encode()).hexdigest()
            
            # 返回完整的哈希值
            return sign_hash
        except:
            return ''

    def _submit_survey(self, url, submit_data):
        """提交问卷"""
        try:
            # 清理 URL（移除 # 及其后面的内容）
            clean_url = url.split('#')[0]
            
            # 构建提交 URL
            parsed_url = urlparse(clean_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # 从 URL 提取问卷 ID
            # 格式: https://www.wjx.cn/vm/xxxxx.aspx 或 https://v.wjx.cn/vm/xxxxx.aspx
            path = parsed_url.path
            match = re.search(r'/vm/([a-zA-Z0-9]+)\.aspx', path)
            if not match:
                match = re.search(r'/([a-zA-Z0-9]+)\.aspx', path)
            
            if match:
                survey_id = match.group(1)
            else:
                print(f"无法从 URL 提取问卷 ID: {clean_url}")
                return False
            
            # 问卷星提交接口格式: https://www.wjx.cn/joinnew/processjq.ashx
            # 或者: https://v.wjx.cn/joinnew/processjq.ashx
            submit_url = f"{base_url}/joinnew/processjq.ashx"
            
            # 添加问卷 ID 到提交数据
            submit_data['shortid'] = survey_id
            submit_data['curID'] = survey_id  # 问卷ID
            submit_data['t'] = str(int(time.time() * 1000))
            submit_data['submittype'] = '1'  # 提交类型
            
            # 添加其他可能需要的参数
            submit_data['v'] = '1'  # 版本
            submit_data['lang'] = 'zh-CN'  # 语言
            
            print(f"提交 URL: {submit_url}")
            print(f"问卷 ID: {survey_id}")
            print(f"提交数据键: {list(submit_data.keys())}")
            
            # 调试：打印完整的提交数据
            print(f"完整提交数据:")
            for key, value in submit_data.items():
                if len(str(value)) > 100:
                    print(f"  {key}: {str(value)[:100]}...")
                else:
                    print(f"  {key}: {value}")
            
            # 设置提交请求头
            submit_headers = {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': base_url,
                'Referer': clean_url,
                'Accept': 'text/plain, */*; q=0.01',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
            }
            
            # 模拟延迟
            time.sleep(random.uniform(1, 3))
            
            # 发送提交请求
            print(f"正在发送POST请求到: {submit_url}")
            print(f"提交数据大小: {len(urlencode(submit_data))} 字节")
            
            response = self.session.post(
                submit_url,
                data=submit_data,
                headers=submit_headers,
                timeout=30,
                allow_redirects=True,
                verify=False  # 忽略SSL证书验证
            )
            
            print(f"提交响应状态: {response.status_code}")
            print(f"提交响应URL: {response.url}")
            
            # 保存完整响应用于调试
            try:
                import os
                debug_file = os.path.join(os.path.dirname(__file__), 'survey_response_debug.html')
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"✓ 完整响应已保存到 {debug_file}")
            except Exception as e:
                print(f"⚠️  保存响应失败: {e}")
            
            # 提取HTML中的错误信息
            if '<html' in response.text.lower():
                soup = BeautifulSoup(response.text, 'html.parser')
                # 查找错误信息 - 尝试多个选择器
                error_elem = (soup.find(class_='layui-layer-content') or 
                             soup.find(class_='error-message') or 
                             soup.find(id='msg') or
                             soup.find('p') or
                             soup.find('div', class_='content'))
                if error_elem:
                    error_text = error_elem.get_text(strip=True)
                    print(f"提交响应错误信息: {error_text[:200]}")
                else:
                    # 如果找不到特定元素，提取所有文本
                    all_text = soup.get_text(strip=True)
                    print(f"提交响应全文: {all_text[:300]}")
            
            print(f"提交响应内容: {response.text[:500]}")
            
            # 检查响应
            if response.status_code == 200:
                response_text = response.text.strip()
                
                # 根据提供的示例，成功的标志是响应中不包含"22"
                # 问卷星返回格式通常是数字或 JSON
                # 10 = 成功, 1 = 需要验证, 2 = 重复提交等
                
                # 首先检查是否包含错误代码
                if '22' in response_text:
                    print(f"✗ 提交失败: 返回错误代码 22")
                    return False
                elif response_text == '10':
                    print("✓ 问卷提交成功 (返回码: 10)")
                    return True
                elif response_text in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
                    error_codes = {
                        '1': '需要验证码',
                        '2': '重复提交',
                        '3': '问卷已关闭',
                        '4': '参数错误',
                        '5': 'IP限制',
                        '6': '设备限制',
                        '7': '答案不完整',
                        '8': '时间限制',
                        '9': '其他错误',
                    }
                    print(f"✗ 提交失败: {error_codes.get(response_text, '未知错误')} (返回码: {response_text})")
                    return False
                elif '成功' in response_text or 'success' in response_text.lower() or '感谢' in response_text:
                    print("✓ 问卷提交成功")
                    return True
                elif '验证' in response_text or 'verify' in response_text.lower():
                    print("✗ 需要验证，提交失败")
                    return False
                elif '<html' in response_text.lower():
                    # 返回了HTML页面，这通常表示提交失败
                    # 根据示例，成功的提交应该返回数字代码，而不是HTML页面
                    print(f"✗ 提交失败: 返回HTML页面而不是数字代码")
                    return False
                else:
                    # 尝试解析 JSON
                    try:
                        result = json.loads(response_text)
                        if result.get('code') == 10 or result.get('success'):
                            print("✓ 问卷提交成功 (JSON)")
                            return True
                        else:
                            print(f"✗ JSON响应: {result}")
                            return False
                    except:
                        pass
                    
                    # 根据示例，如果响应不是数字代码，就是失败
                    print(f"✗ 提交失败: 无效的响应格式 {response_text[:100]}")
                    return False
            else:
                print(f"✗ 提交失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"提交问卷时出错: {e}")
            import traceback
            traceback.print_exc()
            return False

    def close(self):
        """关闭会话"""
        try:
            self.session.close()
        except:
            pass
