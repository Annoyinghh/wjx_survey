"""
基于 HTTP 请求的问卷解析器
不依赖 Selenium，适合云端部署
"""
import requests
from bs4 import BeautifulSoup
import re
import json
import random
import time


class SurveyParserHTTP:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session.headers.update(self.headers)

    def parse_survey(self, url):
        """解析问卷结构"""
        try:
            # 清理 URL
            clean_url = url.split('#')[0]
            
            # 获取页面内容
            response = self.session.get(clean_url, timeout=30)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"获取问卷页面失败: HTTP {response.status_code}")
                return None
            
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # 尝试从 JavaScript 中提取题目数据（多页问卷）
            questions = self._extract_questions_from_js(html)
            
            # 如果 JS 提取失败，从 HTML 解析
            if not questions:
                questions = self._get_questions(soup)
            
            survey_data = {
                "title": self._get_survey_title(soup),
                "questions": questions,
                "form_data": self._extract_form_data(soup, html),
                "url": url
            }
            
            print(f"解析完成: 标题={survey_data['title']}, 题目数={len(questions)}")
            return survey_data
            
        except Exception as e:
            print(f"解析问卷时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_questions_from_js(self, html):
        """从 JavaScript 中提取题目数据（适用于多页问卷）"""
        questions = []
        
        try:
            # 问卷星会在 JS 中存储题目数据，格式类似 dataList 或 jqData
            # 尝试匹配 var dataList = [...] 或类似结构
            patterns = [
                r'var\s+dataList\s*=\s*(\[[\s\S]*?\]);',
                r'"dataList"\s*:\s*(\[[\s\S]*?\])',
                r'jqData\s*=\s*(\{[\s\S]*?\});',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    try:
                        data = json.loads(match.group(1))
                        if isinstance(data, list) and len(data) > 0:
                            print(f"从 JS 中提取到 {len(data)} 个题目数据")
                            # 这里可以进一步解析 data 结构
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"从 JS 提取题目失败: {e}")
        
        return questions  # 如果提取失败返回空列表，会回退到 HTML 解析

    def _get_survey_title(self, soup):
        """获取问卷标题"""
        try:
            title_elem = soup.find(class_='htitle')
            if title_elem:
                return title_elem.get_text(strip=True)
            
            # 备用方案
            title_elem = soup.find('title')
            if title_elem:
                return title_elem.get_text(strip=True)
            
            return "未命名问卷"
        except:
            return "未命名问卷"

    def _get_questions(self, soup):
        """获取所有问题（包括多页问卷的所有题目）"""
        questions = []
        found_ids = set()
        
        # 方法1: 查找所有 class 包含 field 的 div
        question_elements = list(soup.find_all('div', class_='field'))
        print(f"方法1找到 {len(question_elements)} 个 field 元素")
        
        # 方法2: 查找所有 id 为 div1, div2, div3... 的元素
        for i in range(1, 100):  # 假设最多100题
            elem = soup.find('div', id=f'div{i}')
            if elem:
                if elem not in question_elements:
                    question_elements.append(elem)
                found_ids.add(f'div{i}')
        print(f"方法2找到 {len(found_ids)} 个 div* 元素")
        
        # 方法3: 查找所有 id 以 div 开头且后面是数字的元素
        all_divs = soup.find_all('div', id=lambda x: x and re.match(r'^div\d+$', x))
        for elem in all_divs:
            if elem not in question_elements:
                question_elements.append(elem)
        print(f"方法3总共找到 {len(question_elements)} 个问题元素")
        
        # 去重
        unique_elements = []
        seen_ids = set()
        for elem in question_elements:
            elem_id = elem.get('id')
            if elem_id and elem_id not in seen_ids:
                unique_elements.append(elem)
                seen_ids.add(elem_id)
        
        print(f"去重后 {len(unique_elements)} 个问题元素")
        
        for idx, element in enumerate(unique_elements):
            try:
                question = self._parse_question(element)
                if question:
                    questions.append(question)
                    print(f"✓ 解析第 {idx+1} 题: {question['id']} - {question['type']}")
                else:
                    print(f"✗ 第 {idx+1} 题解析返回 None")
            except Exception as e:
                print(f"✗ 解析第 {idx+1} 题出错: {str(e)}")
                continue
        
        # 按题号排序
        def get_question_number(q):
            match = re.search(r'\d+', q['id'])
            return int(match.group()) if match else 0
        
        questions.sort(key=get_question_number)
        
        print(f"最终解析出 {len(questions)} 个问题")
        return questions

    def _parse_question(self, element):
        """解析单个问题"""
        try:
            # 获取问题ID
            question_id = element.get('id', '')
            if not question_id:
                return None
            
            # 获取问题文本
            label_elem = element.find(class_='field-label')
            question_text = label_elem.get_text(strip=True) if label_elem else ""
            
            # 如果没有找到 field-label，尝试其他方式获取文本
            if not question_text:
                # 尝试获取第一个 h5 或其他标题元素
                title_elem = element.find(['h5', 'h4', 'h3', 'label'])
                if title_elem:
                    question_text = title_elem.get_text(strip=True)
            
            # 判断问题类型
            question_type = self._get_question_type(element)
            
            # 获取选项
            options = self._get_options(element, question_type)
            
            # 检查是否必填
            required = 'required' in element.get('class', []) or element.find(class_='req') is not None
            
            # 即使没有找到选项，也返回问题（填空题可能没有选项）
            result = {
                "id": question_id,
                "text": question_text,
                "type": question_type,
                "options": options,
                "required": required
            }
            
            # 调试输出
            if not question_text:
                print(f"警告: {question_id} 没有找到问题文本")
            
            return result
        except Exception as e:
            print(f"解析问题 {element.get('id', 'unknown')} 失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _get_question_type(self, element):
        """判断问题类型"""
        # 检查各种类型
        if element.find(class_='ui-radio') or element.find('input', {'type': 'radio'}):
            return "单选题"
        elif element.find(class_='ui-checkbox') or element.find('input', {'type': 'checkbox'}):
            return "多选题"
        elif element.find(class_='ui-input-text') or element.find('input', {'type': 'text'}) or element.find('textarea'):
            return "填空题"
        elif element.find(class_='ui-listview'):
            return "排序题"
        elif element.find(class_='matrix-rating') or element.find(class_='matrix'):
            if element.get('total'):
                return "比重题"
            return "矩阵评分题"
        elif element.find(class_='scale-rating') or element.find(class_='scale'):
            return "量表题"
        else:
            # 默认为单选题（最常见的类型）
            return "单选题"

    def _get_options(self, element, question_type):
        """获取问题选项"""
        options = []
        
        try:
            if question_type == "单选题":
                # 尝试多种选择器
                option_elements = element.find_all(class_='ui-radio')
                if not option_elements:
                    option_elements = element.find_all('input', {'type': 'radio'})
                if not option_elements:
                    option_elements = element.find_all('a', class_=lambda x: x and 'radio' in x)
                
                for i, opt in enumerate(option_elements):
                    text = opt.get_text(strip=True)
                    # 如果是 input，获取其父元素的文本
                    if not text and opt.name == 'input':
                        parent = opt.find_parent()
                        text = parent.get_text(strip=True) if parent else ""
                    
                    if text:
                        options.append({
                            "index": i,
                            "text": text,
                            "value": str(i + 1)
                        })
                        
            elif question_type == "多选题":
                option_elements = element.find_all(class_='ui-checkbox')
                if not option_elements:
                    option_elements = element.find_all('input', {'type': 'checkbox'})
                if not option_elements:
                    option_elements = element.find_all('a', class_=lambda x: x and 'checkbox' in x)
                
                for i, opt in enumerate(option_elements):
                    text = opt.get_text(strip=True)
                    if not text and opt.name == 'input':
                        parent = opt.find_parent()
                        text = parent.get_text(strip=True) if parent else ""
                    
                    if text:
                        options.append({
                            "index": i,
                            "text": text,
                            "value": str(i + 1)
                        })
                        
            elif question_type == "填空题":
                options.append({
                    "text": "填空题",
                    "type": "text"
                })
                
            elif question_type == "排序题":
                option_elements = element.find_all(class_='ui-li-static')
                for i, opt in enumerate(option_elements):
                    text = opt.get_text(strip=True)
                    if text:
                        options.append({
                            "index": i,
                            "text": text,
                            "value": str(i + 1)
                        })
                        
            elif question_type in ["矩阵评分题", "量表题"]:
                # 获取评分范围
                rate_elements = element.find_all(class_='rate-off')
                if rate_elements:
                    options.append({
                        "type": "scale",
                        "min": 1,
                        "max": len(rate_elements)
                    })
                    
            elif question_type == "比重题":
                # 获取比重选项
                rows = element.find_all('tr', id=lambda x: x and x.startswith('drv'))
                for i, row in enumerate(rows):
                    title_td = row.find('td', class_='title')
                    if title_td:
                        options.append({
                            "index": i,
                            "text": title_td.get_text(strip=True),
                            "type": "weight"
                        })
                        
        except Exception as e:
            print(f"获取选项时出错: {e}")
            import traceback
            traceback.print_exc()
            
        return options

    def _extract_form_data(self, soup, html):
        """提取表单提交所需的隐藏字段"""
        form_data = {}
        
        try:
            # 查找隐藏字段
            hidden_inputs = soup.find_all('input', type='hidden')
            for inp in hidden_inputs:
                name = inp.get('name')
                value = inp.get('value', '')
                if name:
                    form_data[name] = value
            
            # 从 JavaScript 中提取关键参数
            # 问卷星通常在 JS 中包含 ktimes, starttime 等参数
            patterns = [
                (r'ktimes\s*[=:]\s*["\']?(\d+)', 'ktimes'),
                (r'starttime\s*[=:]\s*["\']?(\d+)', 'starttime'),
                (r'jqnonce\s*[=:]\s*["\']?([^"\']+)', 'jqnonce'),
                (r'rn\s*[=:]\s*["\']?([^"\']+)', 'rn'),
                (r'hlv\s*[=:]\s*["\']?(\d+)', 'hlv'),
            ]
            
            for pattern, key in patterns:
                match = re.search(pattern, html)
                if match:
                    form_data[key] = match.group(1)
            
        except Exception as e:
            print(f"提取表单数据时出错: {e}")
            
        return form_data
