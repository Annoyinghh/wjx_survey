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
from datetime import datetime

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
                
                # 尝试多种方式初始化 WebDriver
                self.driver = None
                
                # 方案1: 使用 webdriver-manager（推荐）
                try:
                    print("尝试使用 webdriver-manager...")
                    from webdriver_manager.chrome import ChromeDriverManager
                    from selenium.webdriver.chrome.service import Service
                    
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=options)
                    print("✓ 使用 webdriver-manager 成功")
                except ImportError:
                    print("  webdriver-manager 未安装，尝试其他方案...")
                except Exception as e:
                    print(f"  webdriver-manager 失败: {e}")
                
                # 方案2: 使用 Selenium 内置驱动管理器
                if not self.driver:
                    try:
                        print("尝试使用 Selenium 内置驱动管理器...")
                        self.driver = webdriver.Chrome(options=options)
                        print("✓ Selenium 内置驱动管理器成功")
                    except Exception as e:
                        print(f"  Selenium 内置驱动管理器失败: {e}")
                
                # 方案3: 手动指定 ChromeDriver 路径
                if not self.driver:
                    chromedriver_paths = [
                        'chromedriver',
                        'chromedriver.exe',
                        os.path.join(os.path.dirname(__file__), 'chromedriver'),
                        os.path.join(os.path.dirname(__file__), 'chromedriver.exe'),
                        r'C:\chromedriver.exe',
                        '/usr/local/bin/chromedriver',
                    ]
                    
                    for driver_path in chromedriver_paths:
                        try:
                            if os.path.exists(driver_path) or driver_path in ['chromedriver', 'chromedriver.exe']:
                                print(f"尝试使用 ChromeDriver: {driver_path}")
                                service = Service(driver_path)
                                self.driver = webdriver.Chrome(service=service, options=options)
                                print(f"✓ 使用 ChromeDriver {driver_path} 成功")
                                break
                        except Exception as e:
                            continue
                
                # 如果所有方案都失败
                if not self.driver:
                    raise Exception(
                        "无法初始化 ChromeDriver。请尝试以下方案之一:\n"
                        "1. 安装 webdriver-manager: pip install webdriver-manager\n"
                        "2. 下载 ChromeDriver: https://chromedriver.chromium.org/\n"
                        "3. 将 chromedriver 放在项目目录或系统 PATH 中"
                    )
                self.wait = WebDriverWait(self.driver, 20)
                
                # 【关键】在页面加载前注入反检测脚本
                # 必须在访问任何页面之前执行，这样JS才能在页面加载时生效
                stealth_js = '''
                    // 1. 隐藏 webdriver 属性（最关键）
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                        configurable: true
                    });
                    
                    // 2. 删除 webdriver 相关痕迹
                    delete navigator.__proto__.webdriver;
                    
                    // 3. 模拟真实的 plugins
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => {
                            const plugins = [
                                {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
                                {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
                                {name: 'Native Client', filename: 'internal-nacl-plugin', description: ''}
                            ];
                            plugins.length = 3;
                            return plugins;
                        },
                        configurable: true
                    });
                    
                    // 4. 模拟真实的 languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['zh-CN', 'zh', 'en-US', 'en'],
                        configurable: true
                    });
                    
                    // 5. 模拟 chrome 对象
                    window.chrome = {
                        runtime: {
                            connect: function() {},
                            sendMessage: function() {}
                        },
                        loadTimes: function() {
                            return {
                                commitLoadTime: Date.now() / 1000,
                                connectionInfo: "http/1.1",
                                finishDocumentLoadTime: Date.now() / 1000,
                                finishLoadTime: Date.now() / 1000,
                                firstPaintAfterLoadTime: 0,
                                firstPaintTime: Date.now() / 1000,
                                navigationType: "Other",
                                npnNegotiatedProtocol: "unknown",
                                requestTime: Date.now() / 1000,
                                startLoadTime: Date.now() / 1000,
                                wasAlternateProtocolAvailable: false,
                                wasFetchedViaSpdy: false,
                                wasNpnNegotiated: false
                            };
                        },
                        csi: function() {
                            return {
                                onloadT: Date.now(),
                                pageT: Date.now(),
                                startE: Date.now(),
                                tran: 15
                            };
                        }
                    };
                    
                    // 6. 修改 permissions 查询
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                    
                    // 7. 隐藏自动化相关的属性
                    Object.defineProperty(navigator, 'maxTouchPoints', {
                        get: () => 1,
                        configurable: true
                    });
                    
                    // 8. 模拟真实的 platform
                    Object.defineProperty(navigator, 'platform', {
                        get: () => 'Win32',
                        configurable: true
                    });
                    
                    // 9. 隐藏 Headless 特征
                    Object.defineProperty(navigator, 'hardwareConcurrency', {
                        get: () => 8,
                        configurable: true
                    });
                    
                    // 10. 覆盖 toString 方法防止检测
                    const oldCall = Function.prototype.call;
                    function call() {
                        return oldCall.apply(this, arguments);
                    }
                    Function.prototype.call = call;
                    
                    // 11. 防止通过 iframe 检测
                    const iframe = document.createElement('iframe');
                    iframe.style.display = 'none';
                    document.body.appendChild && document.body.appendChild(iframe);
                    
                    console.log('[反检测] 脚本已注入');
                '''
                
                self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    'source': stealth_js
                })
                
                print("✓ 浏览器初始化完成（已注入反检测脚本）")
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
                self._human_delay(1, 2.5)  # 增加延迟，更像人类
            
            # 提交问卷
            self._human_delay(2, 4, "准备提交")
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
                options = [opt.find_element(By.XPATH, '..') for opt in options]
        
        if not options:
            return
        
        # 检查每个选项是否有附加文本框，优先选择没有文本框的选项
        options_with_textbox = []  # 有文本框的选项索引
        options_without_textbox = []  # 没有文本框的选项索引
        
        for i, opt in enumerate(options):
            try:
                # 检查选项是否有关联的文本框
                has_textbox = self._option_has_textbox(opt, element, i)
                if has_textbox:
                    options_with_textbox.append(i)
                else:
                    options_without_textbox.append(i)
            except:
                options_without_textbox.append(i)
        
        # 优先从没有文本框的选项中选择
        if options_without_textbox:
            if q_id in self.weights:
                selected_idx = self._select_by_weight(q_id, len(options))
                if selected_idx in options_with_textbox and options_without_textbox:
                    selected_idx = random.choice(options_without_textbox)
            else:
                selected_idx = random.choice(options_without_textbox)
        else:
            # 所有选项都有文本框，随机选一个
            selected_idx = self._select_by_weight(q_id, len(options)) if q_id in self.weights else random.randint(0, len(options) - 1)
        
        try:
            self._scroll_to_element(options[selected_idx])
            options[selected_idx].click()
            print(f"  选择第 {selected_idx + 1} 项")
        except:
            self.driver.execute_script("arguments[0].click();", options[selected_idx])
        
        # 选择后检查并填写任何出现的文本框
        self._fill_option_textbox(element)
    
    def _fill_multi_choice(self, q_id, element):
        """多选题"""
        options = element.find_elements(By.CSS_SELECTOR, '.ui-checkbox, label.ui-btn')
        if not options:
            options = element.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')
            if options:
                options = [opt.find_element(By.XPATH, '..') for opt in options]
        
        if not options:
            return
        
        # 检查是否有"其他"选项，记录其索引
        other_keywords = ['其他', '其它', '以上都不是']
        other_option_idx = -1
        valid_options = []
        
        for i, opt in enumerate(options):
            try:
                opt_text = opt.text.strip()
                is_other = any(kw in opt_text for kw in other_keywords)
                if is_other:
                    other_option_idx = i
                else:
                    valid_options.append(i)
            except:
                valid_options.append(i)
        
        # 解析题目要求的最少选择数量
        min_select = 2  # 默认最少2项
        try:
            label = element.find_element(By.CSS_SELECTOR, '.field-label, .topichtml')
            label_text = label.text
            # 匹配 "最少选择X项" 或 "至少选择X项"
            match = re.search(r'[最至]少选择(\d+)项', label_text)
            if match:
                min_select = int(match.group(1))
        except:
            pass
        
        # 确保选择数量满足要求，优先从非"其他"选项中选择
        if len(valid_options) >= min_select:
            num_select = min(len(valid_options), random.randint(max(2, min_select), min(5, len(valid_options))))
            selected_indices = random.sample(valid_options, num_select)
        else:
            # 有效选项不够，需要包含"其他"
            num_select = min(len(options), random.randint(max(2, min_select), min(5, len(options))))
            selected_indices = self._select_multiple_by_weight(q_id, len(options), num_select)
        
        # 确保至少选择了要求的数量
        if len(selected_indices) < min_select:
            available = [i for i in range(len(options)) if i not in selected_indices]
            while len(selected_indices) < min_select and available:
                idx = random.choice(available)
                selected_indices.append(idx)
                available.remove(idx)
        
        for idx in selected_indices:
            try:
                self._human_delay(0.2, 0.5)
                options[idx].click()
            except:
                self.driver.execute_script("arguments[0].click();", options[idx])
        
        print(f"  选择了 {len(selected_indices)} 项")
        
        # 选择后检查并填写任何出现的文本框
        self._fill_option_textbox(element)
    
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
    
    def _option_has_textbox(self, option, element, option_idx):
        """检查选项是否有关联的文本框"""
        try:
            # 方法1: 检查选项内部是否有文本框
            inner_textbox = option.find_elements(By.CSS_SELECTOR, 'input[type="text"], textarea')
            if inner_textbox:
                return True
            
            # 方法2: 检查选项文本是否包含需要填写的关键词
            opt_text = option.text.strip()
            textbox_keywords = ['其他', '其它', '请说明', '请填写', '请注明', '具体', '（', '(']
            if any(kw in opt_text for kw in textbox_keywords):
                return True
            
            # 方法3: 检查选项后面是否紧跟文本框（通过相邻元素）
            try:
                # 问卷星的文本框通常在选项的同级或子级
                option_id = option.get_attribute('for') or ''
                if option_id:
                    # 查找关联的文本框
                    related_textbox = element.find_elements(By.CSS_SELECTOR, 
                        f'input[id*="{option_id}"], input[name*="q{option_idx}"]')
                    if related_textbox:
                        return True
            except:
                pass
            
            return False
        except:
            return False
    
    def _fill_option_textbox(self, element):
        """填写选项关联的文本框（选择后调用）"""
        try:
            # 查找所有可见的空文本框
            textboxes = element.find_elements(By.CSS_SELECTOR, 
                'input[type="text"], textarea, input.othertxt, input.otherText')
            
            for tb in textboxes:
                try:
                    if tb.is_displayed():
                        current_value = tb.get_attribute('value') or ''
                        if not current_value.strip():
                            # 生成答案
                            if self.use_ai and self.ai_generator:
                                try:
                                    # 获取题目文本作为上下文
                                    q_text = element.text[:100] if element.text else "补充说明"
                                    answer = self.ai_generator.generate_answer(q_text)
                                    if not answer:
                                        answer = "暂无补充"
                                except:
                                    answer = "暂无补充"
                            else:
                                default_answers = ["暂无补充", "无特殊情况", "正常", "一般情况"]
                                answer = random.choice(default_answers)
                            
                            tb.clear()
                            # 模拟打字
                            for char in answer:
                                tb.send_keys(char)
                                time.sleep(random.uniform(0.02, 0.05))
                            print(f"  填写附加文本框: {answer}")
                except:
                    continue
        except:
            pass
    
    def _fill_other_textbox(self, element):
        """填写"其他"选项的文本框（兼容旧调用）"""
        self._fill_option_textbox(element)
    
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
            # 提交前先检查是否有未填写的必填题
            self._check_and_fill_missing()
            
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
            
            # 尝试最多3次提交
            for attempt in range(3):
                # 点击提交
                try:
                    submit_btn.click()
                except:
                    self.driver.execute_script("arguments[0].click();", submit_btn)
                
                print("✓ 点击提交按钮")
                
                # 等待响应
                self._human_delay(1.5, 2.5)
                
                # 检查是否有错误提示弹窗（必填题未填等）
                if self._handle_error_alert():
                    print(f"  处理错误提示后重试 ({attempt + 1}/3)")
                    self._human_delay(1, 2)
                    continue
                
                # 检查验证码
                captcha_handled = False
                for i in range(3):
                    if self._handle_captcha():
                        print(f"  第{i+1}次验证码处理完成")
                        captcha_handled = True
                        self._human_delay(1, 2)
                    else:
                        break
                
                # 如果处理了验证码，可能需要再次点击提交
                if captcha_handled:
                    try:
                        submit_btn = self.driver.find_element(By.CSS_SELECTOR, '#submit_button, #ctlNext, .submitbtn')
                        if submit_btn and submit_btn.is_displayed():
                            submit_btn.click()
                            self._human_delay(1.5, 2.5)
                    except:
                        pass
                
                # 等待页面跳转
                self._human_delay(2, 3)
                
                # 检查提交结果
                if self._check_submit_result():
                    return True
                
                # 如果失败，检查是否还在问卷页面，可以重试
                try:
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, '#submit_button, #ctlNext, .submitbtn')
                    if not submit_btn.is_displayed():
                        break  # 按钮不可见，可能已经成功或出错
                except:
                    break  # 找不到按钮，退出重试
            
            return False
            
        except Exception as e:
            print(f"提交时出错: {e}")
            return False
    
    def _check_and_fill_missing(self):
        """检查并填写遗漏的必填题"""
        try:
            # 查找带有错误标记的题目（问卷星会给未填的必填题加红色边框或提示）
            error_fields = self.driver.find_elements(By.CSS_SELECTOR, 
                '.field.error, .field.invalid, .field[style*="border-color: red"], div.field:has(.error-tip)')
            
            if not error_fields:
                # 也检查是否有红色星号的必填题未填
                required_fields = self.driver.find_elements(By.CSS_SELECTOR, 'div.field')
                for field in required_fields:
                    try:
                        # 检查是否是必填题（有红色星号）
                        label = field.find_element(By.CSS_SELECTOR, '.field-label, .topichtml')
                        if '*' in label.text[:5]:  # 必填题通常以*开头
                            # 检查是否已填写
                            if not self._is_field_filled(field):
                                error_fields.append(field)
                    except:
                        continue
            
            if error_fields:
                print(f"发现 {len(error_fields)} 个未填写的题目，尝试补填...")
                for field in error_fields:
                    try:
                        q_type = self._detect_question_type(field)
                        q_id = field.get_attribute('id') or ''
                        self._fill_question({
                            'id': q_id,
                            'index': 0,
                            'text': '',
                            'type': q_type,
                            'element': field
                        })
                        self._human_delay(0.5, 1)
                    except:
                        continue
        except Exception as e:
            print(f"检查遗漏题目时出错: {e}")
    
    def _is_field_filled(self, field):
        """检查题目是否已填写"""
        try:
            # 检查单选/多选是否有选中
            selected = field.find_elements(By.CSS_SELECTOR, 
                '.ui-radio-on, .ui-checkbox-on, input:checked, .jqradio.checked, .jqcheck.checked')
            if selected:
                return True
            
            # 检查文本框是否有内容
            inputs = field.find_elements(By.CSS_SELECTOR, 'input[type="text"], textarea')
            for inp in inputs:
                if inp.get_attribute('value'):
                    return True
            
            # 检查下拉框是否选择
            selects = field.find_elements(By.CSS_SELECTOR, 'select')
            for sel in selects:
                if sel.get_attribute('value'):
                    return True
            
            return False
        except:
            return True  # 出错时假设已填写
    
    def _handle_error_alert(self):
        """处理错误提示弹窗（如必填题未填）"""
        try:
            # 问卷星常见的错误提示弹窗
            alert_selectors = [
                '.layui-layer',
                '.layer-content',
                '#layui-layer1',
                '.jqalert',
                '.alert-box',
                '#alert_box',
            ]
            
            for selector in alert_selectors:
                try:
                    alert = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if alert and alert.is_displayed():
                        alert_text = alert.text
                        print(f"  检测到提示: {alert_text[:50]}...")
                        
                        # 检查是否是必填题未填的提示
                        if any(x in alert_text for x in ['必答', '必填', '请填写', '请选择', '至少选择', '请完成']):
                            # 点击确定按钮关闭弹窗
                            close_btns = alert.find_elements(By.CSS_SELECTOR, 
                                'button, .layui-layer-btn0, .layui-layer-close, a.btn')
                            for btn in close_btns:
                                try:
                                    if btn.is_displayed():
                                        btn.click()
                                        self._human_delay(0.3, 0.5)
                                        break
                                except:
                                    continue
                            
                            # 尝试定位并填写未填的题目
                            self._check_and_fill_missing()
                            return True
                except:
                    continue
            
            return False
        except:
            return False
    
    def _handle_captcha(self):
        """处理验证码（包括问卷星智能验证）"""
        try:
            # 1. 检查问卷星智能验证弹窗 - "请完成安全验证" 对话框
            # 弹窗内有 "点击开始智能验证" 按钮
            smart_verify_selectors = [
                # 问卷星智能验证按钮（根据截图）
                'div.wjx-captcha-wrap',
                '.captcha-wrap',
                '#captcha_div',
                'div[class*="captcha"]',
                # 验证弹窗
                '.layui-layer',
                '.sm-pop',
            ]
            
            # 先检查是否有验证弹窗
            for selector in smart_verify_selectors:
                try:
                    captcha_wrap = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if captcha_wrap and captcha_wrap.is_displayed():
                        print(f"检测到验证弹窗: {selector}")
                        
                        # 查找 "点击开始智能验证" 按钮
                        verify_btn_selectors = [
                            '#SM_BTN_1',  # 数美验证按钮
                            '.sm-btn',
                            '.sm-btn-default',
                            '#sm-btn',
                            'button[class*="sm"]',
                            '#rectMask',
                            '.rectMask',
                            'div[id*="SM_"]',
                            # 通用按钮
                            'button',
                            'a.btn',
                        ]
                        
                        for btn_selector in verify_btn_selectors:
                            try:
                                btns = captcha_wrap.find_elements(By.CSS_SELECTOR, btn_selector)
                                for btn in btns:
                                    if btn.is_displayed() and btn.is_enabled():
                                        btn_text = btn.text or btn.get_attribute('value') or ''
                                        if '验证' in btn_text or '开始' in btn_text or not btn_text:
                                            print(f"点击验证按钮: {btn_text or btn_selector}")
                                            
                                            # 使用 ActionChains 模拟真实点击
                                            actions = ActionChains(self.driver)
                                            actions.move_to_element(btn)
                                            actions.pause(random.uniform(0.1, 0.3))
                                            actions.click()
                                            actions.perform()
                                            
                                            # 等待验证完成
                                            time.sleep(4)
                                            
                                            # 检查验证是否成功（弹窗消失）
                                            try:
                                                if not captcha_wrap.is_displayed():
                                                    print("✓ 智能验证完成，弹窗已关闭")
                                                    return True
                                            except:
                                                print("✓ 智能验证完成")
                                                return True
                            except:
                                continue
                        break
                except:
                    continue
            
            # 2. 直接在页面上查找验证按钮（不在弹窗内）
            page_verify_selectors = [
                '#SM_BTN_1',
                '.sm-btn',
                '#rectMask',
                '.rectMask',
                'div[class*="captcha"] button',
                'div[class*="verify"] button',
            ]
            
            for selector in page_verify_selectors:
                try:
                    btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if btn and btn.is_displayed():
                        print(f"找到页面验证按钮: {selector}")
                        
                        actions = ActionChains(self.driver)
                        actions.move_to_element(btn)
                        actions.pause(random.uniform(0.2, 0.5))
                        actions.click()
                        actions.perform()
                        
                        time.sleep(4)
                        print("✓ 点击验证按钮完成")
                        return True
                except:
                    continue
            
            # 3. 检查滑块验证码
            slider_selectors = [
                '.nc_iconfont.btn_slide',
                '#nc_1_n1z',
                '.slider',
                '.slidetounlock',
                '#nc_1__scale_text',
            ]
            
            for selector in slider_selectors:
                try:
                    slider = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if slider and slider.is_displayed():
                        print("检测到滑块验证码，尝试处理...")
                        return self._slide_captcha(slider)
                except:
                    continue
            
            # 4. 检查点选验证码（无法自动处理）
            click_captcha = self.driver.find_elements(By.CSS_SELECTOR, '.geetest_item, .captcha-item')
            if click_captcha:
                print("检测到点选验证码，无法自动处理")
                return False
            
            return False
            
        except Exception as e:
            print(f"验证码处理出错: {e}")
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
        """检查提交结果 - 严格判断"""
        try:
            # 等待页面跳转（增加等待时间）
            time.sleep(4)
            
            current_url = self.driver.current_url
            print(f"提交后URL: {current_url}")
            
            # 保存原始URL用于比较
            original_url_base = current_url.split('?')[0].split('#')[0]
            
            # 问卷星成功提交后的URL特征（严格匹配）
            # 成功: https://www.wjx.cn/wjx/join/completemobile2.aspx?...
            # 失败: 还在原页面 https://v.wjx.cn/vm/xxx.aspx 或 https://www.wjx.cn/vm/xxx.aspx
            
            success_url_patterns = [
                'completemobile2.aspx',  # 问卷星移动端完成页
                'complete.aspx',         # 问卷星PC端完成页
                'completemobile.aspx',   # 另一种完成页
                '/join/complete',        # 完成页路径
                'jqmore.aspx',           # 推荐更多问卷页（也是成功）
            ]
            
            # 检查URL是否包含成功标志
            url_has_success = any(pattern in current_url.lower() for pattern in success_url_patterns)
            
            # 检查URL是否还在问卷填写页面（失败标志）
            still_on_survey = any([
                '/vm/' in current_url,           # 问卷填写页
                '/vj/' in current_url,           # 另一种问卷页
                current_url.endswith('.aspx#'),  # 还在原页面
                current_url.endswith('.aspx'),   # 还在原页面（无hash）
            ]) and not url_has_success
            
            if url_has_success:
                print("✓ 问卷提交成功！(URL已跳转到完成页)")
                return True
            
            if still_on_survey:
                print("✗ 提交失败，URL仍在问卷页面")
                # 尝试诊断失败原因
                self._diagnose_submit_failure()
            
            # 检查页面内容
            try:
                body_text = self.driver.find_element(By.TAG_NAME, 'body').text
                print(f"页面内容前200字: {body_text[:200]}...")
                
                # 成功标志
                success_keywords = ['感谢您的参与', '提交成功', '问卷已提交', '答卷完成', '您已完成本次答卷', '谢谢您的参与']
                
                # 失败标志（更精确，避免误判）
                fail_indicators = {
                    '验证码': '需要验证码',
                    '请完成验证': '需要完成验证',
                    '智能验证': '触发智能验证',
                    '滑动验证': '需要滑动验证',
                    '必答题': '有必答题未填',
                    '请选择': '有选择题未填',
                    '请填写': '有填空题未填',
                    '至少选择': '多选题选择数量不足',
                }
                
                has_success = any(x in body_text for x in success_keywords)
                
                # 检查具体的失败原因
                fail_reason = None
                for keyword, reason in fail_indicators.items():
                    if keyword in body_text:
                        fail_reason = reason
                        break
                
                # 只有明确成功才算成功
                if has_success and not fail_reason:
                    print("✓ 问卷提交成功！(页面内容确认)")
                    return True
                
                if fail_reason:
                    print(f"✗ 提交失败原因: {fail_reason}")
                    return False
                
                # 如果还在问卷页面（有题目内容），也算失败
                if still_on_survey and ('你的' in body_text or '请选择' in body_text or '*' in body_text[:100]):
                    print("✗ 提交失败，页面仍显示问卷内容")
                    return False
                
                # 检查是否还有提交按钮（说明还在问卷页）
                try:
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, '#submit_button, #ctlNext, .submitbtn')
                    if submit_btn and submit_btn.is_displayed():
                        print("✗ 提交失败，提交按钮仍然可见")
                        return False
                except:
                    pass  # 没找到提交按钮，可能已经成功
                    
            except Exception as e:
                print(f"获取页面内容失败: {e}")
            
            # 最终判断：如果URL没变化，肯定失败
            if still_on_survey:
                print("✗ 提交失败，确认仍在问卷页面")
                return False
            
            # 不确定的情况，保守处理为失败
            print("? 提交结果不确定，标记为失败")
            return False
            
        except Exception as e:
            print(f"检查结果出错: {e}")
            return False
    
    def _diagnose_submit_failure(self):
        """诊断提交失败的原因，并保存截图"""
        try:
            print("--- 诊断提交失败原因 ---")
            
            # 0. 保存失败截图
            screenshot_path = self._save_failure_screenshot()
            if screenshot_path:
                print(f"  ★ 失败截图已保存: {screenshot_path}")
            
            # 1. 检查是否有错误提示弹窗
            alert_selectors = ['.layui-layer', '.jqalert', '#alert_box', '.alert-box']
            for selector in alert_selectors:
                try:
                    alert = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if alert and alert.is_displayed():
                        print(f"  发现弹窗: {alert.text[:100]}")
                except:
                    continue
            
            # 2. 检查是否有验证码
            captcha_selectors = ['#rectMask', '.sm-btn', '#nc_1_n1z', '.geetest', '[class*="captcha"]']
            for selector in captcha_selectors:
                try:
                    captcha = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if captcha and captcha.is_displayed():
                        print(f"  发现验证码元素: {selector}")
                except:
                    continue
            
            # 3. 检查未填写的必填题
            try:
                # 查找带红色边框或错误样式的题目
                error_fields = self.driver.find_elements(By.CSS_SELECTOR, 
                    '.field.error, .field[style*="red"], .field:has(.error-tip), .divalidate')
                if error_fields:
                    print(f"  发现 {len(error_fields)} 个可能未填写的题目")
                    for field in error_fields[:3]:  # 只显示前3个
                        try:
                            field_id = field.get_attribute('id')
                            print(f"    - {field_id}")
                        except:
                            pass
            except:
                pass
            
            # 4. 检查页面是否有错误提示文字
            try:
                body_text = self.driver.find_element(By.TAG_NAME, 'body').text
                error_patterns = ['请填写', '请选择', '必答', '至少', '验证', '错误', '失败']
                for pattern in error_patterns:
                    if pattern in body_text:
                        # 找到包含该文字的具体位置
                        idx = body_text.find(pattern)
                        context = body_text[max(0, idx-20):idx+50]
                        print(f"  页面包含 '{pattern}': ...{context}...")
                        break
            except:
                pass
            
            print("--- 诊断结束 ---")
        except Exception as e:
            print(f"诊断出错: {e}")
    
    def _save_failure_screenshot(self):
        """保存失败时的截图"""
        try:
            # 创建截图目录
            screenshot_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'failure_screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)
            
            # 生成文件名（时间戳）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"submit_fail_{timestamp}.png"
            filepath = os.path.join(screenshot_dir, filename)
            
            # 保存截图
            self.driver.save_screenshot(filepath)
            
            # 同时保存页面HTML（方便调试）
            html_path = filepath.replace('.png', '.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            return filepath
        except Exception as e:
            print(f"保存截图失败: {e}")
            return None
    
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
