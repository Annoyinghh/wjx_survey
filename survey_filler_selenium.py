"""
基于 Selenium 的问卷填写器
支持所有问卷星题型，带反检测措施
Selenium 4.6+ 内置 selenium-manager 自动管理 ChromeDriver
"""
import random
import time
import json
import re
import os

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("请安装依赖: pip install selenium")


class SurveyFillerSelenium:
    """问卷星自动填写器 - 支持所有题型"""
    
    def __init__(self):
        if not SELENIUM_AVAILABLE:
            raise ImportError("undetected-chromedriver 未安装")
        
        self.driver = None
        self.wait = None
        self.use_ai = False
        self.weights = {}
        self.ai_generator = None
        
        # 尝试导入 AI 生成器
        try:
            from ai_answer import AIAnswerGenerator
            self.ai_generator = AIAnswerGenerator()
        except ImportError:
            pass
    
    def _init_browser(self, headless=False, max_retries=3):
        """初始化浏览器"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"第 {attempt + 1} 次尝试初始化浏览器...")
                    time.sleep(2 + attempt * 2)
                
                options = Options()
                
                # 查找 Chrome 路径
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
                    "/usr/bin/google-chrome",
                    "/usr/bin/chromium-browser",
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                ]
                
                chrome_path = None
                for path in chrome_paths:
                    if os.path.exists(path):
                        chrome_path = path
                        break
                
                if chrome_path:
                    options.binary_location = chrome_path
                    if attempt == 0:
                        print(f"使用 Chrome: {chrome_path}")
                
                # 反检测设置
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_experimental_option('excludeSwitches', ['enable-automation'])
                options.add_experimental_option('useAutomationExtension', False)
                
                # 基本设置
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('--lang=zh-CN')
                
                # 云端环境检测
                is_cloud = os.environ.get('RENDER') or os.environ.get('HEROKU') or os.environ.get('RAILWAY')
                
                # 无头模式
                if headless or is_cloud:
                    options.add_argument('--headless=new')
                    options.add_argument('--disable-extensions')
                    options.add_argument('--disable-software-rasterizer')
                    if attempt == 0:
                        print("使用无头模式（后台运行）")
                
                # 随机 User-Agent
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                ]
                options.add_argument(f'--user-agent={random.choice(user_agents)}')
                
                # Selenium 4.6+ 内置 selenium-manager，自动下载匹配的 ChromeDriver
                print("使用 Selenium 内置驱动管理器...")
                
                self.driver = webdriver.Chrome(options=options)
                self.wait = WebDriverWait(self.driver, 20)
                
                # 执行反检测脚本
                self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    'source': '''
                        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                        Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
                        window.chrome = {runtime: {}};
                    '''
                })
                
                print("✓ 浏览器初始化完成")
                return
                
            except Exception as e:
                last_error = e
                error_msg = str(e)
                print(f"浏览器初始化失败 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
                
                try:
                    if self.driver:
                        self.driver.quit()
                        self.driver = None
                except:
                    pass
                
                time.sleep(2)
        
        # 所有重试都失败
        raise Exception(f"浏览器初始化失败，已重试 {max_retries} 次: {last_error}")
    
    def _human_delay(self, min_sec=0.5, max_sec=2.0, action=""):
        """模拟人类延迟"""
        delay = random.uniform(min_sec, max_sec)
        if action:
            print(f"[模拟] {action}，等待 {delay:.1f}s")
        time.sleep(delay)
    
    def _simulate_mouse_movement(self):
        """模拟鼠标随机移动"""
        try:
            actions = ActionChains(self.driver)
            for _ in range(random.randint(2, 5)):
                x = random.randint(-100, 100)
                y = random.randint(-100, 100)
                actions.move_by_offset(x, y)
                actions.pause(random.uniform(0.1, 0.3))
            actions.perform()
        except:
            pass
    
    def _scroll_to_element(self, element):
        """滚动到元素位置"""
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                element
            )
            self._human_delay(0.3, 0.8)
        except:
            pass
    
    def fill_survey(self, url, weights=None):
        """填写问卷主函数"""
        try:
            if weights:
                self.weights = weights
            
            print(f"开始填写问卷: {url}")
            print(f"权重设置: {json.dumps(self.weights, ensure_ascii=False)[:200]}...")
            
            # 初始化浏览器（无头模式，不弹出窗口）
            self._init_browser(headless=True)
            
            # 访问问卷
            self._human_delay(1, 2, "准备访问问卷")
            self.driver.get(url)
            
            # 等待页面加载
            self._human_delay(2, 4, "等待页面加载")
            
            # 模拟鼠标移动
            self._simulate_mouse_movement()
            
            # 解析并填写所有问题
            questions = self._parse_all_questions()
            print(f"找到 {len(questions)} 个问题")
            
            for q in questions:
                self._fill_question(q)
                self._human_delay(0.5, 1.5)
            
            # 提交问卷
            self._human_delay(1, 2, "准备提交")
            result = self._submit()
            
            return result
            
        except Exception as e:
            print(f"填写问卷时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.close()

    def _parse_all_questions(self):
        """解析所有问题"""
        questions = []
        
        try:
            # 等待问题加载
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'field')))
            
            fields = self.driver.find_elements(By.CSS_SELECTOR, 'div.field')
            
            for field in fields:
                try:
                    field_id = field.get_attribute('id') or ''
                    if not field_id or not field_id.startswith('div'):
                        continue
                    
                    # 提取题号
                    match = re.search(r'div(\d+)', field_id)
                    if not match:
                        continue
                    
                    q_index = int(match.group(1))
                    
                    # 获取题目文本
                    try:
                        label = field.find_element(By.CSS_SELECTOR, '.field-label, .topichtml')
                        q_text = label.text.strip()
                    except:
                        q_text = ""
                    
                    # 判断题型
                    q_type = self._detect_question_type(field)
                    
                    questions.append({
                        'id': field_id,
                        'index': q_index,
                        'text': q_text,
                        'type': q_type,
                        'element': field
                    })
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"解析问题出错: {e}")
        
        return questions
    
    def _detect_question_type(self, field):
        """检测问题类型"""
        try:
            # 单选题
            if field.find_elements(By.CSS_SELECTOR, '.ui-radio, .ui-controlgroup[data-role="controlgroup"] input[type="radio"]'):
                return 'single_choice'
            
            # 多选题
            if field.find_elements(By.CSS_SELECTOR, '.ui-checkbox, input[type="checkbox"]'):
                return 'multi_choice'
            
            # 下拉选择题
            if field.find_elements(By.CSS_SELECTOR, 'select, .ui-select'):
                return 'dropdown'
            
            # 矩阵单选题
            if field.find_elements(By.CSS_SELECTOR, '.matrix-table .ui-radio, table.matrix'):
                return 'matrix_single'
            
            # 矩阵多选题
            if field.find_elements(By.CSS_SELECTOR, '.matrix-table .ui-checkbox'):
                return 'matrix_multi'
            
            # 矩阵评分题 / 量表题
            if field.find_elements(By.CSS_SELECTOR, '.scale-rating, .matrix-rating, .rate-off, .star-rating'):
                return 'rating'
            
            # NPS评分题
            if field.find_elements(By.CSS_SELECTOR, '.nps-rating, .nps-item'):
                return 'nps'
            
            # 滑块题
            if field.find_elements(By.CSS_SELECTOR, '.ui-slider, input[type="range"]'):
                return 'slider'
            
            # 排序题
            if field.find_elements(By.CSS_SELECTOR, '.ui-sortable, .sortable-list, .ui-listview'):
                return 'sort'
            
            # 比重题 / 分配题
            if field.get_attribute('total') or field.find_elements(By.CSS_SELECTOR, '.allocation-input, .weight-input'):
                return 'allocation'
            
            # 级联选择题（省市区）
            if field.find_elements(By.CSS_SELECTOR, '.cascader, .region-select, select.province'):
                return 'cascader'
            
            # 日期题
            if field.find_elements(By.CSS_SELECTOR, 'input[type="date"], .datepicker, .ui-datepicker'):
                return 'date'
            
            # 时间题
            if field.find_elements(By.CSS_SELECTOR, 'input[type="time"], .timepicker'):
                return 'time'
            
            # 上传题
            if field.find_elements(By.CSS_SELECTOR, 'input[type="file"], .upload-btn'):
                return 'upload'
            
            # 多项填空题
            if field.find_elements(By.CSS_SELECTOR, '.multi-input, .gap-fill'):
                return 'multi_text'
            
            # 单项填空题 / 简答题
            if field.find_elements(By.CSS_SELECTOR, 'textarea, input[type="text"], .ui-input-text'):
                return 'text'
            
            # 图片选择题
            if field.find_elements(By.CSS_SELECTOR, '.image-choice, .pic-choice'):
                return 'image_choice'
            
            return 'unknown'
            
        except:
            return 'unknown'
    
    def _fill_question(self, question):
        """填写单个问题"""
        q_id = question['id']
        q_type = question['type']
        q_text = question['text'][:50] if question['text'] else ''
        element = question['element']
        
        print(f"填写第{question['index']}题: {q_text}... 类型: {q_type}")
        
        try:
            self._scroll_to_element(element)
            
            if q_type == 'single_choice':
                self._fill_single_choice(q_id, element)
            elif q_type == 'multi_choice':
                self._fill_multi_choice(q_id, element)
            elif q_type == 'dropdown':
                self._fill_dropdown(element)
            elif q_type == 'matrix_single':
                self._fill_matrix_single(element)
            elif q_type == 'matrix_multi':
                self._fill_matrix_multi(element)
            elif q_type == 'rating':
                self._fill_rating(q_id, element)
            elif q_type == 'nps':
                self._fill_nps(element)
            elif q_type == 'slider':
                self._fill_slider(element)
            elif q_type == 'sort':
                self._fill_sort(element)
            elif q_type == 'allocation':
                self._fill_allocation(element)
            elif q_type == 'cascader':
                self._fill_cascader(element)
            elif q_type == 'date':
                self._fill_date(element)
            elif q_type == 'time':
                self._fill_time(element)
            elif q_type == 'text':
                self._fill_text(q_text, element)
            elif q_type == 'multi_text':
                self._fill_multi_text(element)
            elif q_type == 'image_choice':
                self._fill_image_choice(q_id, element)
            else:
                print(f"  未知题型，跳过")
                
        except Exception as e:
            print(f"  填写出错: {e}")

    # ==================== 各题型填写方法 ====================
    
    def _fill_single_choice(self, q_id, element):
        """单选题"""
        options = element.find_elements(By.CSS_SELECTOR, '.ui-radio, label.ui-btn')
        if not options:
            options = element.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
            if options:
                # 点击 label 而不是 input
                options = [opt.find_element(By.XPATH, '..') for opt in options]
        
        if not options:
            return
        
        # 根据权重选择
        selected_idx = self._select_by_weight(q_id, len(options))
        
        try:
            self._scroll_to_element(options[selected_idx])
            options[selected_idx].click()
            print(f"  选择第 {selected_idx + 1} 项")
        except:
            # 使用 JS 点击
            self.driver.execute_script("arguments[0].click();", options[selected_idx])
    
    def _fill_multi_choice(self, q_id, element):
        """多选题"""
        options = element.find_elements(By.CSS_SELECTOR, '.ui-checkbox, label.ui-btn')
        if not options:
            options = element.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
            if options:
                options = [opt.find_element(By.XPATH, '..') for opt in options]
        
        if not options:
            return
        
        # 选择 2-4 个选项
        num_select = min(len(options), random.randint(2, min(4, len(options))))
        
        # 根据权重选择多个
        selected_indices = self._select_multiple_by_weight(q_id, len(options), num_select)
        
        for idx in selected_indices:
            try:
                self._human_delay(0.2, 0.5)
                options[idx].click()
            except:
                self.driver.execute_script("arguments[0].click();", options[idx])
        
        print(f"  选择了 {len(selected_indices)} 项")
    
    def _fill_dropdown(self, element):
        """下拉选择题"""
        try:
            select = element.find_element(By.CSS_SELECTOR, 'select')
            options = select.find_elements(By.TAG_NAME, 'option')
            
            # 跳过第一个（通常是"请选择"）
            valid_options = [opt for opt in options if opt.get_attribute('value')]
            
            if valid_options:
                selected = random.choice(valid_options)
                selected.click()
                print(f"  选择: {selected.text}")
        except:
            pass
    
    def _fill_matrix_single(self, element):
        """矩阵单选题"""
        rows = element.find_elements(By.CSS_SELECTOR, 'tr[id^="drv"], .matrix-row')
        
        for row in rows:
            try:
                radios = row.find_elements(By.CSS_SELECTOR, '.ui-radio, input[type="radio"]')
                if radios:
                    selected = random.choice(radios)
                    try:
                        selected.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", selected)
                    self._human_delay(0.2, 0.4)
            except:
                continue
        
        print(f"  填写了 {len(rows)} 行")
    
    def _fill_matrix_multi(self, element):
        """矩阵多选题"""
        rows = element.find_elements(By.CSS_SELECTOR, 'tr[id^="drv"], .matrix-row')
        
        for row in rows:
            try:
                checkboxes = row.find_elements(By.CSS_SELECTOR, '.ui-checkbox, input[type="checkbox"]')
                if checkboxes:
                    # 每行选 1-2 个
                    num = min(len(checkboxes), random.randint(1, 2))
                    selected = random.sample(checkboxes, num)
                    for cb in selected:
                        try:
                            cb.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", cb)
                        self._human_delay(0.1, 0.3)
            except:
                continue
    
    def _fill_rating(self, q_id, element):
        """评分题 / 量表题"""
        # 查找评分项
        rate_items = element.find_elements(By.CSS_SELECTOR, '.rate-off, .star-item, .scale-item, td.rate')
        
        if not rate_items:
            # 尝试查找矩阵评分的行
            rows = element.find_elements(By.CSS_SELECTOR, 'tr[id^="drv"]')
            for row in rows:
                items = row.find_elements(By.CSS_SELECTOR, '.rate-off, td.rate, .scale-item')
                if items:
                    # 选择较高评分（后半部分）
                    mid = len(items) // 2
                    idx = random.randint(mid, len(items) - 1)
                    try:
                        items[idx].click()
                    except:
                        self.driver.execute_script("arguments[0].click();", items[idx])
                    self._human_delay(0.2, 0.4)
            return
        
        # 单行评分
        if rate_items:
            mid = len(rate_items) // 2
            idx = random.randint(mid, len(rate_items) - 1)
            try:
                rate_items[idx].click()
            except:
                self.driver.execute_script("arguments[0].click();", rate_items[idx])
            print(f"  评分: {idx + 1}/{len(rate_items)}")
    
    def _fill_nps(self, element):
        """NPS评分题（0-10分）"""
        items = element.find_elements(By.CSS_SELECTOR, '.nps-item, .nps-score')
        if items:
            # 选择 7-10 分（推荐者）
            idx = random.randint(7, min(10, len(items) - 1))
            try:
                items[idx].click()
            except:
                self.driver.execute_script("arguments[0].click();", items[idx])
            print(f"  NPS评分: {idx}")
    
    def _fill_slider(self, element):
        """滑块题"""
        try:
            slider = element.find_element(By.CSS_SELECTOR, '.ui-slider-handle, input[type="range"]')
            
            # 获取滑块范围
            min_val = int(slider.get_attribute('min') or 0)
            max_val = int(slider.get_attribute('max') or 100)
            
            # 随机值
            value = random.randint(min_val + (max_val - min_val) // 3, max_val)
            
            # 设置值
            self.driver.execute_script(f"arguments[0].value = {value};", slider)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", slider)
            
            print(f"  滑块值: {value}")
        except Exception as e:
            print(f"  滑块填写失败: {e}")
    
    def _fill_sort(self, element):
        """排序题"""
        try:
            items = element.find_elements(By.CSS_SELECTOR, '.ui-li-static, .sortable-item, li')
            
            if len(items) > 1:
                # 随机打乱顺序（通过拖拽）
                actions = ActionChains(self.driver)
                
                for i in range(min(3, len(items) - 1)):
                    source = random.choice(items)
                    target = random.choice(items)
                    if source != target:
                        actions.drag_and_drop(source, target)
                        actions.pause(0.3)
                
                actions.perform()
                print(f"  排序完成")
        except Exception as e:
            print(f"  排序失败: {e}")
    
    def _fill_allocation(self, element):
        """比重题 / 分配题（总和100）"""
        try:
            inputs = element.find_elements(By.CSS_SELECTOR, 'input[type="text"], input[type="number"]')
            
            if not inputs:
                return
            
            n = len(inputs)
            total = 100
            
            # 分配权重
            values = []
            remaining = total
            
            for i in range(n - 1):
                max_val = remaining - (n - i - 1) * 5
                val = random.randint(5, min(max_val, 40))
                values.append(val)
                remaining -= val
            
            values.append(remaining)
            random.shuffle(values)
            
            # 填入值
            for inp, val in zip(inputs, values):
                inp.clear()
                inp.send_keys(str(val))
                self._human_delay(0.2, 0.4)
            
            print(f"  分配: {values}")
        except Exception as e:
            print(f"  分配题填写失败: {e}")

    def _fill_cascader(self, element):
        """级联选择题（省市区）"""
        try:
            selects = element.find_elements(By.CSS_SELECTOR, 'select')
            
            for select in selects:
                self._human_delay(0.3, 0.6)
                options = select.find_elements(By.TAG_NAME, 'option')
                valid_options = [opt for opt in options if opt.get_attribute('value')]
                
                if valid_options:
                    selected = random.choice(valid_options)
                    selected.click()
            
            print(f"  级联选择完成")
        except Exception as e:
            print(f"  级联选择失败: {e}")
    
    def _fill_date(self, element):
        """日期题"""
        try:
            date_input = element.find_element(By.CSS_SELECTOR, 'input[type="date"], input.datepicker')
            
            # 生成随机日期（最近一年内）
            import datetime
            today = datetime.date.today()
            random_days = random.randint(-365, 0)
            random_date = today + datetime.timedelta(days=random_days)
            date_str = random_date.strftime('%Y-%m-%d')
            
            date_input.clear()
            date_input.send_keys(date_str)
            
            print(f"  日期: {date_str}")
        except Exception as e:
            print(f"  日期填写失败: {e}")
    
    def _fill_time(self, element):
        """时间题"""
        try:
            time_input = element.find_element(By.CSS_SELECTOR, 'input[type="time"], input.timepicker')
            
            # 生成随机时间
            hour = random.randint(8, 22)
            minute = random.choice([0, 15, 30, 45])
            time_str = f'{hour:02d}:{minute:02d}'
            
            time_input.clear()
            time_input.send_keys(time_str)
            
            print(f"  时间: {time_str}")
        except Exception as e:
            print(f"  时间填写失败: {e}")
    
    def _fill_text(self, q_text, element):
        """填空题 / 简答题"""
        try:
            text_input = element.find_element(By.CSS_SELECTOR, 'textarea, input[type="text"]')
            
            # 生成答案
            answer = self._generate_text_answer(q_text)
            
            text_input.clear()
            
            # 模拟打字
            for char in answer:
                text_input.send_keys(char)
                time.sleep(random.uniform(0.03, 0.1))
            
            print(f"  填写: {answer[:30]}...")
        except Exception as e:
            print(f"  填空题填写失败: {e}")
    
    def _fill_multi_text(self, element):
        """多项填空题"""
        try:
            inputs = element.find_elements(By.CSS_SELECTOR, 'input[type="text"], textarea')
            
            default_answers = ["满意", "很好", "正常", "无", "暂无"]
            
            for inp in inputs:
                answer = random.choice(default_answers)
                inp.clear()
                inp.send_keys(answer)
                self._human_delay(0.3, 0.6)
            
            print(f"  填写了 {len(inputs)} 个空")
        except Exception as e:
            print(f"  多项填空失败: {e}")
    
    def _fill_image_choice(self, q_id, element):
        """图片选择题"""
        try:
            images = element.find_elements(By.CSS_SELECTOR, '.image-choice, .pic-item, img')
            
            if images:
                selected_idx = self._select_by_weight(q_id, len(images))
                try:
                    images[selected_idx].click()
                except:
                    self.driver.execute_script("arguments[0].click();", images[selected_idx])
                print(f"  选择图片 {selected_idx + 1}")
        except Exception as e:
            print(f"  图片选择失败: {e}")
    
    # ==================== 辅助方法 ====================
    
    def _select_by_weight(self, q_id, num_options):
        """根据权重选择一个选项"""
        weights = self.weights.get(q_id, {})
        
        if weights:
            valid_indices = []
            valid_weights = []
            
            for i in range(num_options):
                w = weights.get(str(i), 1)
                if w > 0:
                    valid_indices.append(i)
                    valid_weights.append(w)
            
            if valid_indices:
                total = sum(valid_weights)
                r = random.uniform(0, total)
                cumulative = 0
                
                for idx, w in zip(valid_indices, valid_weights):
                    cumulative += w
                    if r <= cumulative:
                        return idx
        
        return random.randint(0, num_options - 1)
    
    def _select_multiple_by_weight(self, q_id, num_options, num_select):
        """根据权重选择多个选项"""
        weights = self.weights.get(q_id, {})
        selected = []
        available = list(range(num_options))
        
        for _ in range(num_select):
            if not available:
                break
            
            if weights:
                w_list = [weights.get(str(i), 1) for i in available]
                total = sum(w_list)
                
                if total > 0:
                    r = random.uniform(0, total)
                    cumulative = 0
                    
                    for i, w in enumerate(w_list):
                        cumulative += w
                        if r <= cumulative:
                            selected.append(available[i])
                            available.pop(i)
                            break
                    continue
            
            idx = random.choice(available)
            selected.append(idx)
            available.remove(idx)
        
        return selected
    
    def _generate_text_answer(self, q_text):
        """生成填空题答案"""
        # 尝试使用 AI
        if self.use_ai and self.ai_generator:
            try:
                answer = self.ai_generator.generate_answer(q_text)
                if answer:
                    return answer
            except:
                pass
        
        # 默认答案
        default_answers = [
            "满意",
            "很好",
            "没有特别的建议",
            "暂无",
            "一切正常",
            "希望继续保持",
        ]
        return random.choice(default_answers)

    # ==================== 提交相关 ====================
    
    def _submit(self):
        """提交问卷"""
        try:
            # 查找提交按钮
            submit_selectors = [
                '#submit_button',
                '#ctlNext',
                '.submitbtn',
                'a.submitbtn',
                'input[type="submit"]',
                'button[type="submit"]',
                '//a[contains(text(), "提交")]',
                '//button[contains(text(), "提交")]',
            ]
            
            submit_btn = None
            for selector in submit_selectors:
                try:
                    if selector.startswith('//'):
                        submit_btn = self.driver.find_element(By.XPATH, selector)
                    else:
                        submit_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if submit_btn and submit_btn.is_displayed():
                        break
                except:
                    continue
            
            if not submit_btn:
                print("未找到提交按钮")
                return False
            
            # 滚动到提交按钮
            self._scroll_to_element(submit_btn)
            self._human_delay(0.5, 1)
            
            # 点击提交
            try:
                submit_btn.click()
            except:
                self.driver.execute_script("arguments[0].click();", submit_btn)
            
            print("✓ 点击提交按钮")
            
            # 等待响应
            self._human_delay(2, 4)
            
            # 检查是否有验证码
            if self._handle_captcha():
                self._human_delay(1, 2)
            
            # 检查提交结果
            return self._check_submit_result()
            
        except Exception as e:
            print(f"提交时出错: {e}")
            return False
    
    def _handle_captcha(self):
        """处理验证码"""
        try:
            # 检查滑块验证码
            slider_selectors = [
                '.nc_iconfont.btn_slide',
                '#nc_1_n1z',
                '.slider',
                '.slidetounlock',
                '[class*="slide"]',
            ]
            
            for selector in slider_selectors:
                try:
                    slider = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if slider and slider.is_displayed():
                        print("检测到滑块验证码，尝试处理...")
                        return self._slide_captcha(slider)
                except:
                    continue
            
            # 检查点选验证码
            click_captcha = self.driver.find_elements(By.CSS_SELECTOR, '.geetest_item, .captcha-item')
            if click_captcha:
                print("检测到点选验证码，无法自动处理")
                return False
            
            return False
            
        except:
            return False
    
    def _slide_captcha(self, slider):
        """处理滑块验证码"""
        try:
            # 获取滑块位置
            location = slider.location
            size = slider.size
            
            # 计算滑动距离
            slide_distance = 280  # 大约滑动距离
            
            # 创建动作链
            actions = ActionChains(self.driver)
            
            # 移动到滑块
            actions.move_to_element(slider)
            actions.pause(random.uniform(0.1, 0.3))
            
            # 按下
            actions.click_and_hold()
            actions.pause(random.uniform(0.1, 0.2))
            
            # 模拟人类滑动轨迹（非匀速）
            moved = 0
            while moved < slide_distance:
                # 变速滑动
                if moved < slide_distance * 0.7:
                    # 前70%快速
                    step = random.randint(15, 30)
                else:
                    # 后30%慢速
                    step = random.randint(3, 8)
                
                step = min(step, slide_distance - moved)
                actions.move_by_offset(step, random.randint(-2, 2))
                actions.pause(random.uniform(0.01, 0.03))
                moved += step
            
            # 释放
            actions.pause(random.uniform(0.1, 0.2))
            actions.release()
            
            # 执行
            actions.perform()
            
            print("✓ 滑块验证完成")
            return True
            
        except Exception as e:
            print(f"滑块验证失败: {e}")
            return False
    
    def _check_submit_result(self):
        """检查提交结果"""
        try:
            # 等待页面跳转
            time.sleep(3)
            
            current_url = self.driver.current_url
            print(f"提交后URL: {current_url}")
            
            # 检查URL是否跳转到完成页面
            url_success = any([
                'complete' in current_url.lower(),
                'finish' in current_url.lower(),
                'success' in current_url.lower(),
                'jqmore' in current_url.lower(),  # 问卷星完成页
            ])
            
            if url_success:
                print("✓ 问卷提交成功！(URL跳转)")
                return True
            
            # 检查页面内容
            try:
                body_text = self.driver.find_element(By.TAG_NAME, 'body').text
                print(f"页面内容前100字: {body_text[:100]}...")
                
                # 成功标志
                success_keywords = ['感谢', '提交成功', '问卷已提交', '答卷完成', '您已完成', '谢谢参与']
                if any(x in body_text for x in success_keywords):
                    print("✓ 问卷提交成功！")
                    return True
                
                # 失败标志
                fail_keywords = ['验证码', '请完成验证', '请点击', '智能验证', '滑动验证', '请先完成']
                if any(x in body_text for x in fail_keywords):
                    print("✗ 提交失败，需要验证码")
                    return False
                
                # 还在原页面（没有跳转）
                if '提交' in body_text and ('问卷' in body_text or '题' in body_text):
                    print("✗ 提交失败，仍在问卷页面")
                    return False
                    
            except Exception as e:
                print(f"获取页面内容失败: {e}")
            
            # 不确定，返回失败（更保守）
            print("? 提交结果不确定，标记为失败")
            return False
            
        except Exception as e:
            print(f"检查结果出错: {e}")
            return False
    
    def close(self):
        """关闭浏览器"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except:
            pass


# 导出类
SurveyFiller = SurveyFillerSelenium
